"""Authentication: session types, application-key exchange, and website login.

`AuthSession`, `AuthState`, `AuthSessionError`, `AuthTokenResponse`, and
`SessionTransition` are the session/state types shared across the SDK.
`key_exchange` exchanges an application key for a session token against
`api.drivethrurpg.com`. `credential_login` exchanges an email/password pair
for an application key against `www.drivethrurpg.com`, upstream of
`key_exchange.authenticate`.
"""

from __future__ import annotations

from dtrpg_sdk.auth import credential_login, key_exchange
from dtrpg_sdk.auth.session import (
    AuthSession,
    AuthSessionError,
    AuthState,
    AuthTokenResponse,
    SessionTransition,
)

__all__ = [
    "AuthSession",
    "AuthSessionError",
    "AuthState",
    "AuthTokenResponse",
    "SessionTransition",
    "credential_login",
    "key_exchange",
]
