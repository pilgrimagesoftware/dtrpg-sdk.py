---
title: Quick start
version: latest
slug: quickstart
---

# Quick start

Configure the SDK with your application key, exchange it for a session
token, and fetch the authenticated user's library.

```python
from dtrpg_sdk import Config, DriveThruRpgSdk, LibraryItemsParams
from dtrpg_sdk.auth import key_exchange

config = Config(application_key="my-app-key")
sdk = DriveThruRpgSdk.with_config(config)

# Exchange the application key for a session token.
token_response = key_exchange.authenticate("my-app-key", config)
sdk.apply_auth_response(token_response)

# Build an authenticated library client and fetch the user's library.
client = sdk.library_client()
products = client.list_order_products(LibraryItemsParams(page=1, page_size=25))
for item in products.data:
    print(item.attributes.name)
```

See [Authentication]({{ '/latest/auth/' | relative_url }}) for the
credential-login flow (email/password instead of an existing application
key), and [Library client]({{ '/latest/library/' | relative_url }}) for the
rest of the available endpoints.
