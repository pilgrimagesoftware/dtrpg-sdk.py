---
title: dtrpg-sdk.py documentation
version: latest
slug: index
---

# dtrpg-sdk.py documentation

`dtrpg-sdk` is a Python SDK for the [DriveThruRPG API](https://api.drivethrurpg.com).
It provides configuration, the credential-login and application-key auth
flows, session lifecycle management, and a `LibraryClient` covering order
products, download preparation, and product lists/product list items.
Requires Python 3.12+. This is the latest documentation.

## Getting started

- [Installation]({{ '/latest/install/' | relative_url }}) - add the package
  with `uv` or `pip`.
- [Quick start]({{ '/latest/quickstart/' | relative_url }}) - authenticate
  and fetch your library in a few lines.

## Using the SDK

- [Authentication]({{ '/latest/auth/' | relative_url }}) - the
  application-key and credential-login flows, and session lifecycle.
- [Library client]({{ '/latest/library/' | relative_url }}) - ordered
  products, downloads, and product lists.
- [Error handling]({{ '/latest/errors/' | relative_url }}) - the SDK's
  exception hierarchy and when each one is raised.

Select a release from the version picker when working with an earlier
release.

For a reference implementation of the same API surface in another
language, see the
[Go](https://github.com/pilgrimagesoftware/dtrpg-sdk.go),
[Rust](https://github.com/pilgrimagesoftware/dtrpg-sdk.rs), or
[Swift](https://github.com/pilgrimagesoftware/dtrpg-sdk.swift) SDKs.
