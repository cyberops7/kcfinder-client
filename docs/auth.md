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

For HarmonySite's KCFinder fork. Authenticates in three steps:

1. POST to the HarmonySite login URL to establish a web session
2. GET a HarmonySite admin page (by default the new-page form,
   `dbpage.php?pg=form&dbase=pages`) and read the signed `bros_config` and
   `bros_sig` from the KCFinder links that HarmonySite embeds in it
3. GET the KCFinder browse URL with those params to initialize the KCFinder
   session, and raise `AuthError` if KCFinder refuses it

The signed params are also sent as query parameters on every subsequent
KCFinder request.

```python
from kcfinder_client import HarmonySiteAuth

auth = HarmonySiteAuth(
    login_url="https://example.harmonysong.com/dbaction.php",
    browse_url="https://example.harmonysong.com/brostools/jquery/kcfinder/browse.php",
    username="admin",
    password="secret",
)
```

#### Constructor Parameters

| Parameter         | Type          | Required | Description                                                 |
|-------------------|---------------|----------|-------------------------------------------------------------|
| `login_url`       | `str`         | Yes      | The HarmonySite `dbaction.php` login endpoint               |
| `browse_url`      | `str`         | Yes      | The KCFinder `browse.php` URL                               |
| `username`        | `str`         | Yes      | HarmonySite login username                                  |
| `password`        | `str`         | Yes      | HarmonySite login password                                  |
| `config_page_url` | `str \| None` | No       | Page to read the signed params from (default: see above)    |
| `bros_config`     | `str \| None` | No       | Legacy PHP-serialized config, used only as a fallback       |
| `brosseccheck`    | `str`         | No       | Legacy security token; default is `"Xx-ok-xX"`              |

#### Signed params expire

HarmonySite's signed `bros_config` is base64-encoded JSON carrying an `exp`
timestamp, and `bros_sig` is an HMAC over it. They expire about an hour after
they are issued. `auth.expires_at` returns the expiry as a UTC `datetime`
after authentication (or `None` when the legacy params are in use). Open a new
client, which authenticates again, for each job rather than holding one open
for hours.

<details>
<summary><strong>Legacy bros_config fallback</strong></summary>

Before November 2026, HarmonySite accepted a fixed PHP-serialized
`bros_config` plus `brosseccheck=Xx-ok-xX`. HarmonySite now refuses those.
They are still accepted as constructor arguments, and used only when the
config page embeds no signed KCFinder URL:

```
a:3:{s:9:"uploadDir";s:6:"files/";s:9:"thumbsDir";s:14:"files/.thumbs/";s:9:"uploadURL";s:0:"";}
```

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

| Variable                | Description                                          |
|-------------------------|------------------------------------------------------|
| `KCFINDER_LOGIN_URL`    | The HarmonySite login URL (`dbaction.php`)           |
| `KCFINDER_BROWSE_URL`   | The KCFinder `browse.php` URL                        |
| `KCFINDER_USERNAME`     | Login username                                       |
| `KCFINDER_PASSWORD`     | Login password                                       |

### Optional Variables

| Variable                   | Default                                | Description                          |
|----------------------------|----------------------------------------|--------------------------------------|
| `KCFINDER_CONFIG_PAGE_URL` | `<site>/dbpage.php?pg=form&dbase=pages` | Page to read the signed params from |
| `KCFINDER_BROS_CONFIG`     | none                                   | Legacy fallback `bros_config`        |
| `KCFINDER_BROSSECCHECK`    | `"Xx-ok-xX"`                           | Legacy fallback security token       |

<details>
<summary><strong>Example .env file</strong></summary>

```bash
KCFINDER_LOGIN_URL=https://example.harmonysong.com/dbaction.php
KCFINDER_BROWSE_URL=https://example.harmonysong.com/kcfinder/browse.php
KCFINDER_USERNAME=admin
KCFINDER_PASSWORD=secret
```

</details>

## Custom Auth

To support a different authentication scheme, subclass `BaseAuth` and
implement its methods:

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

    def get_query_params(self) -> dict[str, str]:
        # Return extra query params to include on every request URL.
        # Override this if your KCFinder fork requires additional
        # params beyond act and type. Default returns empty dict.
        return {}
```

---

See also: [File Operations](files.md) for getting started after auth
