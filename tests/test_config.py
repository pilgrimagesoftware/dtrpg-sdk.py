"""Unit tests for `Config`."""

from __future__ import annotations

import dataclasses

import pytest

from dtrpg_sdk.config import DEFAULT_API_VERSION, DEFAULT_BASE_URL, Config


def test_default_values_use_production_api() -> None:
    """A `Config` constructed with only an application key uses production defaults."""
    config = Config(application_key="my-app-key")

    assert config.application_key == "my-app-key"
    assert config.base_url == DEFAULT_BASE_URL
    assert config.api_version == DEFAULT_API_VERSION


def test_custom_base_url_overrides_default() -> None:
    """A caller-supplied `base_url` overrides the production default."""
    config = Config(application_key="my-app-key", base_url="http://localhost:8080/api")

    assert config.base_url == "http://localhost:8080/api"
    assert config.api_version == DEFAULT_API_VERSION


def test_custom_api_version_overrides_default() -> None:
    """A caller-supplied `api_version` overrides the `"vBeta"` default."""
    config = Config(application_key="my-app-key", api_version="v1")

    assert config.api_version == "v1"


def test_no_environment_fallback_missing_application_key_raises_type_error() -> None:
    """Omitting `application_key` fails construction; there is no env-var fallback."""
    with pytest.raises(TypeError):
        Config()  # type: ignore[call-arg]


def test_config_is_immutable() -> None:
    """`Config` instances cannot be mutated after construction."""
    config = Config(application_key="my-app-key")

    with pytest.raises(dataclasses.FrozenInstanceError):
        config.application_key = "other-key"  # type: ignore[misc]
