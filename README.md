# dtrpg-sdk.py

[![CI](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/actions/workflows/ci.yaml/badge.svg)](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)

A Python SDK for the [DriveThruRPG API](https://api.drivethrurpg.com).

Requires Python 3.12+.

Provides configuration, the credential-login and application-key auth flows, session
lifecycle management, and a `LibraryClient` covering order products, download
preparation, and product lists/product list items. For a reference implementation of
the same API surface in another language, see the
[Go](https://github.com/pilgrimagesoftware/dtrpg-sdk.go), [Rust](https://github.com/pilgrimagesoftware/dtrpg-sdk.rs),
or [Swift](https://github.com/pilgrimagesoftware/dtrpg-sdk.swift) SDKs.

## Installation

Not yet published to PyPI. Once released:

```bash
uv add dtrpg-sdk
```

## Quick Start

```python
from dtrpg_sdk import Config, DriveThruRpgSdk, LibraryItemsParams
from dtrpg_sdk.auth import key_exchange

config = Config(application_key="my-app-key")
sdk = DriveThruRpgSdk.with_config(config)

# Exchange the application key for a session token.
token_response = key_exchange.authenticate("my-app-key", config)
sdk.apply_auth_response(token_response)

# Build an authenticated library client and fetch the user's library.
client = sdk.library_client()
products = client.list_order_products(LibraryItemsParams(page=1, page_size=25))
for item in products.data:
    print(item.attributes.name)
```

## Building from source

This repository uses the `dtrpg-api` repository as a submodule (`API/`), matching the
pattern used by the Go/Rust/Swift SDKs. Clone with submodules, or initialize them after
cloning:

```bash
git clone --recursive https://github.com/pilgrimagesoftware/dtrpg-sdk.py.git

# or, if already cloned:
git submodule update --init --recursive
```

## Development

```bash
uv sync --all-extras --dev
uv run ruff check .
uv run ruff format --check .
uv run pyrefly check
uv run pytest
```

See [docs/python.md](https://github.com/pilgrimagesoftware/dtrpg/blob/master/docs/python.md) in
the umbrella repo for the full set of conventions this project follows.

## Release Process

See [RELEASE.md](RELEASE.md).

## License

MIT — see [LICENSE.md](LICENSE.md).
