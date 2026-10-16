---
title: Authentication
version: latest
slug: auth
---

# Authentication

The SDK supports two ways to obtain a session, depending on what
credential you start with.

## Application key -> session token

If you already have a DriveThruRPG application key, exchange it for a
short-lived JWT access token and a long-lived refresh token with
`key_exchange.authenticate`:

```python
from dtrpg_sdk import Config, DriveThruRpgSdk
from dtrpg_sdk.auth import key_exchange

config = Config(application_key="my-app-key")
sdk = DriveThruRpgSdk.with_config(config)

token_response = key_exchange.authenticate("my-app-key", config)
session = sdk.apply_auth_response(token_response)
print(session.token)
```

`authenticate` posts to `POST /{api_version}/auth_key` and is the only SDK
operation that does not require a pre-existing session.

## Email/password -> application key

If you only have an email and password, use `login_with_credentials` to
obtain an application key first, then feed it into `key_exchange.authenticate`
as above. This targets `www.drivethrurpg.com`'s website login endpoints, a
separate origin from the `api.drivethrurpg.com` endpoint `Config` describes:

```python
from dtrpg_sdk import Config
from dtrpg_sdk.auth.credential_login import login_with_credentials

config = Config(application_key="placeholder")
app_key = login_with_credentials("user@example.com", "secret", config)
```

Raises `InvalidCredentialsError` if the credentials are rejected, or
`ApplicationKeyRequestFailedError` if credentials pass validation but the
key request itself fails.

## Session lifecycle

`DriveThruRpgSdk` holds at most one active session:

- `apply_auth_response(response)` stores a new session from a raw token
  response. Raises `UnconfiguredError` if the SDK has no `Config` yet.
- `require_session()` returns the active session, or raises
  `UnauthenticatedError` if there is none.
- `clear_session()` removes the session for voluntary log-out.
- `invalidate_session(error)` removes the session after the API reports a
  session failure, and returns the given error so callers can propagate it.

```python
try:
    client = sdk.library_client()
except UnauthenticatedError:
    # No session yet -- authenticate first.
    ...
```

## Refreshing a session

An access token is short-lived. To renew it without repeating the application-key
exchange, call `sdk.refresh_session()`. It sends the session's refresh token to the API and
replaces the stored session with the response, including the new refresh token and expiry.

```python
try:
    sdk.refresh_session()
except DecodeFailedError:
    # The refresh token was rejected; fall back to key_exchange.authenticate with
    # the application key. The existing session is left in place.
    ...

# Clients created before the refresh still hold the old token.
client = sdk.library_client()
```

`auth.token_refresh.refresh(refresh_token, config)` makes the same call without an SDK
instance.
