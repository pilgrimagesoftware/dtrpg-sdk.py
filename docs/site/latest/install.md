---
title: Installation
version: latest
slug: install
---

# Installation

Requires Python 3.12+.

Not yet published to PyPI. Once released:

```bash
uv add dtrpg-sdk
```

or with `pip`:

```bash
pip install dtrpg-sdk
```

## Building from source

This repository uses the `dtrpg-api` repository as a submodule (`API/`),
matching the pattern used by the Go/Rust/Swift SDKs. Clone with submodules,
or initialize them after cloning:

```bash
git clone --recursive https://github.com/pilgrimagesoftware/dtrpg-sdk.py.git

# or, if already cloned:
git submodule update --init --recursive
```

Then install dependencies and run the test suite with `uv`:

```bash
uv sync --all-extras --dev
uv run pytest
```

See the [repository README](https://github.com/pilgrimagesoftware/dtrpg-sdk.py)
for linting, type checking, and the full development workflow.
