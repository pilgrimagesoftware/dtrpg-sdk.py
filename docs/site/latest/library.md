---
title: Library client
version: latest
slug: library
---

# Library client

`LibraryClient` is a synchronous, authenticated HTTP client for the
DriveThruRPG API's library endpoints. Create one from an authenticated SDK
instance rather than constructing it directly, so configuration and session
state are validated first:

```python
client = sdk.library_client()
```

## Ordered products

```python
from dtrpg_sdk import LibraryItemsParams

# List the user's ordered products, paginated.
products = client.list_order_products(LibraryItemsParams(page=1, page_size=25))
for item in products.data:
    print(item.attributes.name)

# Fetch a single ordered product by id.
product = client.get_order_product(order_product_id=12345)

# Prepare a download for one of its files (index matches OrderProductFile.index).
download = client.prepare_download(order_product_id=12345, index=0)
```

## Product lists

```python
from dtrpg_sdk import PageParams

# List the user's product lists.
lists = client.list_product_lists(PageParams(page=1, page_size=25))

# Create a new product list.
new_list = client.create_product_list("Favorites")

# List items within a product list.
items = client.list_product_list_items(new_list.id, PageParams(page=1, page_size=25))

# Add a product to a product list.
client.add_product_list_item(product_list_id=new_list.id, product_id=67890)

# Remove a product list item by its own id (not the product's id).
client.delete_product_list_item(product_list_item_id=items.data[0].id)

# Delete a product list.
client.delete_product_list(new_list.id)
```

Every method raises `HttpError` on transport failure, `ApiError` on a
non-success HTTP status, and `DecodeFailedError` if a success response
can't be decoded -- see [Error handling]({{ '/latest/errors/' | relative_url }}).
