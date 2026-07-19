## Context

`dtrpg-sdk.rs` (v1.1.0) is the reference implementation for this API surface. This design ports its architecture to Python, preserving its deliberate design decisions (see Decisions below) rather than re-deriving the API shape from scratch. Rust's module layout — `config.rs`, `sdk.rs`, `error.rs`, `auth/` (two independent flows), `library/` (client + models) — maps directly onto a Python package layout.

Rust's `LibraryClient` is hand-written against the OpenAPI contract, not generated from it; `build.rs` only extracts the server URL and a path/method inventory for a single traceability test, with zero runtime effect on request behavior. Python follows the same approach: hand-written client, `API/openapi.yaml` present as a submodule for traceability, no code generation pipeline.

## Goals / Non-Goals

**Goals:**
- Match the Rust SDK's public API shape (types, method names translated to Python idiom, method signatures, error semantics) closely enough that a developer familiar with one SDK can predict the other's behavior.
- Preserve every deliberate Rust design decision listed below unless there's a Python-specific reason to diverge (and if so, document it here, not silently).
- Ship with the same test rigor: unit tests for pure logic (session state transitions), integration-style tests against a local mock HTTP server for every client method.

**Non-Goals:**
- Async support in this initial implementation. Rust uses `tokio` throughout; Python's async story (`asyncio` + `httpx`) is a reasonable follow-up but doubles the API surface (sync + async client) for a first implementation. This SDK ships a synchronous client using `httpx.Client`. Revisit once the app integration (`dtrpg-app`) states an async requirement.
- Token auto-refresh. Rust doesn't implement it either — `refresh_token`/`refresh_token_ttl` are stored and exposed, not acted upon automatically.
- Environment-variable configuration. Matches Rust's explicit-config-only stance (`rust-sdk-configuration` spec: "configuration must be explicit before use").
- Code generation from `openapi.yaml`. The submodule is present for contract traceability, matching Rust; a generated client is out of scope here as it was for Rust.

## Decisions

**Decision: Package layout mirrors Rust's module boundaries.**
```
src/dtrpg_sdk/
    __init__.py       # public re-exports
    config.py          # Config
    sdk.py              # DriveThruRpgSdk-equivalent (session lifecycle orchestration)
    errors.py            # SdkError, AuthSessionError
    auth/
        __init__.py
        session.py         # AuthTokenResponse, AuthState, AuthSession, SessionTransition
        key_exchange.py      # authenticate()
        credential_login.py    # login_with_credentials()
    library/
        __init__.py
        client.py             # LibraryClient, ClientError
        models.py               # request/response/model dataclasses
```
Alternative considered: a flat `dtrpg_sdk/__init__.py` with everything inlined. Rejected — Rust's separation (session orchestration knows nothing about HTTP; `LibraryClient` knows nothing about session state, just holds a token) is a load-bearing design decision (see Rust design decision #1), not incidental structure, and collapsing it would make the eventual async variant or a token-refresh feature harder to add cleanly.

**Decision: `LibraryClient` takes `Config` + a bare token string, not a reference to the SDK object.**
Matches Rust exactly. This is what makes `LibraryClient` independently testable and constructible without going through the full session-lifecycle dance. `sdk.library_client()` is the only sanctioned way to build one in normal use, but nothing prevents direct construction for tests.

**Decision: dataclasses (not Pydantic) for models, `dataclasses.asdict`/manual `from_dict` for (de)serialization.**
Alternative considered: Pydantic v2 for automatic validation and JSON:API envelope handling. Rejected for this initial implementation — Rust's models are plain structs with `serde` doing purely mechanical field mapping (including `rename` for camelCase wire fields), no validation logic beyond type-correctness. Pydantic would add a real dependency and a different error-handling story (Pydantic's `ValidationError` vs. this SDK's `ClientError.DecodeFailed`) for no behavior Rust's approach doesn't already provide. Field renames (e.g. `refreshToken` → `refresh_token`) are handled by a small shared `from_camel_case_dict` helper in `library/models.py`, not per-field metadata. Revisit if the model surface grows enough that hand-written `from_dict`/`to_dict` becomes a maintenance burden — that's a legitimate reason to add Pydantic later, but not a reason to start with it.

**Decision: `httpx.Client` (sync), not `requests`.**
`requests` has no built-in typed exception hierarchy distinguishing transport errors from HTTP-status errors as cleanly as `httpx` (`httpx.HTTPError` subclasses `TransportError`/`HTTPStatusError` distinctly), and `httpx` is the modern, actively maintained choice with a sync/async-symmetric API (relevant if async is added later per the Non-Goals note). `Retry-After` header access works identically either way (`response.headers.get("Retry-After")`).

**Decision: Two-tier session invalidation (`clear_session` vs `invalidate_session`) ported as-is.**
`clear_session()` — silent logout. `invalidate_session(error: AuthSessionError) -> AuthSessionError` — raises `SdkError` variant if no session exists, otherwise clears and returns the same error it was given (does not classify it). No Python-specific reason to collapse this to one method; preserves parity with Rust's documented three-way distinction (silent clear / structured invalidate / reserved `AuthSession.invalidate` transition primitive for future token-refresh-in-place).

**Decision: `prepare_download(order_product_id, index)` — `index` is a required positional/keyword argument, no default.**
Directly ports Rust's documented decision (`dtrpg-sdk.rs`'s `2026-07-10-prepare-download-file-index` design doc): a default of `0` is unsafe for multi-file bundles and was explicitly rejected there. Same reasoning applies here — do not add `index: int = 0`.

**Decision: Errors as an exception hierarchy, not a Result-like return type.**
Python doesn't have Rust's `Result<T, E>` as an idiomatic return convention — raising is the idiom. `SdkError` and `ClientError` become exception classes (`class SdkError(Exception)`, subclasses `UnconfiguredError`, `UnauthenticatedError`; `class ClientError(Exception)`, subclasses `HttpError`, `InvalidCredentialsError`, `ApplicationKeyRequestFailedError`, `DecodeFailedError`, `ApiError` with a `retry_after: float | None` attribute). This is the one structural divergence from Rust's enum-based errors, driven by target-language idiom rather than a judgment call — every other decision in this doc is a deliberate choice, this one is just "how Python does this."

**Decision: Bearer token sent without a `Bearer ` prefix.**
Ported verbatim from Rust — documented API-specific quirk (`Authorization: <raw JWT>`), not a bug to "fix" in the port.

**Decision: `Retry-After` — delay-seconds form only, matching Rust's explicit scope decision.**
No date-parsing dependency added for a form the API is judged unlikely to send on 429s. If this proves wrong in practice, broaden explicitly (update this doc), don't silently patch around it.

**Decision: JSON:API envelope handling stays per-endpoint, not a generic `Envelope[T]`.**
Matches Rust's documented experience (`create_product_list` needed its own envelope after a live-payload failure that a generic wrapper would have masked). Each response type that needs envelope-unwrapping gets its own `from_dict` handling that decision explicitly, verified against the same fixtures/mocks Rust uses where available.

## Risks / Trade-offs

- [Risk] Hand-written models mean a `dtrpg-api` contract change requires a manual Python-side update, with no compiler/type-checker catching a missed field the way Rust's `serde` (with `deny_unknown_fields` semantics or missing-field errors) would at deserialization time. → Mitigation: `pyrefly`/`ty` type checking on `from_dict` return types catches shape mismatches at the call site; the mock-server test suite exercises every model against realistic fixture payloads, same as Rust's `wiremock` tests.
- [Risk] `httpx` is a new direct dependency (Rust: `reqwest`; Go: stdlib `net/http`; this is the first Python HTTP client dependency choice in the family). → Mitigation: `httpx` is broadly adopted, actively maintained, and this decision is documented here for the next language port to reference rather than re-litigate.
- [Risk] Sync-only client may need an async variant later if `dtrpg-app`'s Python tooling (if any) or a future async consumer needs it. → Mitigation: `httpx`'s sync/async API symmetry (`httpx.Client` / `httpx.AsyncClient` share method signatures) makes adding `AsyncLibraryClient` a mechanical follow-up, not a redesign.

## Migration Plan

Not applicable — net-new capability in a package that previously had none. No existing consumers to migrate.

## Open Questions

- Async client: revisit once a concrete consumer (app integration, a user-reported request) needs it — tracked as a follow-up, not blocking this change.
- Whether to add Pydantic once the model surface grows: revisit if hand-written `from_dict`/`to_dict` becomes unwieldy; not a blocker now.
