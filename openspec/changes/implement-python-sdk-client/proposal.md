## Why

`dtrpg-sdk.py` currently exposes nothing beyond a version string — the package scaffolding (CI, release pipeline, governance docs) shipped in v0.1.0, but there is no actual client. The Go, Rust, and Swift SDKs already provide configuration, authentication/session lifecycle, and a library client against the DriveThruRPG API; Python is the one remaining gap among the SDK family's "at parity" languages, and the umbrella `sdk-language-family` spec requires this capability set before Python is considered at parity ([dtrpg-sdk.py#1](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/issues/1)).

## What Changes

- Add `Config`: explicit, programmatic SDK configuration (application key, base URL, API version) with no environment-variable magic, matching the Rust SDK's deliberately minimal configuration model.
- Add the auth/session lifecycle: two independent, composable operations — `login_with_credentials` (email/password → application key, against the website host) and `authenticate` (application key → JWT session, against the API host) — plus an `AuthSession`/`DriveThruRpgSdk`-equivalent session container with explicit `clear_session()` and `invalidate_session()` paths (voluntary logout vs. API-reported failure, kept distinct).
- Add a `LibraryClient` covering every existing library endpoint: list/get order products, prepare a download (index required, no default), list/create/delete product lists, list/add/delete product list items.
- Add the `dtrpg-api` submodule under `API/` so the package has a direct dependency on the same API contract file used by the other SDKs (traceability only — see design.md for why this SDK does not generate client code from it, matching Rust's approach).
- Replicate the Rust SDK's error-handling contract: non-success response bodies are never decoded against the success schema; `Retry-After` (delay-seconds form) is surfaced on rate-limited responses; the bearer token is sent without a `Bearer ` prefix (a documented API quirk, not an oversight).

## Capabilities

### New Capabilities
- `python-sdk-configuration`: Defines how the Python SDK is configured (application key, base URL, API version) before use.
- `python-authentication-flow`: Defines the Python SDK's credential-login and application-key-to-session auth flows, and session lifecycle (apply/clear/invalidate).
- `python-library-client-behavior`: Defines Python SDK library-client behavior for order products, download preparation, and product lists/product list items, including error and rate-limit handling.

### Modified Capabilities
None — `sdk-language-family` is owned by the umbrella `dtrpg` repo, not this one; it cannot be modified via a delta spec here. Once this change ships and merges, a small follow-up update to `dtrpg/openspec/specs/sdk-language-family/spec.md` (marking Python at parity) belongs to the umbrella repo, per `repo-boundaries`.

## Impact

- **Affected code**: `dtrpg-sdk.py` — new `src/dtrpg_sdk/` modules (`config`, `auth/`, `library/`), new `API/` submodule, new test suite.
- **Affected docs**: `dtrpg-sdk.py/README.md` (quick-start example, install instructions once parity is reached). A follow-up in the umbrella `dtrpg` repo updates `sdk-language-family`'s parity status — tracked separately, not part of this change.
- **No breaking changes** to any other repo; this is new capability in a package that previously exposed nothing.
- **Depends on**: `dtrpg-api`'s current `openapi.yaml` contract (already verified usable as a starting point during the umbrella `add-python-node-sdk-family` change).
