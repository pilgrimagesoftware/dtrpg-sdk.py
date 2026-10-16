---
title: Error handling
version: latest
slug: errors
---

# Error handling

Python doesn't have Rust's `Result<T, E>` as an idiomatic return
convention, so the SDK raises exceptions rather than returning them. There
are two hierarchies.

## SDK lifecycle errors (`SdkError`)

Raised by `DriveThruRpgSdk` methods for configuration or session-state
issues:

- `UnconfiguredError` -- no `Config` has been set. Call `configure` or
  `with_config` first.
- `UnauthenticatedError` -- no active session. Call `apply_auth_response`
  with a successful token response first.

## Client and auth-flow errors (`ClientError`)

Raised by `LibraryClient` and the auth flow functions:

- `HttpError` -- a transport failure (connection or timeout), wrapping the
  underlying `httpx.HTTPError` as `.cause`.
- `ApiError` -- the API returned a non-success HTTP status. Carries
  `.status`, an extracted human-readable `.message` when available,
  `.payload` (the truncated raw body), and `.retry_after` (seconds, parsed
  from a `Retry-After` header on 429s).
- `DecodeFailedError` -- a success response couldn't be decoded into the
  expected type. Carries `.cause` and `.payload` for diagnosis.
- `InvalidCredentialsError` -- `login_with_credentials` rejected the
  given email/password.
- `ApplicationKeyRequestFailedError` -- credentials passed validation but
  the application key request itself failed. Carries `.status`.

## Example

```python
from dtrpg_sdk import ApiError, HttpError, UnauthenticatedError

try:
    client = sdk.library_client()
    products = client.list_order_products(LibraryItemsParams(page=1))
except UnauthenticatedError:
    # No session -- re-authenticate.
    ...
except ApiError as err:
    print(f"API error {err.status}: {err.message}")
    if err.retry_after is not None:
        # Back off before retrying.
        ...
except HttpError as err:
    print(f"Transport error: {err.cause}")
```
