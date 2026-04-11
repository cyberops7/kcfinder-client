# Auth

## Table of Contents

- [Strategies](#strategies)
   - [HarmonySiteAuth](#harmonysiteauth)
   - [SessionAuth](#sessionauth)
- [Environment Variables](#environment-variables)
- [Custom Auth](#custom-auth)

---

kcfinder-client uses a pluggable auth strategy pattern. You pick the right
strategy for your KCFinder installation, configure it once, and pass it to
the client.

## Strategies

### HarmonySiteAuth

For HarmonySite's KCFinder fork. Authenticates in two steps:

1. POST to the HarmonySite login URL to establish a web session
2. GET the KCFinder browse URL with `bros_config` and `brosseccheck` query
   params to initialize the KCFinder session

```python
from kcfinder_client import HarmonySiteAuth

auth = HarmonySiteAuth(
    login_url="https://example.harmonysong.com/dbaction.php",
    browse_url="https://example.harmonysong.com/kcfinder/browse.php",
    username="admin",
    password="secret",
    bros_config={
        "uploadDir": "files/",
        "thumbsDir": "files/.thumbs/",
        "uploadURL": "https://example.harmonysong.com/files/",
    },
    brosseccheck="Xx-ok-xX",  # optional, default is "Xx-ok-xX"
)
```

#### Constructor Parameters

| Parameter      | Type   | Required | Description                                    |
|----------------|--------|----------|------------------------------------------------|
| `login_url`    | `str`  | Yes      | The HarmonySite `dbaction.php` login endpoint  |
| `browse_url`   | `str`  | Yes      | The KCFinder `browse.php` URL                  |
| `username`     | `str`  | Yes      | HarmonySite login username                     |
| `password`     | `str`  | Yes      | HarmonySite login password                     |
| `bros_config`  | `dict` | Yes      | KCFinder configuration dictionary (see below)  |
| `brosseccheck` | `str`  | No       | Security token; default is `"Xx-ok-xX"`        |

<details>
<summary><strong>bros_config reference</strong></summary>

The `bros_config` dict is deserialized by HarmonySite's KCFinder fork to
configure the file manager session. At minimum it should contain:

```json
{
    "uploadDir": "files/",
    "thumbsDir": "files/.thumbs/",
    "uploadURL": "https://example.harmonysong.com/files/"
}
```

| Key          | Description                                        |
|--------------|----------------------------------------------------|
| `uploadDir`  | Server-relative path to the root upload directory  |
| `thumbsDir`  | Server-relative path to the thumbnails directory   |
| `uploadURL`  | Public URL prefix for uploaded files               |

The dict is JSON-encoded and passed as a query parameter on the initial
`browse.php` GET request.

</details>

### SessionAuth

For standard KCFinder installations where you already have a valid `PHPSESSID`
cookie. Use this when KCFinder's session is established by some other
mechanism.

```python
from kcfinder_client import SessionAuth

auth = SessionAuth(
    session_id="abc123yoursessionid",
    referer="https://example.com/kcfinder/browse.php",
)
```

| Parameter    | Type  | Description                                         |
|--------------|-------|-----------------------------------------------------|
| `session_id` | `str` | Value of the `PHPSESSID` cookie                     |
| `referer`    | `str` | The full browse URL (used as the `Referer` header)  |

## Environment Variables

Use `harmonysite_auth_from_env()` to load HarmonySiteAuth configuration from
environment variables. This keeps credentials out of source code.

> [!TIP]
> Never hardcode credentials in source files. Load them from environment
> variables or a secret manager, and use `harmonysite_auth_from_env()` for
> the simplest integration.

```python
from kcfinder_client import harmonysite_auth_from_env

auth = harmonysite_auth_from_env()
```

### Required Variables

| Variable                | Description                                  |
|-------------------------|----------------------------------------------|
| `KCFINDER_LOGIN_URL`    | The HarmonySite login URL (`dbaction.php`)   |
| `KCFINDER_BROWSE_URL`   | The KCFinder `browse.php` URL                |
| `KCFINDER_USERNAME`     | Login username                               |
| `KCFINDER_PASSWORD`     | Login password                               |
| `KCFINDER_BROS_CONFIG`  | JSON string of the `bros_config` dict        |

### Optional Variables

| Variable                  | Default        | Description            |
|---------------------------|----------------|------------------------|
| `KCFINDER_BROSSECCHECK`   | `"Xx-ok-xX"`  | Security check token   |

<details>
<summary><strong>Example .env file</strong></summary>

```bash
KCFINDER_LOGIN_URL=https://example.harmonysong.com/dbaction.php
KCFINDER_BROWSE_URL=https://example.harmonysong.com/kcfinder/browse.php
KCFINDER_USERNAME=admin
KCFINDER_PASSWORD=secret
KCFINDER_BROS_CONFIG={"uploadDir":"files/","thumbsDir":"files/.thumbs/","uploadURL":"https://example.harmonysong.com/files/"}
```

</details>

## Custom Auth

To support a different authentication scheme, subclass `BaseAuth` and
implement its three methods:

```python
from kcfinder_client import BaseAuth
import httpx

class MyCustomAuth(BaseAuth):
    async def authenticate(self, session: httpx.AsyncClient) -> None:
        # Set up cookies or headers on the async session
        session.cookies.set("my_session", "value")

    def authenticate_sync(self, session: httpx.Client) -> None:
        # Same thing for the sync client
        session.cookies.set("my_session", "value")

    def get_referer(self) -> str:
        # Return the URL to use as the Referer header
        return "https://example.com/kcfinder/browse.php"
```

---

See also: [File Operations](files.md) for getting started after auth
