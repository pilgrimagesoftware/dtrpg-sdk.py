"""Library resource types for the DriveThruRPG SDK.

This module provides Python model types that mirror the API-defined schemas
for library resources: ordered products, product files, product lists, and
associated pagination and metadata structures.

Every response type implements a `from_dict` classmethod that decodes it
from the raw JSON payload returned by the DriveThruRPG API. Field names
follow the API contract and are mapped from camelCase JSON to snake_case
Python conventions via the shared `from_camel_case_dict` helper, except
where a field is semantically renamed (e.g. JSON `type` -> `resource_type`,
JSON `self` -> `self_`), which is handled explicitly per class.

Query parameter types (`LibraryItemsParams`, `PageParams`) are plain
dataclasses with no wire-format mapping; they are consumed by
`LibraryClient` methods to build URL query strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import Any, TypeVar

T = TypeVar("T")

_CAMEL_BOUNDARY_RE = re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Za-z])(?=[0-9])")


def camel_to_snake(name: str) -> str:
    """Converts a camelCase (or Mixed-acronym) identifier to snake_case.

    Handles runs of uppercase letters (e.g. `"sizeMB"` -> `"size_mb"`) and
    letter/digit boundaries (e.g. `"thumbnail100"` -> `"thumbnail_100"`)
    correctly, matching the field names used throughout this module.
    """
    return _CAMEL_BOUNDARY_RE.sub("_", name).lower()


def _camel_case_kwargs(data: dict[str, Any], cls: type) -> dict[str, Any]:
    """Filters and converts a camelCase dict's keys to `cls`'s field names."""
    field_names = {f.name for f in fields(cls)}
    kwargs: dict[str, Any] = {}
    for key, value in data.items():
        snake_key = camel_to_snake(key)
        if snake_key in field_names:
            kwargs[snake_key] = value
    return kwargs


def from_camel_case_dict(data: dict[str, Any], cls: type[T]) -> T:
    """Constructs a dataclass instance from a wire-format (camelCase) JSON dict.

    Converts every key in `data` from camelCase to snake_case and passes
    only the keys matching `cls`'s declared field names to its constructor.
    Suitable for classes whose fields are all primitives; classes with
    nested or semantically renamed fields build their own `from_dict`
    using `_camel_case_kwargs` plus explicit overrides.
    """
    return cls(**_camel_case_kwargs(data, cls))  # type: ignore[call-arg]


# ── Pagination ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class PaginationLinks:
    """Pagination links included in all paginated API responses."""

    self_: str
    """The canonical URL for the current page of results."""

    first: str | None = None
    """URL for the first page of results, if available."""

    last: str | None = None
    """URL for the last page of results, if available."""

    prev: str | None = None
    """URL for the previous page of results, if available."""

    next: str | None = None
    """URL for the next page of results, if available."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PaginationLinks:
        """Decodes `PaginationLinks`, mapping the reserved-word JSON key `self`."""
        return PaginationLinks(
            self_=data["self"],
            first=data.get("first"),
            last=data.get("last"),
            prev=data.get("prev"),
            next=data.get("next"),
        )


@dataclass(frozen=True)
class PaginationMeta:
    """Pagination metadata included in all paginated API responses."""

    items_per_page: int
    """The number of items returned per page."""

    current_page: int
    """The current page number (1-based)."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PaginationMeta:
        """Decodes `PaginationMeta` from its camelCase JSON payload."""
        return from_camel_case_dict(data, PaginationMeta)


# ── File / Checksum ───────────────────────────────────────────────────────────


@dataclass(frozen=True)
class FileChecksum:
    """Checksum information for a single downloadable product file."""

    checksum: str
    """The checksum hash string for the file."""

    checksum_date: str
    """The date when the checksum was generated (ISO 8601 string)."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> FileChecksum:
        """Decodes a `FileChecksum` from its camelCase JSON payload."""
        return from_camel_case_dict(data, FileChecksum)


@dataclass(frozen=True)
class OrderProductFile:
    """A downloadable file associated with an ordered product."""

    index: int
    """The index of this file within the ordered product's file list."""

    order_product_download_id: int
    """The unique identifier for this specific download record."""

    title: str
    """The display title of the file."""

    filename: str
    """The filename as it will appear when downloaded."""

    size: int
    """The file size in bytes."""

    size_mb: str
    """The file size expressed in megabytes as a formatted string."""

    checksums: list[FileChecksum] = field(default_factory=list)
    """Checksums available for verifying the integrity of the downloaded file.

    The API may return `null` or omit this field for products without
    checksum data; treated as an empty list.
    """

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductFile:
        """Decodes an `OrderProductFile`, including its nested checksum list."""
        kwargs = _camel_case_kwargs(data, OrderProductFile)
        kwargs["checksums"] = [
            FileChecksum.from_dict(c) for c in (data.get("checksums") or [])
        ]
        return OrderProductFile(**kwargs)


# ── Filters / History / Attributes ───────────────────────────────────────────


@dataclass(frozen=True)
class OrderProductFilter:
    """A filter category associated with an ordered product.

    Populated when `getFilters=1` is included in the request.
    """

    filter_id: int
    """The unique identifier of this filter category."""

    parent_filter_id: int
    """The unique identifier of this filter's parent category."""

    name: str
    """The display name of this filter category."""

    parent_name: str
    """The display name of this filter's parent category."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductFilter:
        """Decodes an `OrderProductFilter` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductFilter)


@dataclass(frozen=True)
class OrderProductHistoryEntry:
    """A single history entry recording a change made to an ordered product."""

    changed: str
    """The date and time when the change occurred (ISO 8601 string)."""

    changes: str
    """A human-readable description of what changed."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductHistoryEntry:
        """Decodes an `OrderProductHistoryEntry` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductHistoryEntry)


@dataclass(frozen=True)
class OrderProductAttribute:
    """An individual attribute option associated with an ordered product.

    Attributes describe purchase options such as format or edition.
    """

    order_id: int
    """The unique identifier of the order this attribute belongs to."""

    option_name: str
    """The name of the option (e.g., `"Format"`)."""

    option_value_name: str
    """The display name of the selected option value (e.g., `"PDF"`)."""

    price: str
    """The price associated with this option, as a formatted string."""

    price_prefix: str
    """A prefix to display before the price (e.g., `"$"`)."""

    option_value_id: int
    """The unique identifier for the selected option value."""

    option_type: str
    """The type classification of this option."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductAttribute:
        """Decodes an `OrderProductAttribute` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductAttribute)


# ── OrderProduct ──────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OrderProductPublisher:
    """Publisher metadata embedded directly on an ordered product's attributes."""

    name: str
    """The display name of the publisher."""

    publisher_id: int
    """The unique identifier of the publisher."""

    slug: str
    """The URL slug for the publisher's storefront page."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductPublisher:
        """Decodes an `OrderProductPublisher` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductPublisher)


@dataclass(frozen=True)
class OrderProductDescription:
    """Descriptive text for a product, embedded within `OrderProductInfo`."""

    name: str
    """The display name of the product."""

    slug: str
    """The URL slug for the product's storefront page."""

    purchase_note: str | None = None
    """HTML purchase note shown to the customer, if any."""

    short_description: str | None = None
    """A short marketing description of the product."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductDescription:
        """Decodes an `OrderProductDescription` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductDescription)


@dataclass(frozen=True)
class OrderProductInfo:
    """Product catalog metadata embedded on an ordered product's attributes.

    Includes relative paths to cover images. Image paths (`image`,
    `web_image`, `thumbnail`, `thumbnail_100`) are relative to the
    DriveThruRPG images base URL (`https://api.drivethrurpg.com/images/`).
    """

    bundle_id: int
    """Bundle ID if this product is part of a bundle, otherwise 0."""

    product_id: int
    """Unique identifier for the product in the DTRPG catalog."""

    image: str | None = None
    """Relative path to the full-size cover image, if available."""

    web_image: str | None = None
    """Relative path to the web-optimized (WebP) cover image, if available."""

    thumbnail: str | None = None
    """Relative path to the 140px cover thumbnail image, if available."""

    thumbnail_100: str | None = None
    """Relative path to the 100px cover thumbnail image, if available."""

    date_created: str | None = None
    """Date and time when the product was added to the DTRPG catalog, if known."""

    description: OrderProductDescription | None = None
    """Descriptive text for the product, if requested."""

    filesize: float | None = None
    """Total file size in megabytes, if known."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductInfo:
        """Decodes an `OrderProductInfo`, including its nested `description`."""
        kwargs = _camel_case_kwargs(data, OrderProductInfo)
        description = data.get("description")
        kwargs["description"] = (
            OrderProductDescription.from_dict(description) if description else None
        )
        return OrderProductInfo(**kwargs)


@dataclass(frozen=True)
class OrderProductOrder:
    """Order summary metadata embedded on an ordered product's attributes."""

    order_id: int
    """The unique identifier of the order."""

    date_created: str | None = None
    """Date and time when the order was created, if known."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductOrder:
        """Decodes an `OrderProductOrder` from its camelCase JSON payload."""
        return from_camel_case_dict(data, OrderProductOrder)


@dataclass(frozen=True)
class OrderProductAttributes:
    """The full attribute set for an ordered product.

    The primary payload within an `OrderProductItem`. Includes required
    fields present on every ordered product as well as optional collections
    (filters, history, attributes) that are populated only when specifically
    requested.
    """

    order_id: int
    """The unique identifier of the order this product belongs to."""

    product_id: int
    """The unique identifier of the product."""

    royalty_publisher_id: int
    """The publisher identifier used for royalty tracking."""

    name: str
    """The display name of the product."""

    final_price: float
    """The final price paid for the product."""

    quantity: int
    """The quantity of this product in the order."""

    bundle_id: int
    """The bundle identifier, if the product was purchased as part of a bundle."""

    archived: int
    """Indicates whether the product has been archived (`1`) or not (`0`)."""

    order_product_id: int
    """The unique identifier for this order-product record."""

    customer_id: int
    """The unique identifier of the customer who owns this order."""

    files: list[OrderProductFile] = field(default_factory=list)
    """The list of downloadable files associated with this ordered product."""

    isbn: str | None = None
    """The ISBN of the product, if applicable."""

    date_purchased: str | None = None
    """The date the product was purchased (ISO 8601 string), if available."""

    filesize: int | None = None
    """The total file size in bytes, if available."""

    add_on_info: str | None = None
    """Additional add-on information associated with this product, if any."""

    file_last_modified: str | None = None
    """The date the product files were last modified (ISO 8601 string), if known."""

    file_last_downloaded: str | None = None
    """The date the product files were last downloaded (ISO 8601 string), if known."""

    filters: list[OrderProductFilter] | None = None
    """Filter categories for this product; populated when `getFilters=1`."""

    history: list[OrderProductHistoryEntry] | None = None
    """The change history for this ordered product, if requested."""

    attributes: list[OrderProductAttribute] | None = None
    """Optional attributes describing purchase options (format, edition, etc.)."""

    publisher: OrderProductPublisher | None = None
    """Publisher metadata embedded directly on this ordered product's attributes."""

    product: OrderProductInfo | None = None
    """Product catalog metadata (cover images, description) on this product."""

    order: OrderProductOrder | None = None
    """Order summary metadata embedded on this ordered product."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductAttributes:
        """Decodes `OrderProductAttributes`, including all nested collections."""
        kwargs = _camel_case_kwargs(data, OrderProductAttributes)
        kwargs["files"] = [
            OrderProductFile.from_dict(f) for f in (data.get("files") or [])
        ]
        filters = data.get("filters")
        kwargs["filters"] = (
            [OrderProductFilter.from_dict(f) for f in filters]
            if filters is not None
            else None
        )
        history = data.get("history")
        kwargs["history"] = (
            [OrderProductHistoryEntry.from_dict(h) for h in history]
            if history is not None
            else None
        )
        attributes = data.get("attributes")
        kwargs["attributes"] = (
            [OrderProductAttribute.from_dict(a) for a in attributes]
            if attributes is not None
            else None
        )
        publisher = data.get("publisher")
        kwargs["publisher"] = (
            OrderProductPublisher.from_dict(publisher) if publisher else None
        )
        product = data.get("product")
        kwargs["product"] = OrderProductInfo.from_dict(product) if product else None
        order = data.get("order")
        kwargs["order"] = OrderProductOrder.from_dict(order) if order else None
        return OrderProductAttributes(**kwargs)


@dataclass(frozen=True)
class RelationshipData:
    """The `type`/`id` pair identifying a resource referenced by a relationship."""

    resource_type: str
    """The referenced resource's type string (e.g., `"Product"`)."""

    id: str
    """The referenced resource's id, matching an `id` in the `included` array."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> RelationshipData:
        """Decodes `RelationshipData`, mapping JSON `type` to `resource_type`."""
        return RelationshipData(resource_type=data["type"], id=data["id"])


@dataclass(frozen=True)
class RelationshipRef:
    """A single JSON:API relationship reference, wrapping the `data` resource id."""

    data: RelationshipData | None = None
    """The referenced resource's type and id, if the relationship is populated."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> RelationshipRef:
        """Decodes a `RelationshipRef`, including its nested `data` reference."""
        inner = data.get("data")
        return RelationshipRef(
            data=RelationshipData.from_dict(inner) if inner else None
        )


@dataclass(frozen=True)
class OrderProductRelationships:
    """JSON:API relationship references carried on an `OrderProductItem`."""

    publisher: RelationshipRef | None = None
    """Reference to the sideloaded `Publisher` resource, if present."""

    product: RelationshipRef | None = None
    """Reference to the sideloaded `Product` resource, if present."""

    order: RelationshipRef | None = None
    """Reference to the sideloaded `Order` resource, if present."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductRelationships:
        """Decodes `OrderProductRelationships` and its nested relationship refs."""
        publisher = data.get("publisher")
        product = data.get("product")
        order = data.get("order")
        return OrderProductRelationships(
            publisher=RelationshipRef.from_dict(publisher) if publisher else None,
            product=RelationshipRef.from_dict(product) if product else None,
            order=RelationshipRef.from_dict(order) if order else None,
        )


@dataclass(frozen=True)
class OrderProductItem:
    """A single item in an ordered products collection response.

    Follows the JSON:API resource object structure with `id`, `type`, and
    `attributes`.

    The live API does *not* embed `publisher`/`product`/`order` metadata
    directly on `attributes` for this endpoint (despite what earlier
    documentation examples showed) -- it references them via
    `relationships`, resolved against the response's top-level `included`
    array. See `OrderProductRelationships` and `IncludedItem`.
    """

    id: str
    """The JSON:API resource identifier."""

    resource_type: str
    """The JSON:API resource type string (e.g., `"order_product"`)."""

    attributes: OrderProductAttributes
    """The full attribute set for this ordered product."""

    relationships: OrderProductRelationships | None = None
    """JSON:API relationship references to sideloaded resources.

    Resolved by matching `id` against the response's `included` array.
    """

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductItem:
        """Decodes an `OrderProductItem`, including nested attributes/relationships."""
        relationships = data.get("relationships")
        return OrderProductItem(
            id=data["id"],
            resource_type=data["type"],
            attributes=OrderProductAttributes.from_dict(data["attributes"]),
            relationships=(
                OrderProductRelationships.from_dict(relationships)
                if relationships
                else None
            ),
        )


# ── Sideloaded resources (`included`) ────────────────────────────────────────


@dataclass(frozen=True)
class PublisherAttributes:
    """Attributes for a publisher resource included alongside ordered products."""

    name: str = ""
    """The display name of the publisher."""

    publisher_id: int = 0
    """The unique identifier of the publisher."""

    slug: str = ""
    """The URL slug for the publisher's storefront page."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PublisherAttributes:
        """Decodes `PublisherAttributes` from its camelCase JSON payload."""
        return from_camel_case_dict(data, PublisherAttributes)


@dataclass(frozen=True)
class PublisherItem:
    """A publisher resource item included in ordered product responses when requested.

    Follows the JSON:API resource object structure.
    """

    id: str
    """The JSON:API resource identifier."""

    resource_type: str
    """The JSON:API resource type string (e.g., `"publisher"`)."""

    attributes: PublisherAttributes
    """The publisher attributes."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> PublisherItem:
        """Decodes a `PublisherItem`, mapping the JSON `type` key to `resource_type`."""
        return PublisherItem(
            id=data["id"],
            resource_type=data["type"],
            attributes=PublisherAttributes.from_dict(data["attributes"]),
        )


@dataclass(frozen=True)
class IncludedItem:
    """A single sideloaded resource entity from an ordered-products response's
    `included` array.

    The `included` array mixes multiple JSON:API resource types
    (`Publisher`, `Product`, `Order`) in a single flat list; `resource_type`
    disambiguates which, and `attributes` is kept as an untyped raw dict
    since its shape depends on `resource_type`. Decode it via
    `IncludedItem.as_publisher` or `IncludedItem.as_product`.
    """

    id: str
    """The JSON:API resource identifier. Matches a `RelationshipData.id`."""

    resource_type: str
    """The JSON:API resource type string (e.g., `"Publisher"`, `"Product"`)."""

    attributes: dict[str, Any]
    """The resource's untyped attribute payload; shape depends on `resource_type`."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> IncludedItem:
        """Decodes an `IncludedItem`, mapping the JSON `type` key to `resource_type`."""
        return IncludedItem(
            id=data["id"],
            resource_type=data["type"],
            attributes=data.get("attributes") or {},
        )

    def as_publisher(self) -> PublisherAttributes | None:
        """Decodes `attributes` as `PublisherAttributes` if the type is `"Publisher"`.

        Returns `None` for any other resource type or if decoding fails.
        """
        if self.resource_type != "Publisher":
            return None
        try:
            return PublisherAttributes.from_dict(self.attributes)
        except (KeyError, TypeError):
            return None

    def as_product(self) -> OrderProductInfo | None:
        """Decodes `attributes` as `OrderProductInfo` if `resource_type == "Product"`.

        Returns `None` for any other resource type or if decoding fails.
        """
        if self.resource_type != "Product":
            return None
        try:
            return OrderProductInfo.from_dict(self.attributes)
        except (KeyError, TypeError):
            return None


# ── Response wrappers ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class OrderProductListResponse:
    """A paginated collection of ordered products.

    Returned by `GET /{api_version}/order_products`.
    """

    links: PaginationLinks
    """Pagination links for navigating the result set."""

    meta: PaginationMeta
    """Pagination metadata describing the current page."""

    data: list[OrderProductItem]
    """The ordered product items on this page."""

    included: list[IncludedItem] | None = None
    """Publisher/Product/Order resources sideloaded alongside the ordered products."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductListResponse:
        """Decodes an `OrderProductListResponse` from its full JSON payload."""
        included = data.get("included")
        return OrderProductListResponse(
            links=PaginationLinks.from_dict(data["links"]),
            meta=PaginationMeta.from_dict(data["meta"]),
            data=[OrderProductItem.from_dict(item) for item in data["data"]],
            included=(
                [IncludedItem.from_dict(item) for item in included]
                if included is not None
                else None
            ),
        )


@dataclass(frozen=True)
class OrderProductItemResponse:
    """A single ordered product resource response.

    Returned by `GET /{api_version}/order_products/{id}`.
    """

    data: OrderProductItem
    """The ordered product item."""

    included: list[IncludedItem] | None = None
    """Publisher/Product/Order resources sideloaded alongside the ordered product.

    Resolved by matching `relationships.*.data.id` against each entry's
    `id` (mirrors `OrderProductListResponse.included`).
    """

    @staticmethod
    def from_dict(data: dict[str, Any]) -> OrderProductItemResponse:
        """Decodes an `OrderProductItemResponse` from its full JSON payload."""
        included = data.get("included")
        return OrderProductItemResponse(
            data=OrderProductItem.from_dict(data["data"]),
            included=(
                [IncludedItem.from_dict(item) for item in included]
                if included is not None
                else None
            ),
        )


# ── Product Lists ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ProductListAttributes:
    """Attributes for a product list resource."""

    customer_id: int
    """The identifier of the customer who owns this list."""

    name: str
    """The display name of the product list."""

    date_created: str
    """The date the list was created (ISO 8601 string)."""

    product_list_id: int
    """The unique identifier for this product list."""

    slug: str
    """The URL slug for this product list."""

    item_count: int
    """The number of items currently in this product list."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProductListAttributes:
        """Decodes `ProductListAttributes` from its camelCase JSON payload."""
        return from_camel_case_dict(data, ProductListAttributes)


@dataclass(frozen=True)
class ProductListItem:
    """A single product list resource item.

    Follows the JSON:API resource object structure.
    """

    id: str
    """The JSON:API resource identifier."""

    resource_type: str
    """The JSON:API resource type string (e.g., `"product_list"`)."""

    attributes: ProductListAttributes
    """The product list attributes."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProductListItem:
        """Decodes a `ProductListItem`, mapping JSON `type` to `resource_type`."""
        return ProductListItem(
            id=data["id"],
            resource_type=data["type"],
            attributes=ProductListAttributes.from_dict(data["attributes"]),
        )


@dataclass(frozen=True)
class ProductListCollectionResponse:
    """A paginated collection of product lists belonging to the authenticated customer.

    Returned by `GET /{api_version}/product_lists`.
    """

    links: PaginationLinks
    """Pagination links for navigating the result set."""

    meta: PaginationMeta
    """Pagination metadata describing the current page."""

    data: list[ProductListItem]
    """The product list items on this page."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProductListCollectionResponse:
        """Decodes a `ProductListCollectionResponse` from its full JSON payload."""
        return ProductListCollectionResponse(
            links=PaginationLinks.from_dict(data["links"]),
            meta=PaginationMeta.from_dict(data["meta"]),
            data=[ProductListItem.from_dict(item) for item in data["data"]],
        )


@dataclass(frozen=True)
class ProductListItemsResponse:
    """A paginated collection of items within a specific product list.

    Returned by `GET /{api_version}/product_list_items`. Individual item
    schemas are not yet formally defined by the API contract, so items are
    represented as raw dicts until the schema matures.
    """

    links: PaginationLinks
    """Pagination links for navigating the result set."""

    meta: PaginationMeta
    """Pagination metadata describing the current page."""

    data: list[dict[str, Any]]
    """The raw product list item data on this page."""

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProductListItemsResponse:
        """Decodes a `ProductListItemsResponse` from its full JSON payload."""
        return ProductListItemsResponse(
            links=PaginationLinks.from_dict(data["links"]),
            meta=PaginationMeta.from_dict(data["meta"]),
            data=list(data["data"]),
        )


@dataclass(frozen=True)
class ProductListItemCreateRequest:
    """Request body for adding a product to a product list.

    Sent by `POST /{api_version}/product_list_items`.
    """

    product_id: int
    """Unique identifier of the product to add."""

    product_list_id: int
    """Unique identifier of the product list to add the product to."""

    def to_wire_dict(self) -> dict[str, Any]:
        """Serializes this request to its camelCase wire-format JSON body."""
        return {"productId": self.product_id, "productListId": self.product_list_id}


@dataclass(frozen=True)
class ProductListItemCreateResponse:
    """The created product list item.

    Returned by `POST /{api_version}/product_list_items`. The API wraps
    this resource in a JSON:API-style envelope on the wire (`{"data":
    {"id": ..., "type": ..., "attributes": {"productId": ...,
    "productListId": ..., "productListItemId": ...}}}`); `from_dict`
    unwraps that envelope so callers work with a flat object.
    """

    product_id: int
    """Unique identifier of the product added to the list."""

    product_list_id: int
    """Unique identifier of the product list the product was added to."""

    product_list_item_id: int
    """Unique identifier assigned to this product list item.

    Required to remove the item later via
    `DELETE /{api_version}/product_list_items/{id}`.
    """

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ProductListItemCreateResponse:
        """Decodes a `ProductListItemCreateResponse`, unwrapping the envelope."""
        attributes = data["data"]["attributes"]
        return ProductListItemCreateResponse(
            product_id=attributes["productId"],
            product_list_id=attributes["productListId"],
            product_list_item_id=attributes["productListItemId"],
        )


# ── Query parameter structs ───────────────────────────────────────────────────


@dataclass
class LibraryItemsParams:
    """Query parameters for the `GET /order_products` (library items) endpoint.

    All fields are optional. Set a field to a value to include the
    corresponding query parameter in the request. Use the default
    constructor to start with no filters applied.

    Examples:
        >>> params = LibraryItemsParams(page=2, page_size=50, get_filters=True)
    """

    page: int | None = None
    """The page number to retrieve (1-based)."""

    page_size: int | None = None
    """The number of items to return per page."""

    get_checksum: bool | None = None
    """When `True`, includes checksum data for each product file (`getChecksum=1`)."""

    get_filters: bool | None = None
    """When `True`, includes filter category data for each product (`getFilters=1`)."""

    library: bool | None = None
    """When `True`, restricts results to library (non-archived) products."""

    archived: bool | None = None
    """When `True`, includes archived products; excludes them when `False`."""

    updated_date_after: str | None = None
    """ISO 8601 date string. When set, returns only products updated after this date
    (`updatedDate[after]=...`).
    """


@dataclass
class PageParams:
    """Query parameters for paginated collection endpoints such as `/product_lists`.

    All fields are optional. Use the default constructor to retrieve the
    first page with the server's default page size.

    Examples:
        >>> params = PageParams(page=3, page_size=25)
    """

    page: int | None = None
    """The page number to retrieve (1-based)."""

    page_size: int | None = None
    """The number of items to return per page."""
