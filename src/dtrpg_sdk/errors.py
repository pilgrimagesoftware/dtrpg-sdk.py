"""Error types for the DriveThruRPG SDK.

This module defines two exception hierarchies:

- `SdkError` -- top-level errors covering SDK lifecycle states such as missing
  configuration or an unauthenticated session.
- `ClientError` -- errors raised by `LibraryClient` and the auth flows,
  covering transport failures, decode failures, and API-reported failures.

Python does not have Rust's `Result<T, E>` as an idiomatic return convention,
so these are raised rather than returned.
"""

from __future__ import annotations


class SdkError(Exception):
    """A top-level error raised by SDK lifecycle operations.

    Most `DriveThruRpgSdk` methods raise a subclass of `SdkError` to signal
    that the failure is a configuration issue or an auth state issue.
    """


class UnconfiguredError(SdkError):
    """Raised when the SDK has not been configured with a `Config` yet.

    Call `DriveThruRpgSdk.configure` or construct the SDK with
    `DriveThruRpgSdk.with_config` before making API calls.
    """

    def __init__(self) -> None:
        """Constructs an `UnconfiguredError` with a fixed, descriptive message."""
        super().__init__("SDK is not configured")


class UnauthenticatedError(SdkError):
    """Raised when the SDK has no active authentication session.

    Obtain a session by calling `DriveThruRpgSdk.apply_auth_response` with a
    successful token response from the API.
    """

    def __init__(self) -> None:
        """Constructs an `UnauthenticatedError` with a fixed, descriptive message."""
        super().__init__("SDK does not have an authenticated session")


class ClientError(Exception):
    """The base class for errors raised by `LibraryClient` and auth flow operations."""


class HttpError(ClientError):
    """An HTTP transport error occurred.

    Wraps the underlying `httpx.HTTPError`, covering connection failures and
    timeout errors.
    """

    def __init__(self, cause: Exception) -> None:
        """Constructs an `HttpError` wrapping the underlying transport exception."""
        super().__init__(f"HTTP error: {cause}")
        self.cause = cause


class InvalidCredentialsError(ClientError):
    """The provided email or password was rejected by DriveThruRPG.

    Raised by `login_with_credentials` when `validate_login_credentials.php`
    indicates the credentials are invalid.
    """

    def __init__(self) -> None:
        """Constructs an `InvalidCredentialsError` with a fixed, descriptive message."""
        super().__init__("invalid credentials")


class ApplicationKeyRequestFailedError(ClientError):
    """Credentials were accepted but the application key request failed.

    Raised by `login_with_credentials` when credentials pass validation but
    `create_account_app.php` returns a non-success status.
    """

    def __init__(self, status: str) -> None:
        """Constructs an `ApplicationKeyRequestFailedError` for the given status."""
        super().__init__(f"application key request failed (status: {status})")
        self.status = status


class DecodeFailedError(ClientError):
    """A response with a successful status could not be decoded into the expected type.

    The raw response body (truncated) is preserved so callers can log the
    offending payload for diagnosis.
    """

    def __init__(self, url: str, status: int, cause: Exception, payload: str) -> None:
        """Constructs a `DecodeFailedError` describing where and why decoding failed."""
        super().__init__(f"response decode failed [{url}] (HTTP {status}): {cause}")
        self.url = url
        self.status = status
        self.cause = cause
        self.payload = payload


class ApiError(ClientError):
    """The API returned a non-success status.

    `message`, when present, is a human-readable explanation extracted from
    the response body (a top-level `message` field, a nested
    `error.message` field, or field-keyed validation errors, e.g.
    `{"productId": "Requires a valid Product ID. Invalid value 22654728."}`).

    The raw response body (truncated) is preserved so callers can log the
    offending payload when no `message` could be extracted.
    """

    def __init__(
        self,
        url: str,
        status: int,
        message: str | None,
        payload: str,
        retry_after: float | None,
    ) -> None:
        """Constructs an `ApiError` describing a non-success API response."""
        detail = message if message is not None else payload
        super().__init__(f"API request failed [{url}] (HTTP {status}): {detail}")
        self.url = url
        self.status = status
        self.message = message
        self.payload = payload
        self.retry_after = retry_after
