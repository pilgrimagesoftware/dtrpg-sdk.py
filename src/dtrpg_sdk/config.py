"""SDK configuration types.

`Config` holds the application-level settings required to make requests to the
DriveThruRPG API: the publisher/application key, the API base URL, and the API
version segment used in request URLs.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.drivethrurpg.com/api"
"""The production DriveThruRPG API base URL used when no custom URL is provided."""

DEFAULT_API_VERSION = "vBeta"
"""The API version path segment used when no custom version is provided."""


@dataclass(frozen=True)
class Config:
    """Configuration for the DriveThruRPG SDK.

    A `Config` must be provided to `DriveThruRpgSdk` before any authenticated API
    calls can be made. It binds an application key to an API endpoint, defaulting
    to the production DriveThruRPG API and the current `"vBeta"` API version.

    There is no environment-variable or config-file fallback: `application_key`
    is a required constructor argument, and omitting it fails construction with
    a `TypeError`.

    Examples:
        >>> config = Config(application_key="my-app-key")
        >>> config.base_url
        'https://api.drivethrurpg.com/api'

        >>> staging = Config(application_key="my-app-key", base_url="http://localhost:8080/api")
        >>> staging.base_url
        'http://localhost:8080/api'
    """

    application_key: str
    base_url: str = DEFAULT_BASE_URL
    api_version: str = DEFAULT_API_VERSION
