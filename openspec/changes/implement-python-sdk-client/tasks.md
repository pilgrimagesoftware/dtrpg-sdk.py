## 1. Setup

- [ ] 1.1 Add the `dtrpg-api` submodule under `API/` (`git submodule add git@github.com:pilgrimagesoftware/dtrpg-api.git API`)
- [ ] 1.2 Add `httpx` as a runtime dependency (`uv add httpx`)
- [ ] 1.3 Create the `src/dtrpg_sdk/{auth,library}/` package structure with `__init__.py` files

## 2. Configuration

- [ ] 2.1 Implement `Config` in `config.py`: `application_key`, `base_url` (default `https://api.drivethrurpg.com/api`), `api_version` (default `vBeta`), immutable dataclass, no env-var fallback
- [ ] 2.2 Unit tests: default values, custom `base_url`, no environment fallback

## 3. Errors

- [ ] 3.1 Implement `SdkError` base + `UnconfiguredError`, `UnauthenticatedError` in `errors.py`
- [ ] 3.2 Implement `ClientError` base + `HttpError`, `InvalidCredentialsError`, `ApplicationKeyRequestFailedError`, `DecodeFailedError`, `ApiError` (with `retry_after: float | None`) in `errors.py`
- [ ] 3.3 Implement `AuthSessionError` (`error_code`, `message`, `auth_state`) and `AuthState` enum (`UNAUTHENTICATED`, `TOKEN_INVALID`, `TOKEN_EXPIRED`, `REFRESH_EXPIRED`, `UNAUTHORIZED`) in `auth/session.py`

## 4. Auth / session lifecycle

- [ ] 4.1 Implement `AuthTokenResponse` (token, refresh_token, refresh_token_ttl) in `auth/session.py`
- [ ] 4.2 Implement `AuthSession` (`from_api_response`, `token`, `refresh_token`, `refresh_token_ttl`, `refresh_token_expired_at`, `invalidate` → `SessionTransition`) in `auth/session.py`
- [ ] 4.3 Implement `key_exchange.authenticate(application_key, config) -> AuthTokenResponse` (`POST {base_url}/{api_version}/auth_key?applicationKey=...`, empty JSON body, against the API host) in `auth/key_exchange.py`
- [ ] 4.4 Implement `credential_login.login_with_credentials(email, password, config) -> str` (two-step website-host exchange: `validate_login_credentials.php` then `create_account_app.php`, raising `InvalidCredentialsError`/`ApplicationKeyRequestFailedError` as appropriate) in `auth/credential_login.py`
- [ ] 4.5 Implement `DriveThruRpgSdk` in `sdk.py`: `__init__`, `with_config`, `configure`, `config`, `session`, `require_config`, `require_session`, `apply_auth_response`, `clear_session`, `invalidate_session`, `library_client`
- [ ] 4.6 Unit tests: session state transitions (unconfigured → configured → authenticated → cleared/invalidated), `invalidate_session` with and without an active session
- [ ] 4.7 Integration tests (mock HTTP server) for `authenticate` and `login_with_credentials`, covering success and each documented failure path

## 5. Library client — models

- [ ] 5.1 Implement pagination types: `PaginationLinks`, `PaginationMeta`, `PageParams`, `LibraryItemsParams`
- [ ] 5.2 Implement order-product model types: `FileChecksum`, `OrderProductFile`, `OrderProductAttributes`, `OrderProductItem`, `OrderProductRelationships`, `RelationshipRef`, `RelationshipData`, `OrderProductOrder`, `OrderProductPublisher`, `OrderProductFilter`, `OrderProductHistoryEntry`, `OrderProductAttribute`, `OrderProductDescription`
- [ ] 5.3 Implement sideloaded `included` handling: `PublisherAttributes`, `PublisherItem`, `IncludedItem` with `as_publisher()`/`as_product()`
- [ ] 5.4 Implement response types: `OrderProductListResponse`, `OrderProductItemResponse`
- [ ] 5.5 Implement product-list types: `ProductListAttributes`, `ProductListItem`, `ProductListCollectionResponse`, `ProductListItemsResponse`, `ProductListItemCreateRequest`, `ProductListItemCreateResponse` (with envelope-unwrapping `from_dict`)
- [ ] 5.6 Write `from_camel_case_dict` shared helper for wire-format field mapping

## 6. Library client — HTTP behavior

- [ ] 6.1 Implement `LibraryClient.__init__(config, token)` in `library/client.py`
- [ ] 6.2 Implement `endpoint(path)` URL builder and `auth_header()` (raw token, no `Bearer ` prefix)
- [ ] 6.3 Implement the central `decode_response` chokepoint: read status + `Retry-After` (delay-seconds only) before consuming the body; on non-success, extract an error message (top-level `message`, `error.message`, or field-keyed validation object) and raise `ApiError` without attempting success-schema decode; on success, decode into the target type or raise `DecodeFailedError`
- [ ] 6.4 Implement `list_order_products(params) -> OrderProductListResponse`
- [ ] 6.5 Implement `get_order_product(order_product_id) -> OrderProductItemResponse`
- [ ] 6.6 Implement `prepare_download(order_product_id, index) -> dict` — `index` required, no default
- [ ] 6.7 Implement `list_product_lists(params) -> ProductListCollectionResponse`
- [ ] 6.8 Implement `list_product_list_items(product_list_id, params) -> ProductListItemsResponse`
- [ ] 6.9 Implement `create_product_list(name) -> ProductListItem` (envelope-unwrapping decode)
- [ ] 6.10 Implement `delete_product_list(id) -> None` (raise_for_status shortcut, no body parsing)
- [ ] 6.11 Implement `add_product_list_item(product_list_id, product_id) -> ProductListItemCreateResponse`
- [ ] 6.12 Implement `delete_product_list_item(product_list_item_id) -> None` (raise_for_status shortcut)

## 7. Library client — tests

- [ ] 7.1 Mock-server tests for every `LibraryClient` method: success path, non-success status → `ApiError` (no success-schema decode attempted), `DecodeFailedError` on malformed success body
- [ ] 7.2 Mock-server tests for `Retry-After`: present (delay-seconds), absent, HTTP-date form (must not raise, `retry_after is None`)
- [ ] 7.3 Test the `Authorization` header carries the raw token with no `Bearer ` prefix
- [ ] 7.4 Test `prepare_download` requires `index` (calling without it is a `TypeError`, verified via signature inspection or a direct omission test)
- [ ] 7.5 Test JSON:API envelope unwrapping for `create_product_list` and `add_product_list_item` against realistic fixture payloads

## 8. Documentation

- [ ] 8.1 Update `README.md`: remove the "Status: in development" note, add a Quick Start example mirroring the Rust README's shape (`Config`, `authenticate`, `apply_auth_response`, `library_client`, `list_order_products`)
- [ ] 8.2 Ensure every public class/function has a docstring per `docs/python.md`'s doc-comment convention

## 9. Verification

- [ ] 9.1 `uv run ruff check .` and `uv run ruff format --check .` pass
- [ ] 9.2 `uv run pyrefly check` passes
- [ ] 9.3 `uv run pytest` passes with no skipped tests
- [ ] 9.4 CI (lint, typecheck, test) passes on the PR
