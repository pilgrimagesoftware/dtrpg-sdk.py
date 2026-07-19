"""Authentication session types for the DriveThruRPG SDK.

This module provides the core types for representing and managing the
authentication lifecycle with the DriveThruRPG API:

- `AuthTokenResponse` -- the raw token payload received from the API after a
  successful login.
- `AuthState` -- an enumeration of authentication failure states reported by
  the API.
- `AuthSessionError` -- a structured authentication error returned by the API.
- `AuthSession` -- an active, validated session derived from an
  `AuthTokenResponse`.
- `SessionTransition` -- the result of invalidating a session, carrying the
  error that caused the transition and an optional replacement session.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AuthState(str, Enum):
    """The authentication failure state reported by the DriveThruRPG API.

    Each member's value is the corresponding API wire string, matching the
    Rust SDK's `AuthState::as_api_str`.
    """

    UNAUTHENTICATED = "unauthenticated"
    """No authentication credentials are present."""

    TOKEN_INVALID = "token_invalid"
    """The provided access token is structurally invalid or unrecognized."""

    TOKEN_EXPIRED = "token_expired"
    """The access token has passed its expiry time and must be refreshed."""

    REFRESH_EXPIRED = "refresh_expired"
    """The refresh token has passed its expiry time; the user must re-authenticate."""

    UNAUTHORIZED = "unauthorized"
    """The credentials are valid but the caller lacks permission for the resource."""

    def __str__(self) -> str:
        """Returns the API wire string for this state."""
        return self.value


@dataclass(frozen=True)
class AuthSessionError(Exception):
    """A structured authentication error returned by the DriveThruRPG API.

    Carries the machine-readable `error_code`, a human-readable `message`,
    and an `AuthState` that classifies the failure. Used when the API
    explicitly rejects an operation due to an auth-related condition.
    """

    error_code: str
    message: str
    auth_state: AuthState

    def __str__(self) -> str:
        """Formats the error as `"{message} ({error_code}) [{auth_state}]"`."""
        return f"{self.message} ({self.error_code}) [{self.auth_state}]"


@dataclass(frozen=True)
class AuthTokenResponse:
    """The raw authentication token payload returned by the DriveThruRPG API.

    A direct representation of the API response fields. Callers should
    convert it into an `AuthSession` via `AuthSession.from_api_response`
    before treating the session as active.
    """

    token: str
    """The short-lived JWT access token used to authenticate API requests."""

    refresh_token: str
    """The long-lived refresh token used to obtain a new access token."""

    refresh_token_ttl: int
    """Unix timestamp (seconds) at which the refresh token expires."""

    @staticmethod
    def from_dict(data: dict) -> AuthTokenResponse:
        """Decodes an `AuthTokenResponse` from the API's camelCase JSON payload."""
        return AuthTokenResponse(
            token=data["token"],
            refresh_token=data["refreshToken"],
            refresh_token_ttl=data["refreshTokenTTL"],
        )


@dataclass(frozen=True)
class AuthSession:
    """An active authentication session with the DriveThruRPG API.

    The validated, runtime representation of an authenticated user. Obtained
    by calling `DriveThruRpgSdk.apply_auth_response` with a token response
    from the API.
    """

    token: str
    """The short-lived JWT access token for this session."""

    refresh_token: str
    """The long-lived refresh token for this session."""

    refresh_token_ttl: int
    """The Unix timestamp (seconds) at which the refresh token expires."""

    @staticmethod
    def from_api_response(response: AuthTokenResponse) -> AuthSession:
        """Creates an `AuthSession` from a raw `AuthTokenResponse`."""
        return AuthSession(
            token=response.token,
            refresh_token=response.refresh_token,
            refresh_token_ttl=response.refresh_token_ttl,
        )

    def refresh_token_expired_at(self, unix_timestamp: int) -> bool:
        """Returns `True` if `unix_timestamp` is at or past the refresh token's expiry.

        The refresh token expires at `self.refresh_token_ttl`.
        """
        return unix_timestamp >= self.refresh_token_ttl

    def invalidate(self, error: AuthSessionError) -> SessionTransition:
        """Produces a `SessionTransition` representing this session's invalidation.

        The resulting transition has no replacement session (`next_session`
        is `None`) and carries the provided `error` describing why the
        session was invalidated.

        This is a lower-level primitive for code working with an
        `AuthSession` directly. `DriveThruRpgSdk.invalidate_session` is the
        higher-level equivalent for callers going through the SDK: it does
        not build a `SessionTransition`, and unconditionally clears the
        stored session rather than leaving room for a `next_session`
        replacement.
        """
        return SessionTransition(next_session=None, error=error)


@dataclass(frozen=True)
class SessionTransition:
    """The outcome of invalidating an `AuthSession`.

    Returned when a session ends due to an error. Records the error that
    caused the invalidation and an optional replacement session (for cases
    where token refresh succeeds mid-invalidation).
    """

    next_session: AuthSession | None
    """The replacement session, if one was established as part of this transition."""

    error: AuthSessionError
    """The error that caused this session transition."""
