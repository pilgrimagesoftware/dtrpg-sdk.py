## Purpose
Define how the Python SDK accepts and applies caller configuration so client initialization stays explicit, Python-idiomatic, and aligned with the underlying API contract.
## Requirements
### Requirement: Python SDK configuration must be explicit before use
The Python SDK MUST require the configuration values needed to initialize its client behavior before authenticated operations are attempted, including the values needed to drive auth/session behavior.

#### Scenario: Attempting to use the SDK without configuration
- **WHEN** a caller invokes authenticated Python SDK behavior before providing the required configuration
- **THEN** the SDK raises an `UnconfiguredError`

#### Scenario: Providing configuration for auth/session behavior
- **WHEN** a caller constructs `Config(application_key=...)` and passes it to the SDK
- **THEN** the Python SDK has the configuration needed to apply its documented authentication and session lifecycle behavior

### Requirement: Python SDK configuration must remain Python-idiomatic and free of environment-variable magic
The Python SDK MUST expose configuration only through explicit constructor arguments, with no implicit environment-variable or config-file loading, matching the Rust SDK's configuration model.

#### Scenario: Configuring a custom API endpoint
- **WHEN** a caller constructs `Config(application_key=..., base_url=...)`
- **THEN** the SDK applies that base URL for all subsequent requests instead of the default

#### Scenario: No environment-variable fallback exists
- **WHEN** a caller does not pass an `application_key` explicitly
- **THEN** the SDK does not attempt to read one from an environment variable or config file — construction fails with a `TypeError` for the missing required argument

### Requirement: Python SDK ships the API contract as a submodule for traceability
The Python SDK MUST include `API/openapi.yaml` (the `dtrpg-api` submodule) in the repository so the package has a direct, verifiable dependency on the same API contract used by the other SDKs.

#### Scenario: Building the Python SDK from source
- **WHEN** a contributor clones `dtrpg-sdk.py` with submodules
- **THEN** `API/openapi.yaml` is present and can be diffed against the contract other SDKs consume
