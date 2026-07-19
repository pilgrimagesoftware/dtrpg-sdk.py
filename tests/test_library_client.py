"""Mock-server tests for `LibraryClient`."""

from __future__ import annotations

import inspect

import httpx
import pytest
import respx

from dtrpg_sdk.config import Config
from dtrpg_sdk.errors import ApiError, DecodeFailedError, HttpError
from dtrpg_sdk.library.client import LibraryClient
from dtrpg_sdk.library.models import LibraryItemsParams, PageParams

BASE_URL = "http://testserver/api"


@pytest.fixture
def client() -> LibraryClient:
    """A `LibraryClient` pointed at a fake local API host for mocking."""
    return LibraryClient(
        Config(application_key="test-app-key", base_url=BASE_URL), "test-token"
    )


# ── Authorization header ────────────────────────────────────────────────────


@respx.mock
def test_authorization_header_carries_raw_token_without_bearer_prefix(
    client: LibraryClient,
) -> None:
    """Every request's `Authorization` header is exactly the raw token, no prefix."""
    route = respx.get(f"{BASE_URL}/vBeta/order_products").mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"self": "self-url"},
                "meta": {"itemsPerPage": 25, "currentPage": 1},
                "data": [],
            },
        )
    )

    client.list_order_products(LibraryItemsParams())

    assert route.calls.last.request.headers["Authorization"] == "test-token"


# ── list_order_products ─────────────────────────────────────────────────────


@respx.mock
def test_list_order_products_success(client: LibraryClient) -> None:
    """A successful `order_products` list response decodes correctly."""
    respx.get(f"{BASE_URL}/vBeta/order_products").mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"self": "self-url"},
                "meta": {"itemsPerPage": 25, "currentPage": 1},
                "data": [],
            },
        )
    )

    result = client.list_order_products(LibraryItemsParams(page=1, page_size=25))

    assert result.meta.current_page == 1
    assert result.data == []


@respx.mock
def test_list_order_products_query_params(client: LibraryClient) -> None:
    """`LibraryItemsParams` fields map to the documented query parameter names."""
    route = respx.get(f"{BASE_URL}/vBeta/order_products").mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"self": "self-url"},
                "meta": {"itemsPerPage": 25, "currentPage": 1},
                "data": [],
            },
        )
    )

    client.list_order_products(
        LibraryItemsParams(
            page=2,
            page_size=50,
            get_checksum=True,
            get_filters=True,
            library=True,
            archived=False,
            updated_date_after="2026-01-01",
        )
    )

    params = route.calls.last.request.url.params
    assert params["page"] == "2"
    assert params["pageSize"] == "50"
    assert params["getChecksum"] == "1"
    assert params["getFilters"] == "1"
    assert params["library"] == "true"
    assert params["archived"] == "0"
    assert params["updatedDate[after]"] == "2026-01-01"


@respx.mock
def test_list_order_products_non_success_raises_api_error_without_decode(
    client: LibraryClient,
) -> None:
    """A non-success status raises `ApiError` without a success-schema decode."""
    respx.get(f"{BASE_URL}/vBeta/order_products").mock(
        return_value=httpx.Response(500, text="not the success schema")
    )

    with pytest.raises(ApiError) as exc_info:
        client.list_order_products(LibraryItemsParams())

    assert exc_info.value.status == 500


@respx.mock
def test_list_order_products_malformed_success_body_raises_decode_failed(
    client: LibraryClient,
) -> None:
    """A success status with an undecodable body raises `DecodeFailedError`."""
    respx.get(f"{BASE_URL}/vBeta/order_products").mock(
        return_value=httpx.Response(200, json={"unexpected": "shape"})
    )

    with pytest.raises(DecodeFailedError):
        client.list_order_products(LibraryItemsParams())


@respx.mock
def test_get_order_product_decodes_sideloaded_included_array(
    client: LibraryClient,
) -> None:
    """The single-item detail endpoint decodes sideloaded `Publisher` resources."""
    respx.get(f"{BASE_URL}/vBeta/order_products/22654728").mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "id": "/api/vBeta/order_products/22654728",
                    "type": "order_product",
                    "attributes": {
                        "orderId": 7_332_333,
                        "productId": 144_239,
                        "royaltyPublisherId": 117,
                        "name": "Common Places - Free Map #1",
                        "finalPrice": 0.0,
                        "quantity": 1,
                        "bundleId": 0,
                        "archived": 0,
                        "orderProductId": 22_654_728,
                        "customerId": 399_144,
                        "files": [],
                    },
                    "relationships": {
                        "publisher": {
                            "data": {
                                "type": "Publisher",
                                "id": "/api/vBeta/publishers/117",
                            }
                        }
                    },
                },
                "included": [
                    {
                        "id": "/api/vBeta/publishers/117",
                        "type": "Publisher",
                        "attributes": {
                            "name": "The Forge Studios",
                            "publisherId": 117,
                            "slug": "the-forge-studios",
                        },
                    }
                ],
            },
        )
    )

    result = client.get_order_product(22_654_728)

    assert result.included is not None
    assert len(result.included) == 1
    publisher = result.included[0].as_publisher()
    assert publisher is not None
    assert publisher.name == "The Forge Studios"


# ── prepare_download ─────────────────────────────────────────────────────────


@respx.mock
def test_prepare_download_sends_required_index(client: LibraryClient) -> None:
    """`prepare_download` sends `index` as a query parameter and decodes the body."""
    route = respx.get(f"{BASE_URL}/vBeta/order_products/515276/prepare").mock(
        return_value=httpx.Response(200, json={"url": "https://example.com/download"})
    )

    result = client.prepare_download(515_276, 0)

    assert route.calls.last.request.url.params["index"] == "0"
    assert result == {"url": "https://example.com/download"}


def test_prepare_download_requires_index_argument(client: LibraryClient) -> None:
    """Calling `prepare_download` without `index` raises `TypeError`."""
    with pytest.raises(TypeError):
        client.prepare_download(515_276)  # type: ignore[call-arg]


def test_prepare_download_signature_has_no_default_for_index() -> None:
    """`prepare_download`'s `index` parameter has no default value in its signature."""
    signature = inspect.signature(LibraryClient.prepare_download)
    index_param = signature.parameters["index"]

    assert index_param.default is inspect.Parameter.empty


# ── Product Lists ─────────────────────────────────────────────────────────────


@respx.mock
def test_list_product_lists_success(client: LibraryClient) -> None:
    """A successful `product_lists` response decodes correctly."""
    respx.get(f"{BASE_URL}/vBeta/product_lists").mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"self": "self-url"},
                "meta": {"itemsPerPage": 25, "currentPage": 1},
                "data": [],
            },
        )
    )

    result = client.list_product_lists(PageParams())

    assert result.data == []


@respx.mock
def test_list_product_list_items_success(client: LibraryClient) -> None:
    """A successful `product_list_items` response decodes correctly."""
    route = respx.get(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(
            200,
            json={
                "links": {"self": "self-url"},
                "meta": {"itemsPerPage": 25, "currentPage": 1},
                "data": [],
            },
        )
    )

    result = client.list_product_list_items(86_151, PageParams())

    assert route.calls.last.request.url.params["productListId"] == "86151"
    assert result.data == []


@respx.mock
def test_create_product_list_decodes_json_api_envelope(client: LibraryClient) -> None:
    """`create_product_list` unwraps the JSON:API `{"data": {...}}` envelope."""
    respx.post(f"{BASE_URL}/vBeta/product_lists").mock(
        return_value=httpx.Response(
            201,
            json={
                "data": {
                    "id": "/api/vBeta/product_lists/86267",
                    "type": "ProductList",
                    "attributes": {
                        "customerId": 399_144,
                        "name": "Testing",
                        "dateCreated": "2026-07-09T00:42:39-05:00",
                        "productListId": 86_267,
                        "slug": "testing",
                        "itemCount": 0,
                    },
                }
            },
        )
    )

    result = client.create_product_list("Testing")

    assert result.id == "/api/vBeta/product_lists/86267"
    assert result.attributes.product_list_id == 86_267
    assert result.attributes.name == "Testing"


@respx.mock
def test_delete_product_list_succeeds_on_no_content(client: LibraryClient) -> None:
    """`delete_product_list` succeeds silently on a `204 No Content` response."""
    respx.delete(f"{BASE_URL}/vBeta/product_lists/86151").mock(
        return_value=httpx.Response(204)
    )

    client.delete_product_list(86_151)


@respx.mock
def test_delete_product_list_raises_http_error_on_failure_status(
    client: LibraryClient,
) -> None:
    """`delete_product_list` raises `HttpError` on a non-success status."""
    respx.delete(f"{BASE_URL}/vBeta/product_lists/86151").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(HttpError):
        client.delete_product_list(86_151)


@respx.mock
def test_add_product_list_item_returns_created_item(client: LibraryClient) -> None:
    """`add_product_list_item` returns the created item, unwrapping the envelope."""
    route = respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(
            201,
            json={
                "data": {
                    "id": "/api/vBeta/product_list_items/2629321",
                    "type": "ProductListItem",
                    "attributes": {
                        "productId": 515_276,
                        "productListId": 86_151,
                        "productListItemId": 2_629_321,
                    },
                }
            },
        )
    )

    result = client.add_product_list_item(86_151, 515_276)

    sent_body = route.calls.last.request.content
    assert b'"productId": 515276' in sent_body or b'"productId":515276' in sent_body
    assert result.product_id == 515_276
    assert result.product_list_id == 86_151
    assert result.product_list_item_id == 2_629_321


@respx.mock
def test_add_product_list_item_returns_api_error_on_failure_status(
    client: LibraryClient,
) -> None:
    """A non-success status on `add_product_list_item` raises `ApiError`."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 515_276)

    assert exc_info.value.status == 404


@respx.mock
def test_add_product_list_item_surfaces_validation_message_on_conflict(
    client: LibraryClient,
) -> None:
    """A `409` with a nested `error.message` surfaces that message on `ApiError`."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(
            409,
            json={
                "error": {
                    "id": "6a4ee5880bfda",
                    "message": (
                        "productId: Requires a valid Product ID. "
                        "Invalid value 22654728."
                    ),
                    "code": 409,
                    "status": 409,
                }
            },
        )
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 22_654_728)

    assert exc_info.value.status == 409
    assert exc_info.value.message == (
        "productId: Requires a valid Product ID. Invalid value 22654728."
    )


@respx.mock
def test_add_product_list_item_surfaces_field_keyed_validation_message(
    client: LibraryClient,
) -> None:
    """A flat field-keyed validation error body is joined into a readable message."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(
            422,
            json={"productId": "Requires a valid Product ID. Invalid value 22654728."},
        )
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 22_654_728)

    assert exc_info.value.message == (
        "productId: Requires a valid Product ID. Invalid value 22654728."
    )


@respx.mock
def test_delete_product_list_item_succeeds_on_no_content(client: LibraryClient) -> None:
    """`delete_product_list_item` succeeds silently on a `204 No Content` response."""
    respx.delete(f"{BASE_URL}/vBeta/product_list_items/2629321").mock(
        return_value=httpx.Response(204)
    )

    client.delete_product_list_item(2_629_321)


@respx.mock
def test_delete_product_list_item_raises_http_error_on_failure_status(
    client: LibraryClient,
) -> None:
    """`delete_product_list_item` raises `HttpError` on a non-success status."""
    respx.delete(f"{BASE_URL}/vBeta/product_list_items/2629321").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(HttpError):
        client.delete_product_list_item(2_629_321)


# ── Retry-After ──────────────────────────────────────────────────────────────


@respx.mock
def test_retry_after_present_delay_seconds_form(client: LibraryClient) -> None:
    """A `Retry-After: 30` header (delay-seconds form) is parsed as `30.0`."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "30"})
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 515_276)

    assert exc_info.value.status == 429
    assert exc_info.value.retry_after == 30.0


@respx.mock
def test_retry_after_absent_is_none(client: LibraryClient) -> None:
    """A missing `Retry-After` header results in `retry_after is None`."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 515_276)

    assert exc_info.value.retry_after is None


@respx.mock
def test_retry_after_http_date_form_is_none_not_a_parse_error(
    client: LibraryClient,
) -> None:
    """An HTTP-date `Retry-After` value results in `retry_after is None`."""
    respx.post(f"{BASE_URL}/vBeta/product_list_items").mock(
        return_value=httpx.Response(
            429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}
        )
    )

    with pytest.raises(ApiError) as exc_info:
        client.add_product_list_item(86_151, 515_276)

    assert exc_info.value.status == 429
    assert exc_info.value.retry_after is None
