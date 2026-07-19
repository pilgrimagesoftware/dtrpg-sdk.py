"""Website credential exchange for DriveThruRPG.

This module targets `www.drivethrurpg.com` -- **not** `api.drivethrurpg.com`.
It wraps the two website login endpoints that DriveThruRPG's own login page
uses to turn an email/password pair into an application key.

This is distinct from `key_exchange`, which exchanges an application key for
a short-lived JWT against `api.drivethrurpg.com`. `login_with_credentials`
produces the application key that `key_exchange.authenticate` then exchanges
for a session token; the two modules are complementary, not overlapping.
`key_exchange.authenticate` is unaffected by this module.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import (
    ApplicationKeyRequestFailedError,
    DecodeFailedError,
    HttpError,
    InvalidCredentialsError,
)

_WEBSITE_BASE_URL = "https://www.drivethrurpg.com"
"""Base URL for the DriveThruRPG website login endpoints."""

_LOG_PAYLOAD_LIMIT = 2_000
"""Maximum number of bytes preserved in a decode-failure log payload."""

_logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ValidateLoginResponse:
    """Typed response from `POST /validate_login_credentials.php`.

    The endpoint returns a bare JSON array (not an object). Field order per
    `dtrpg-api/LOGIN.md`: `[field_name, ok, message, locked]`.

    Example: `["password", true, "Locked", true]`
    """

    field_name: str
    """The field that was validated (e.g. `"password"`)."""

    ok: bool
    """Whether the credentials are valid."""

    message: str
    """Status message from the server (e.g. `"Locked"`)."""

    locked: bool
    """Whether the account is locked."""

    @staticmethod
    def from_list(data: list) -> ValidateLoginResponse:
        """Decodes a `ValidateLoginResponse` from its 4-element JSON array form."""
        if len(data) < 4:
            raise ValueError(
                "expected a 4-element JSON array "
                f"[field_name, ok, message, locked], got {data!r}"
            )
        field_name, ok, message, locked = data[0], data[1], data[2], data[3]
        return ValidateLoginResponse(
            field_name=field_name, ok=ok, message=message, locked=locked
        )


def _truncated_payload(raw: str) -> str:
    """Truncates a raw response body to `_LOG_PAYLOAD_LIMIT` characters for logging."""
    if len(raw) > _LOG_PAYLOAD_LIMIT:
        return f"{raw[:_LOG_PAYLOAD_LIMIT]}... (truncated)"
    return raw


def login_with_credentials(email: str, password: str, config: Config) -> str:
    """Exchanges an email/password pair for a DriveThruRPG application key.

    Calls `POST /validate_login_credentials.php` on `www.drivethrurpg.com`.
    If credentials are valid, calls `POST /create_account_app.php` and
    returns the application key from `message.key`. Both requests use
    `multipart/form-data` with `email_address` and `password` fields, per
    `dtrpg-api/LOGIN.md`.

    `config` is currently unused: this function always targets
    `www.drivethrurpg.com`, since the website login endpoints live on a
    separate origin from the `api.drivethrurpg.com` endpoint that `Config`
    describes. It is kept in the signature for symmetry with
    `key_exchange.authenticate` and to leave room for a configurable website
    origin later without a breaking API change.

    Raises:
        HttpError: On any transport or server error.
        InvalidCredentialsError: If `validate_login_credentials.php`
            indicates the credentials are invalid.
        ApplicationKeyRequestFailedError: If credentials pass validation but
            `create_account_app.php` returns a non-success status.
        DecodeFailedError: If a response body cannot be parsed.

    Examples:
        >>> config = Config(application_key="placeholder")
        >>> login_with_credentials(
        ...     "user@example.com", "secret", config
        ... )  # doctest: +SKIP
    """
    del config
    return _do_login(email, password, _WEBSITE_BASE_URL)


def _do_login(email: str, password: str, base_url: str) -> str:
    """Performs the two-step website credential exchange against `base_url`."""
    with httpx.Client() as client:
        # Step 1: validate credentials
        validate_url = f"{base_url}/validate_login_credentials.php"
        _logger.debug("SDK request: POST %s", validate_url)

        try:
            validate_resp = client.post(
                validate_url,
                files={
                    "email_address": (None, email),
                    "password": (None, password),
                },
            )
        except httpx.HTTPError as cause:
            raise HttpError(cause) from cause

        validate_status = validate_resp.status_code
        _logger.debug("SDK response: %s -> %s", validate_url, validate_status)

        try:
            validated = ValidateLoginResponse.from_list(validate_resp.json())
        except (ValueError, TypeError) as cause:
            payload = _truncated_payload(validate_resp.text)
            _logger.error(
                "validate_login_credentials response decode failed: "
                "url=%s status=%s payload=%s error=%s",
                validate_url,
                validate_status,
                payload,
                cause,
            )
            raise DecodeFailedError(
                url=validate_url, status=validate_status, cause=cause, payload=payload
            ) from cause

        if not validated.ok:
            _logger.debug("credential validation rejected: url=%s", validate_url)
            raise InvalidCredentialsError()

        # Step 2: request the application key
        key_url = f"{base_url}/create_account_app.php"
        _logger.debug("SDK request: POST %s", key_url)

        try:
            key_resp = client.post(
                key_url,
                files={
                    "email_address": (None, email),
                    "password": (None, password),
                },
            )
        except httpx.HTTPError as cause:
            raise HttpError(cause) from cause

        key_status = key_resp.status_code
        _logger.debug("SDK response: %s -> %s", key_url, key_status)

        try:
            key_result = key_resp.json()
            status = key_result["status"]
            key = key_result["message"]["key"]
        except (ValueError, KeyError, TypeError) as cause:
            payload = _truncated_payload(key_resp.text)
            _logger.error(
                "create_account_app response decode failed: "
                "url=%s status=%s payload=%s error=%s",
                key_url,
                key_status,
                payload,
                cause,
            )
            raise DecodeFailedError(
                url=key_url, status=key_status, cause=cause, payload=payload
            ) from cause

        if status != "success":
            _logger.error(
                "create_account_app returned non-success status: url=%s status=%s",
                key_url,
                status,
            )
            raise ApplicationKeyRequestFailedError(status=status)

        return key
