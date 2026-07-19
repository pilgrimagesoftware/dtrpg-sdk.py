"""A Python SDK for the DriveThruRPG API.

This package provides types and structures for authenticating with,
configuring, and making requests to the DriveThruRPG API. It covers:

- **Configuration** -- supplying your application key, API base URL, and API
  version via `Config`.
- **Authentication** -- representing token responses, active sessions, and
  session state via `AuthTokenResponse`, `AuthSession`, and `AuthState`.
- **Error handling** -- structured errors for SDK-level, session-level, and
  HTTP failures via `SdkError`, `AuthSessionError`, and `ClientError`.
- **SDK entry point** -- `DriveThruRpgSdk` ties configuration and session
  lifecycle together and vends a `LibraryClient` once authenticated.
- **Library access** -- `LibraryClient` provides a synchronous HTTP client
  for all library endpoints (ordered products, product lists, download
  preparation).
- **Library types** -- Python model types for every API-defined library
  schema, such as `OrderProductItem`, `ProductListItem`, and their
  supporting structures.

Quick Start:
    >>> from dtrpg_sdk import Config, DriveThruRpgSdk, AuthTokenResponse
    >>> sdk = DriveThruRpgSdk.with_config(Config(application_key="my-app-key"))
    >>> response = AuthTokenResponse("jwt-token", "refresh-token", 1_800_000_000)
    >>> session = sdk.apply_auth_response(response)
    >>> session.token
    'jwt-token'
    >>> client = sdk.library_client()
"""

from __future__ import annotations

from dtrpg_sdk.auth.session import (
    AuthSession,
    AuthSessionError,
    AuthState,
    AuthTokenResponse,
    SessionTransition,
)
from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import (
    ApiError,
    ApplicationKeyRequestFailedError,
    ClientError,
    DecodeFailedError,
    HttpError,
    InvalidCredentialsError,
    SdkError,
    UnauthenticatedError,
    UnconfiguredError,
)
from dtrpg_sdk.library import (
    FileChecksum,
    IncludedItem,
    LibraryClient,
    LibraryItemsParams,
    OrderProductAttribute,
    OrderProductAttributes,
    OrderProductDescription,
    OrderProductFile,
    OrderProductFilter,
    OrderProductHistoryEntry,
    OrderProductInfo,
    OrderProductItem,
    OrderProductItemResponse,
    OrderProductListResponse,
    OrderProductOrder,
    OrderProductPublisher,
    OrderProductRelationships,
    PageParams,
    PaginationLinks,
    PaginationMeta,
    ProductListAttributes,
    ProductListCollectionResponse,
    ProductListItem,
    ProductListItemCreateRequest,
    ProductListItemCreateResponse,
    ProductListItemsResponse,
    PublisherAttributes,
    PublisherItem,
    RelationshipData,
    RelationshipRef,
)
from dtrpg_sdk.sdk import DriveThruRpgSdk

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ApiError",
    "ApplicationKeyRequestFailedError",
    "AuthSession",
    "AuthSessionError",
    "AuthState",
    "AuthTokenResponse",
    "ClientError",
    "Config",
    "DecodeFailedError",
    "DriveThruRpgSdk",
    "FileChecksum",
    "HttpError",
    "IncludedItem",
    "InvalidCredentialsError",
    "LibraryClient",
    "LibraryItemsParams",
    "OrderProductAttribute",
    "OrderProductAttributes",
    "OrderProductDescription",
    "OrderProductFile",
    "OrderProductFilter",
    "OrderProductHistoryEntry",
    "OrderProductInfo",
    "OrderProductItem",
    "OrderProductItemResponse",
    "OrderProductListResponse",
    "OrderProductOrder",
    "OrderProductPublisher",
    "OrderProductRelationships",
    "PageParams",
    "PaginationLinks",
    "PaginationMeta",
    "ProductListAttributes",
    "ProductListCollectionResponse",
    "ProductListItem",
    "ProductListItemCreateRequest",
    "ProductListItemCreateResponse",
    "ProductListItemsResponse",
    "PublisherAttributes",
    "PublisherItem",
    "RelationshipData",
    "RelationshipRef",
    "SdkError",
    "SessionTransition",
    "UnauthenticatedError",
    "UnconfiguredError",
]
