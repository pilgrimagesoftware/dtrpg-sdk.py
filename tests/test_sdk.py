"""Unit tests for `DriveThruRpgSdk` session lifecycle state transitions."""

from __future__ import annotations

import pytest

from dtrpg_sdk.auth.session import AuthSessionError, AuthState, AuthTokenResponse
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import UnauthenticatedError, UnconfiguredError
from dtrpg_sdk.sdk import DriveThruRpgSdk


def _token_response() -> AuthTokenResponse:
    return AuthTokenResponse(
        token="jwt-token",
        refresh_token="refresh-token",
        refresh_token_ttl=1_771_547_233,
    )


def test_new_sdk_is_unconfigured() -> None:
    """A freshly constructed SDK has no configuration or session."""
    sdk = DriveThruRpgSdk()

    assert sdk.config is None
    assert sdk.session is None


def test_require_config_raises_when_unconfigured() -> None:
    """`require_config` raises `UnconfiguredError` before `configure`/`with_config`."""
    sdk = DriveThruRpgSdk()

    with pytest.raises(UnconfiguredError):
        sdk.require_config()


def test_require_session_raises_when_unauthenticated() -> None:
    """`require_session` raises `UnauthenticatedError` before a session is applied."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))

    with pytest.raises(UnauthenticatedError):
        sdk.require_session()


def test_apply_auth_response_requires_configuration() -> None:
    """Applying an auth response before configuring raises `UnconfiguredError`."""
    sdk = DriveThruRpgSdk()

    with pytest.raises(UnconfiguredError):
        sdk.apply_auth_response(_token_response())


def test_apply_auth_response_stores_session_after_configuration() -> None:
    """A configured SDK stores the session derived from the API token response."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))

    session = sdk.apply_auth_response(_token_response())

    assert session.token == "jwt-token"
    assert session.refresh_token == "refresh-token"
    assert session.refresh_token_expired_at(1_771_547_232) is False
    assert session.refresh_token_expired_at(1_771_547_233) is True


def test_configure_can_be_called_after_construction() -> None:
    """`configure` sets configuration on an SDK created without one."""
    sdk = DriveThruRpgSdk()
    sdk.configure(Config(application_key="app-key"))

    assert sdk.config is not None
    assert sdk.config.application_key == "app-key"


def test_clear_session_removes_session_without_error() -> None:
    """`clear_session` silently removes an active session."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))
    sdk.apply_auth_response(_token_response())

    sdk.clear_session()

    assert sdk.session is None


def test_invalidate_session_clears_and_returns_the_same_error() -> None:
    """`invalidate_session` clears the session and returns the given error as-is."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))
    sdk.apply_auth_response(_token_response())

    error = AuthSessionError(
        error_code="token_expired",
        message="The authentication token has expired.",
        auth_state=AuthState.TOKEN_EXPIRED,
    )

    returned = sdk.invalidate_session(error)

    assert returned == error
    assert sdk.session is None
    with pytest.raises(UnauthenticatedError):
        sdk.require_session()


def test_invalidate_session_without_active_session_raises() -> None:
    """`invalidate_session` raises `UnauthenticatedError` if no session is active."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))
    error = AuthSessionError(
        error_code="unauthenticated",
        message="No session.",
        auth_state=AuthState.UNAUTHENTICATED,
    )

    with pytest.raises(UnauthenticatedError):
        sdk.invalidate_session(error)


def test_library_client_requires_configuration() -> None:
    """`library_client` raises `UnconfiguredError` before configuration."""
    sdk = DriveThruRpgSdk()

    with pytest.raises(UnconfiguredError):
        sdk.library_client()


def test_library_client_requires_session() -> None:
    """`library_client` raises `UnauthenticatedError` before authentication."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))

    with pytest.raises(UnauthenticatedError):
        sdk.library_client()


def test_library_client_created_from_configured_authenticated_sdk() -> None:
    """`library_client` succeeds once both configuration and a session are present."""
    sdk = DriveThruRpgSdk.with_config(Config(application_key="app-key"))
    sdk.apply_auth_response(_token_response())

    client = sdk.library_client()

    assert client.auth_header() == "jwt-token"
