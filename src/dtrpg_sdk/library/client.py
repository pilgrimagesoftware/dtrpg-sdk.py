"""HTTP client for DriveThruRPG library endpoints.

`LibraryClient` provides a synchronous, authenticated interface to the
DriveThruRPG API's library-related endpoints, covering ordered products,
download preparation, product lists, and product list items.

All methods require a valid bearer token, captured when the client is
constructed. Create a `LibraryClient` via `DriveThruRpgSdk.library_client`
to ensure the SDK is both configured and authenticated before the client is
used.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, TypeVar

import httpx

from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import ApiError, DecodeFailedError, HttpError
from dtrpg_sdk.library.models import (
    LibraryItemsParams,
    OrderProductItemResponse,
    OrderProductListResponse,
    PageParams,
    ProductListCollectionResponse,
    ProductListItem,
    ProductListItemCreateRequest,
    ProductListItemCreateResponse,
    ProductListItemsResponse,
)

_LOG_PAYLOAD_LIMIT = 2_000
"""Maximum number of bytes logged from a failing response body."""

_logger = logging.getLogger(__name__)

T = TypeVar("T")


def _truncated_payload(raw: str) -> str:
    """Truncates a raw response body to `_LOG_PAYLOAD_LIMIT` characters for logging."""
    if len(raw) > _LOG_PAYLOAD_LIMIT:
        return f"{raw[:_LOG_PAYLOAD_LIMIT]}... (truncated)"
    return raw


def _extract_error_message(response: httpx.Response) -> str | None:
    """Extracts a human-readable error message from a non-success JSON response body.

    Recognizes three shapes seen across DriveThruRPG API error responses: a
    top-level `message` string; a nested `{"error": {"message": "..."}}`
    object (e.g. `product_list_items` failures); or a flat object keyed by
    field name whose values are a validation message string or an array of
    message strings (e.g. `{"productId": "Requires a valid Product ID.
    Invalid value 22654728."}`). Returns `None` if the body isn't a JSON
    object or matches none of these shapes, so the caller falls back to the
    raw payload.
    """
    try:
        value = response.json()
    except ValueError:
        return None
    if not isinstance(value, dict):
        return None

    message = value.get("message")
    if isinstance(message, str):
        return message

    error = value.get("error")
    if isinstance(error, dict):
        nested_message = error.get("message")
        if isinstance(nested_message, str):
            return nested_message

    parts: list[str] = []
    for field_name, detail in value.items():
        if isinstance(detail, str):
            parts.append(f"{field_name}: {detail}")
        elif isinstance(detail, list):
            for item in detail:
                if isinstance(item, str):
                    parts.append(f"{field_name}: {item}")

    return "; ".join(parts) if parts else None


def _parse_retry_after(response: httpx.Response) -> float | None:
    """Parses the `Retry-After` header, delay-seconds form only.

    Returns `None` if the header is absent or is not a plain integer (e.g.
    the HTTP-date form) -- no date-parsing dependency is added for a form
    the API is judged unlikely to send on 429s.
    """
    value = response.headers.get("Retry-After")
    if value is None:
        return None
    try:
        return float(int(value.strip()))
    except ValueError:
        return None


class LibraryClient:
    """An authenticated HTTP client for DriveThruRPG library endpoints.

    `LibraryClient` combines SDK configuration and an active bearer token to
    authenticate all outgoing requests. Every method maps to a specific API
    endpoint and returns a fully decoded Python type.

    Prefer `DriveThruRpgSdk.library_client` over constructing this directly,
    as that method validates both configuration and session state before
    constructing the client.

    Examples:
        >>> from dtrpg_sdk import Config, DriveThruRpgSdk, AuthTokenResponse
        >>> app_config = Config(application_key="my-app-key")
        >>> sdk = DriveThruRpgSdk.with_config(app_config)
        >>> token_response = AuthTokenResponse("token", "refresh", 9_999_999_999)
        >>> _ = sdk.apply_auth_response(token_response)
        >>> client = sdk.library_client()
    """

    def __init__(self, config: Config, token: str) -> None:
        """Creates a new `LibraryClient` from the given config and bearer token."""
        self._config = config
        self._token = token
        self._http = httpx.Client()

    def endpoint(self, path: str) -> str:
        """Builds the full URL for a versioned API path segment.

        Combines the configured base URL, API version, and the given
        resource path into a single URL string:
        `{base_url}/{api_version}/{path}`.
        """
        return f"{self._config.base_url}/{self._config.api_version}/{path}"

    def auth_header(self) -> str:
        """Returns the `Authorization` header value for the active session.

        The DTRPG API expects the raw JWT token without a `Bearer` prefix.
        """
        return self._token

    def _decode_response(
        self, url: str, response: httpx.Response, decode: Callable[[dict[str, Any]], T]
    ) -> T:
        """Reads a response body and decodes it via `decode`.

        A non-success status is treated as a request failure rather than a
        decode attempt: the body is never passed to `decode` in that case
        (`decode` describes the success schema, so trying to parse an error
        body against it produces a confusing "missing field" decode error
        instead of the API's actual message). Instead a human-readable
        message is extracted from the body and raised via `ApiError`.

        On a success status whose body still fails to decode, the raw
        payload is logged at ERROR level (truncated) and a
        `DecodeFailedError` is raised so callers have both the decode cause
        and the offending payload for diagnosis.
        """
        status = response.status_code
        retry_after = _parse_retry_after(response)

        if not (200 <= status < 300):
            payload = _truncated_payload(response.text)
            message = _extract_error_message(response)
            _logger.error(
                "API request failed: url=%s status=%s payload=%s message=%s",
                url,
                status,
                payload,
                message or "",
            )
            raise ApiError(
                url=url,
                status=status,
                message=message,
                payload=payload,
                retry_after=retry_after,
            )

        try:
            data = response.json()
            return decode(data)
        except (ValueError, KeyError, TypeError) as cause:
            payload = _truncated_payload(response.text)
            _logger.error(
                "API response decode failed: url=%s status=%s payload=%s error=%s",
                url,
                status,
                payload,
                cause,
            )
            raise DecodeFailedError(
                url=url, status=status, cause=cause, payload=payload
            ) from cause

    def _get(
        self, url: str, params: list[tuple[str, str | int | float | bool | None]]
    ) -> httpx.Response:
        """Sends an authenticated `GET` request and returns the raw response."""
        _logger.debug("SDK request: GET %s", url)
        try:
            response = self._http.get(
                url,
                params=httpx.QueryParams(params),
                headers={"Authorization": self.auth_header()},
            )
        except httpx.HTTPError as cause:
            raise HttpError(cause) from cause
        _logger.debug("SDK response: %s -> %s", url, response.status_code)
        return response

    def _post(self, url: str, json_body: dict[str, Any]) -> httpx.Response:
        """Sends an authenticated `POST` request and returns the raw response."""
        _logger.debug("SDK request: POST %s", url)
        try:
            response = self._http.post(
                url, json=json_body, headers={"Authorization": self.auth_header()}
            )
        except httpx.HTTPError as cause:
            raise HttpError(cause) from cause
        _logger.debug("SDK response: %s -> %s", url, response.status_code)
        return response

    def _delete(self, url: str) -> httpx.Response:
        """Sends an authenticated `DELETE` request and returns the raw response."""
        _logger.debug("SDK request: DELETE %s", url)
        try:
            response = self._http.delete(
                url, headers={"Authorization": self.auth_header()}
            )
        except httpx.HTTPError as cause:
            raise HttpError(cause) from cause
        _logger.debug("SDK response: %s -> %s", url, response.status_code)
        return response

    # ── Ordered Products ──────────────────────────────────────────────────────

    def list_order_products(
        self, params: LibraryItemsParams
    ) -> OrderProductListResponse:
        """Fetches a paginated list of ordered products from the user's library.

        Maps to `GET /{api_version}/order_products`.

        Authentication is supplied via the `Authorization` header containing
        the raw JWT token. All non-`None` fields of `params` are included as
        query parameters.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint("order_products")

        query: list[tuple[str, str | int | float | bool | None]] = []
        if params.page is not None:
            query.append(("page", str(params.page)))
        if params.page_size is not None:
            query.append(("pageSize", str(params.page_size)))
        if params.get_checksum is True:
            query.append(("getChecksum", "1"))
        if params.get_filters is True:
            query.append(("getFilters", "1"))
        if params.library is True:
            query.append(("library", "true"))
        if params.archived is not None:
            query.append(("archived", "1" if params.archived else "0"))
        if params.updated_date_after is not None:
            query.append(("updatedDate[after]", params.updated_date_after))

        response = self._get(url, query)
        return self._decode_response(url, response, OrderProductListResponse.from_dict)

    def get_order_product(self, order_product_id: int) -> OrderProductItemResponse:
        """Fetches the details of a single ordered product by its identifier.

        Maps to `GET /{api_version}/order_products/{order_product_id}`.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint(f"order_products/{order_product_id}")
        response = self._get(url, [])
        return self._decode_response(url, response, OrderProductItemResponse.from_dict)

    def prepare_download(self, order_product_id: int, index: int) -> dict[str, Any]:
        """Prepares a download for the given ordered product's file.

        Maps to `GET /{api_version}/order_products/{order_product_id}/prepare`
        with a required `index` query parameter. `index` identifies which
        file within the ordered product to prepare
        -- it matches `OrderProductFile.index` -- and is required: the API
        rejects the request with an error if it is omitted.

        The response is returned as a raw dict because the response schema
        for this endpoint has not yet been formally defined by the API
        contract. The type will be tightened in a future change once the
        API contract matures.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint(f"order_products/{order_product_id}/prepare")
        response = self._get(url, [("index", str(index))])
        return self._decode_response(url, response, dict)

    # ── Product Lists ─────────────────────────────────────────────────────────

    def list_product_lists(self, params: PageParams) -> ProductListCollectionResponse:
        """Fetches a paginated list of product lists belonging to the user.

        Maps to `GET /{api_version}/product_lists`.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint("product_lists")

        query: list[tuple[str, str | int | float | bool | None]] = []
        if params.page is not None:
            query.append(("page", str(params.page)))
        if params.page_size is not None:
            query.append(("pageSize", str(params.page_size)))

        response = self._get(url, query)
        return self._decode_response(
            url, response, ProductListCollectionResponse.from_dict
        )

    def list_product_list_items(
        self, product_list_id: int, params: PageParams
    ) -> ProductListItemsResponse:
        """Fetches a paginated list of items within a specific product list.

        Maps to `GET /{api_version}/product_list_items?productListId={product_list_id}`.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint("product_list_items")

        query: list[tuple[str, str | int | float | bool | None]] = [
            ("productListId", str(product_list_id))
        ]
        if params.page is not None:
            query.append(("page", str(params.page)))
        if params.page_size is not None:
            query.append(("pageSize", str(params.page_size)))

        response = self._get(url, query)
        return self._decode_response(url, response, ProductListItemsResponse.from_dict)

    def create_product_list(self, name: str) -> ProductListItem:
        """Creates a new product list with the given name.

        Maps to `POST /{api_version}/product_lists` with a JSON body
        `{"name": "<name>"}`. The API wraps the created resource in a
        JSON:API envelope (`{"data": {...}}`), which is unwrapped here.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint("product_lists")
        response = self._post(url, {"name": name})
        return self._decode_response(
            url, response, lambda data: ProductListItem.from_dict(data["data"])
        )

    def delete_product_list(self, id_: int) -> None:
        """Deletes a product list by id.

        Raises:
            HttpError: On any transport failure or non-success HTTP status.
        """
        url = self.endpoint(f"product_lists/{id_}")
        response = self._delete(url)
        if not (200 <= response.status_code < 300):
            raise HttpError(
                httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            )

    def add_product_list_item(
        self, product_list_id: int, product_id: int
    ) -> ProductListItemCreateResponse:
        """Adds a product to a product list as a member.

        Maps to `POST /{api_version}/product_list_items`.

        Raises:
            HttpError: On any transport failure.
            ApiError: On a non-success HTTP status.
            DecodeFailedError: If the success response cannot be decoded.
        """
        url = self.endpoint("product_list_items")
        body = ProductListItemCreateRequest(
            product_id=product_id, product_list_id=product_list_id
        )
        response = self._post(url, body.to_wire_dict())
        return self._decode_response(
            url, response, ProductListItemCreateResponse.from_dict
        )

    def delete_product_list_item(self, product_list_item_id: int) -> None:
        """Removes a product list item by its own id (not the product's id).

        Maps to `DELETE /{api_version}/product_list_items/{product_list_item_id}`.

        Raises:
            HttpError: On any transport failure or non-success HTTP status.
        """
        url = self.endpoint(f"product_list_items/{product_list_item_id}")
        response = self._delete(url)
        if not (200 <= response.status_code < 300):
            raise HttpError(
                httpx.HTTPStatusError(
                    f"HTTP {response.status_code}",
                    request=response.request,
                    response=response,
                )
            )
