## Purpose
Define how the Python SDK wraps authentication around API access so callers get predictable Python-facing behavior without redefining the meaning of the API contract.
## Requirements
### Requirement: Python authentication flow must preserve API contract meaning
The Python SDK MUST define how its authentication surface coordinates with the API contract semantics owned by the API repository, without redefining token issuance, expiry, or refresh meaning in Python-specific terms.

#### Scenario: Authenticating through the Python SDK
- **WHEN** a caller invokes `authenticate(application_key, config)`
- **THEN** the SDK sends the application key to the API host, decodes the resulting `AuthTokenResponse` (token, refresh token, refresh token TTL), and returns it without altering its meaning

#### Scenario: Exchanging credentials for an application key
- **WHEN** a caller invokes `login_with_credentials(email, password, config)`
- **THEN** the SDK performs the two-step website-host exchange (validate credentials, then request an application key) and returns the application key, or raises `InvalidCredentialsError` if the first step reports invalid credentials without attempting the second step

### Requirement: Python SDK session lifecycle must distinguish voluntary logout from API-reported failure
The Python SDK MUST expose `clear_session()` for voluntary logout and a separate `invalidate_session(error)` for API-reported authentication failures, and MUST NOT collapse the two into a single method.

#### Scenario: Voluntary logout
- **WHEN** a caller invokes `sdk.clear_session()`
- **THEN** the active session is removed with no error recorded

#### Scenario: API reports an authentication failure
- **WHEN** a caller invokes `sdk.invalidate_session(error)` with a session active
- **THEN** the SDK clears the session and returns the same `AuthSessionError` it was given, without reclassifying it

#### Scenario: Invalidating with no active session
- **WHEN** a caller invokes `sdk.invalidate_session(error)` with no session active
- **THEN** the SDK raises `UnauthenticatedError`

### Requirement: Python authentication errors must preserve API meaning
The Python SDK MUST translate authentication failures into Python exceptions without obscuring the meaning of the underlying API failure.

#### Scenario: Authentication request fails
- **WHEN** the underlying HTTP call fails during `authenticate` or `login_with_credentials`
- **THEN** the Python SDK raises a `ClientError` subclass carrying the original status, message, and payload rather than a generic exception
