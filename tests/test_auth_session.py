"""Unit tests for `AuthSession`, `AuthState`, and `AuthSessionError`."""

from __future__ import annotations

from dtrpg_sdk.auth.session import (
    AuthSession,
    AuthSessionError,
    AuthState,
    AuthTokenResponse,
)


def test_auth_state_formats_as_its_api_wire_string() -> None:
    """`str(AuthState.TOKEN_EXPIRED)` matches the API's wire representation."""
    assert str(AuthState.TOKEN_EXPIRED) == "token_expired"
    assert str(AuthState.UNAUTHENTICATED) == "unauthenticated"
    assert str(AuthState.TOKEN_INVALID) == "token_invalid"
    assert str(AuthState.REFRESH_EXPIRED) == "refresh_expired"
    assert str(AuthState.UNAUTHORIZED) == "unauthorized"


def test_auth_session_error_formats_message_code_and_state() -> None:
    """`str(AuthSessionError)` follows `"{message} ({error_code}) [{auth_state}]"`."""
    error = AuthSessionError(
        error_code="token_expired",
        message="The authentication token has expired.",
        auth_state=AuthState.TOKEN_EXPIRED,
    )

    assert (
        str(error)
        == "The authentication token has expired. (token_expired) [token_expired]"
    )


def test_auth_token_response_from_dict_maps_camel_case_fields() -> None:
    """`AuthTokenResponse.from_dict` maps the API's camelCase field names."""
    response = AuthTokenResponse.from_dict(
        {"token": "jwt", "refreshToken": "refresh", "refreshTokenTTL": 1_771_547_233}
    )

    assert response.token == "jwt"
    assert response.refresh_token == "refresh"
    assert response.refresh_token_ttl == 1_771_547_233


def test_auth_session_from_api_response() -> None:
    """`AuthSession.from_api_response` copies fields from the raw token response."""
    response = AuthTokenResponse(
        token="jwt", refresh_token="refresh", refresh_token_ttl=1_771_547_233
    )

    session = AuthSession.from_api_response(response)

    assert session.token == "jwt"
    assert session.refresh_token == "refresh"
    assert session.refresh_token_ttl == 1_771_547_233


def test_auth_session_invalidate_produces_session_transition_with_no_replacement() -> (
    None
):
    """`AuthSession.invalidate` produces a transition with `next_session=None`."""
    session = AuthSession(
        token="jwt", refresh_token="refresh", refresh_token_ttl=1_771_547_233
    )
    error = AuthSessionError(
        error_code="token_expired",
        message="expired",
        auth_state=AuthState.TOKEN_EXPIRED,
    )

    transition = session.invalidate(error)

    assert transition.next_session is None
    assert transition.error == error
