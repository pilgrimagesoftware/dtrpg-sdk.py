## Purpose
Define Python SDK behavior for library backend operations (order products, download preparation, product lists) used by consuming applications.
## Requirements
### Requirement: The Python SDK MUST provide a client for all library endpoints
The Python SDK MUST expose a `LibraryClient` that callers can use to fetch ordered products, product details, download preparation, product lists, and product list items from the DriveThruRPG API.

#### Scenario: Fetching the user's library
- **WHEN** a caller invokes `library_client.list_order_products(params)`
- **THEN** the SDK sends the authenticated request and returns a deserialized `OrderProductListResponse`

### Requirement: The Python library client MUST be created from a configured, authenticated SDK instance
`LibraryClient` construction via `sdk.library_client()` MUST require both SDK configuration and an active authentication session.

#### Scenario: Creating a library client from the SDK
- **WHEN** a caller invokes `sdk.library_client()` on an unconfigured or unauthenticated SDK instance
- **THEN** the SDK raises `UnconfiguredError` or `UnauthenticatedError` respectively, before any HTTP request is made

### Requirement: The Python library client MUST authenticate requests using the raw session token
Every library API request MUST include an `Authorization` header carrying the session's raw token, with no `Bearer ` prefix, matching the DriveThruRPG API's documented behavior.

#### Scenario: Sending an authenticated library request
- **WHEN** the Python library client sends a request to any library endpoint
- **THEN** the request's `Authorization` header value is exactly the session token, with no prefix

### Requirement: Download preparation MUST include the target file's index
`prepare_download` MUST require the caller to supply the target file's `index` (its position within the ordered product's file list) as a required parameter, matching what the DriveThruRPG API enforces.

#### Scenario: Preparing a download with a valid index
- **WHEN** a caller invokes `prepare_download(order_product_id, index)` with a valid order product ID and the target file's index
- **THEN** the SDK sends the request with the index included and returns the deserialized response on success

#### Scenario: No default index is silently assumed
- **WHEN** a caller invokes `prepare_download` without supplying `index`
- **THEN** the call raises a `TypeError` for the missing required argument — there is no default value

### Requirement: Non-success responses MUST NOT be decoded against the success schema
When a library request returns a non-success HTTP status, the Python SDK MUST NOT attempt to parse the response body as the endpoint's success type, and MUST surface the API's own error message when present.

#### Scenario: API returns a validation error
- **WHEN** a library endpoint returns a non-success status with a JSON error body
- **THEN** the SDK raises `ApiError` carrying the extracted message, HTTP status, and raw payload, without attempting to construct the success response type from that body

### Requirement: Rate-limited responses MUST surface the Retry-After value
When a library request receives a `429` response with a `Retry-After` header in delay-seconds form, the Python SDK MUST parse and expose that value on the raised error.

#### Scenario: API rate-limits a request
- **WHEN** a library endpoint returns HTTP 429 with a `Retry-After: 30` header
- **THEN** the raised `ApiError` exposes `retry_after == 30.0`

#### Scenario: Retry-After is absent or in HTTP-date form
- **WHEN** a library endpoint returns HTTP 429 without a `Retry-After` header, or with one in HTTP-date form
- **THEN** the raised `ApiError` exposes `retry_after is None` rather than raising a parse error
