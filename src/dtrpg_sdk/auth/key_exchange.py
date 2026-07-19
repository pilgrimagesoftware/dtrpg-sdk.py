"""HTTP client for the DriveThruRPG authentication endpoint.

`authenticate` exchanges a DriveThruRPG application key for a short-lived JWT
access token and a long-lived refresh token. It is the only SDK operation
that does not require a pre-existing `AuthSession`.
"""

from __future__ import annotations

import logging

import httpx

from dtrpg_sdk.auth.session import AuthTokenResponse
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import DecodeFailedError, HttpError

_LOG_PAYLOAD_LIMIT = 2_000
"""Maximum number of bytes logged from a failing auth response body."""

_logger = logging.getLogger(__name__)


def _truncated_payload(raw: str) -> str:
    """Truncates a raw response body to `_LOG_PAYLOAD_LIMIT` characters for logging."""
    if len(raw) > _LOG_PAYLOAD_LIMIT:
        return f"{raw[:_LOG_PAYLOAD_LIMIT]}... (truncated)"
    return raw


def authenticate(api_key: str, config: Config) -> AuthTokenResponse:
    """Exchanges a DriveThruRPG application key for a session token.

    Posts to `POST /{api_version}/auth_key` with `applicationKey` as a query
    parameter. On success, returns the JWT access token, refresh token, and
    refresh token TTL.

    Raises:
        HttpError: On transport or server errors.
        DecodeFailedError: If the response body cannot be parsed.

    Examples:
        >>> config = Config(application_key="my-app-key")
        >>> response = authenticate("my-app-key", config)  # doctest: +SKIP
        >>> response.token  # doctest: +SKIP
    """
    url = f"{config.base_url}/{config.api_version}/auth_key"

    _logger.debug("SDK request: POST %s", url)
    try:
        with httpx.Client() as client:
            response = client.post(url, params={"applicationKey": api_key}, json={})
    except httpx.HTTPError as cause:
        raise HttpError(cause) from cause

    status = response.status_code
    _logger.debug("SDK response: %s -> %s", url, status)

    try:
        return AuthTokenResponse.from_dict(response.json())
    except (ValueError, KeyError) as cause:
        raw = response.text
        payload = _truncated_payload(raw)
        _logger.error(
            "auth_key response decode failed: url=%s status=%s payload=%s error=%s",
            url,
            status,
            payload,
            cause,
        )
        raise DecodeFailedError(
            url=url, status=status, cause=cause, payload=payload
        ) from cause
