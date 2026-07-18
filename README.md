# dtrpg-sdk.py

[![CI](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/actions/workflows/ci.yaml/badge.svg)](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/actions/workflows/ci.yaml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)

A Python SDK for the [DriveThruRPG API](https://api.drivethrurpg.com).

Requires Python 3.12+.

**Status: in development.** This repository currently provides the package scaffolding
(build, lint, type check, test, and release pipeline). Configuration, authentication/session
lifecycle, and the library client (orders, product lists, download preparation) are not yet
implemented — see [dtrpg-sdk.py#1](https://github.com/pilgrimagesoftware/dtrpg-sdk.py/issues/1)
for progress. For a complete reference implementation of the same API surface, see the
[Go](https://github.com/pilgrimagesoftware/dtrpg-sdk.go), [Rust](https://github.com/pilgrimagesoftware/dtrpg-sdk.rs),
or [Swift](https://github.com/pilgrimagesoftware/dtrpg-sdk.swift) SDKs.

## Installation

Not yet published to PyPI. Once released:

```bash
uv add dtrpg-sdk
```

## Building from source

This repository will use the `dtrpg-api` repository as a submodule (`API/`) once the
`dtrpg-api` integration lands, matching the pattern used by the Go/Rust/Swift SDKs. Clone
with submodules, or initialize them after cloning:

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
