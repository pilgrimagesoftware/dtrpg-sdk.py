"""Unit and mock-server tests for `dtrpg_sdk.auth.credential_login`."""

from __future__ import annotations

import httpx
import pytest
import respx

from dtrpg_sdk.auth.credential_login import ValidateLoginResponse, _do_login
from dtrpg_sdk.errors import ApplicationKeyRequestFailedError, InvalidCredentialsError

# ── ValidateLoginResponse unit tests ────────────────────────────────────────


def test_validate_login_response_parses_example_from_login_md() -> None:
    """Parses the exact example array from `dtrpg-api/LOGIN.md`."""
    response = ValidateLoginResponse.from_list(["password", True, "Locked", True])

    assert response.field_name == "password"
    assert response.ok is True
    assert response.message == "Locked"
    assert response.locked is True


def test_validate_login_response_parses_invalid_credentials() -> None:
    """Parses a rejected-credentials array."""
    response = ValidateLoginResponse.from_list(["password", False, "Invalid", False])

    assert response.ok is False
    assert response.locked is False


def test_validate_login_response_rejects_short_array() -> None:
    """A short array (missing fields) raises `ValueError`."""
    with pytest.raises(ValueError):
        ValidateLoginResponse.from_list(["password", True])


# ── Integration-style tests using a local mock HTTP server ─────────────────


@respx.mock
def test_valid_credentials_return_application_key() -> None:
    """Valid credentials produce the application key from `create_account_app.php`."""
    validate_route = respx.post(
        "http://testserver/validate_login_credentials.php"
    ).mock(return_value=httpx.Response(200, json=["password", True, "Locked", True]))
    key_route = respx.post("http://testserver/create_account_app.php").mock(
        return_value=httpx.Response(
            200, json={"status": "success", "message": {"key": "test-app-key-abc123"}}
        )
    )

    result = _do_login("user@example.com", "secret", "http://testserver")

    assert validate_route.called
    assert key_route.called
    assert result == "test-app-key-abc123"


@respx.mock
def test_invalid_credentials_return_error_without_calling_key_endpoint() -> None:
    """Invalid credentials raise `InvalidCredentialsError`, skipping the key call."""
    respx.post("http://testserver/validate_login_credentials.php").mock(
        return_value=httpx.Response(200, json=["password", False, "Invalid", False])
    )
    key_route = respx.post("http://testserver/create_account_app.php").mock(
        return_value=httpx.Response(200)
    )

    with pytest.raises(InvalidCredentialsError):
        _do_login("user@example.com", "secret", "http://testserver")

    assert not key_route.called


@respx.mock
def test_key_request_failure_after_valid_credentials_is_distinguishable() -> None:
    """A non-success `create_account_app.php` status raises the failure error."""
    respx.post("http://testserver/validate_login_credentials.php").mock(
        return_value=httpx.Response(200, json=["password", True, "Locked", True])
    )
    respx.post("http://testserver/create_account_app.php").mock(
        return_value=httpx.Response(
            200, json={"status": "error", "message": {"key": ""}}
        )
    )

    with pytest.raises(ApplicationKeyRequestFailedError) as exc_info:
        _do_login("user@example.com", "secret", "http://testserver")

    assert exc_info.value.status == "error"
