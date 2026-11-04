import base64
import binascii
import html
import json
import os
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from urllib.parse import urlencode

import httpx

from kcfinder_client.exceptions import AuthError


class BaseAuth(ABC):
    """Base class for KCFinder authentication strategies."""

    @abstractmethod
    async def authenticate(self, session: httpx.AsyncClient) -> None:
        """Authenticate an async HTTP session."""

    @abstractmethod
    def authenticate_sync(self, session: httpx.Client) -> None:
        """Authenticate a sync HTTP session."""

    @abstractmethod
    def get_referer(self) -> str:
        """Return the Referer URL required for KCFinder requests."""

    def get_query_params(self) -> dict[str, str]:
        """Return extra query params to include on every KCFinder request.

        The HarmonySite fork requires ``bros_config`` and ``brosseccheck``
        on every request URL, not just the session init.  Standard KCFinder
        installs return an empty dict.
        """
        return {}


class SessionAuth(BaseAuth):
    """Auth for standard KCFinder installs with a pre-established session.

    Use this when you already have a valid PHPSESSID cookie value.
    """

    def __init__(self, session_id: str, referer: str) -> None:
        self._session_id = session_id
        self._referer = referer

    async def authenticate(self, session: httpx.AsyncClient) -> None:
        session.cookies.set("PHPSESSID", self._session_id)

    def authenticate_sync(self, session: httpx.Client) -> None:
        session.cookies.set("PHPSESSID", self._session_id)

    def get_referer(self) -> str:
        return self._referer


_SIGNED_URL_PATTERN = re.compile(
    r"kcfinder/browse\.php\?[^\"'\s]*?bros_config=([A-Za-z0-9+/=_%-]+)"
    r"&bros_sig=([0-9a-fA-F]+)"
)

# The refusal page JS-escapes the apostrophe ("don\'t"), so match after it.
_REFUSED_MARKER = "have permissions to browse"


def parse_signed_bros_params(page_html: str) -> dict[str, str] | None:
    """Find the signed KCFinder params embedded in a HarmonySite page.

    HarmonySite's editor opens KCFinder with ``bros_config`` (base64 JSON
    with an expiry) and ``bros_sig`` (an HMAC over it). Returns both as
    query params, or None when the page embeds no KCFinder URL.
    """
    match = _SIGNED_URL_PATTERN.search(html.unescape(page_html))
    if match is None:
        return None
    return {"bros_config": match.group(1), "bros_sig": match.group(2)}


def _decode_expiry(bros_config: str) -> datetime | None:
    """Return the expiry encoded in a signed bros_config, if it has one."""
    try:
        padded = bros_config + "=" * (-len(bros_config) % 4)
        exp = json.loads(base64.b64decode(padded)).get("exp")
    except (binascii.Error, UnicodeDecodeError, ValueError, AttributeError):
        return None
    if not isinstance(exp, int | float):
        return None
    return datetime.fromtimestamp(exp, tz=UTC)


class HarmonySiteAuth(BaseAuth):
    """Auth for HarmonySite's KCFinder fork.

    Authenticates in three steps:
    1. POST to login_url with credentials to establish a web session
    2. GET config_page_url and read the signed ``bros_config``/``bros_sig``
       that HarmonySite embeds in its KCFinder links
    3. GET browse_url with those params to init the KCFinder session

    If the config page embeds no signed KCFinder URL, the legacy
    ``bros_config``/``brosseccheck`` params are used instead, when given.
    Signed params expire (see ``expires_at``), so authenticate again for
    each long-running job.
    """

    def __init__(
        self,
        login_url: str,
        browse_url: str,
        username: str,
        password: str,
        bros_config: str | None = None,
        brosseccheck: str = "Xx-ok-xX",
        config_page_url: str | None = None,
    ) -> None:
        self._login_url = login_url
        self._browse_url = browse_url
        self._username = username
        self._password = password
        self._bros_config = bros_config
        self._brosseccheck = brosseccheck
        self._config_page_url = config_page_url or (
            f"{login_url.rsplit('/', 1)[0]}/dbpage.php?pg=form&dbase=pages"
        )
        self._signed_params: dict[str, str] | None = None

    @property
    def expires_at(self) -> datetime | None:
        """When the signed params stop being accepted, or None if unknown."""
        if self._signed_params is None:
            return None
        return _decode_expiry(self._signed_params["bros_config"])

    def _login_data(self) -> dict[str, str]:
        """Build the HarmonySite login form payload."""
        return {
            "dbase": "users",
            "action": "login",
            "username": self._username,
            "password": self._password,
            "nextpage": self._login_url.rsplit("/", 1)[0],
            "login": "Log In",
            "remember": "1",
        }

    def _login_succeeded(self, session_cookies: httpx.Cookies) -> bool:
        """Check whether the HarmonySite login actually succeeded.

        HarmonySite returns HTTP 200 even on bad credentials. A successful
        login sets additional cookies (e.g. ``fakelevel``) beyond
        ``PHPSESSID``; a failed login only sets ``PHPSESSID``.
        """
        return len(session_cookies) > 1

    def _check_login(
        self, login_resp: httpx.Response, session_cookies: httpx.Cookies
    ) -> None:
        if login_resp.status_code != 200:
            raise AuthError(f"Login failed with status {login_resp.status_code}")
        if not self._login_succeeded(session_cookies):
            raise AuthError("Login failed: invalid credentials")

    def _use_config_page(self, config_resp: httpx.Response) -> None:
        """Adopt the signed params from the config page, or fall back to legacy."""
        signed = None
        if config_resp.status_code == 200:
            signed = parse_signed_bros_params(config_resp.text)
        if signed is None and self._bros_config is None:
            raise AuthError(
                "Could not find signed KCFinder params on "
                f"{self._config_page_url}, and no legacy bros_config was given"
            )
        self._signed_params = signed

    def _check_init(self, init_resp: httpx.Response) -> None:
        if init_resp.status_code != 200:
            raise AuthError(
                f"KCFinder session init failed with status {init_resp.status_code}"
            )
        if _REFUSED_MARKER in init_resp.text:
            raise AuthError("KCFinder refused the session: no permission to browse")

    async def authenticate(self, session: httpx.AsyncClient) -> None:
        login_resp = await session.post(
            self._login_url,
            data=self._login_data(),
            follow_redirects=True,
        )
        self._check_login(login_resp, session.cookies)
        self._use_config_page(await session.get(self._config_page_url))
        self._check_init(await session.get(self._init_url()))

    def authenticate_sync(self, session: httpx.Client) -> None:
        login_resp = session.post(
            self._login_url,
            data=self._login_data(),
            follow_redirects=True,
        )
        self._check_login(login_resp, session.cookies)
        self._use_config_page(session.get(self._config_page_url))
        self._check_init(session.get(self._init_url()))

    def get_referer(self) -> str:
        return self._init_url()

    def get_query_params(self) -> dict[str, str]:
        if self._signed_params is not None:
            return dict(self._signed_params)
        if self._bros_config is None:
            return {}
        return {
            "bros_config": self._bros_config,
            "brosseccheck": self._brosseccheck,
        }

    def _init_url(self) -> str:
        params = self.get_query_params()
        if not params:
            return self._browse_url
        return f"{self._browse_url}?{urlencode(params)}"


def harmonysite_auth_from_env() -> HarmonySiteAuth:
    """Build a HarmonySiteAuth from environment variables.

    Required env vars:
        KCFINDER_LOGIN_URL: The HarmonySite login URL
        KCFINDER_BROWSE_URL: The KCFinder browse.php URL
        KCFINDER_USERNAME: Login username
        KCFINDER_PASSWORD: Login password

    Optional env vars:
        KCFINDER_BROS_CONFIG: Legacy PHP-serialized bros_config, used only
            when the site embeds no signed KCFinder params
        KCFINDER_BROSSECCHECK: Legacy security check token (default: "Xx-ok-xX")
        KCFINDER_CONFIG_PAGE_URL: Page to read the signed params from
            (default: <site>/dbpage.php?pg=form&dbase=pages)
    """
    return HarmonySiteAuth(
        login_url=os.environ["KCFINDER_LOGIN_URL"],
        browse_url=os.environ["KCFINDER_BROWSE_URL"],
        username=os.environ["KCFINDER_USERNAME"],
        password=os.environ["KCFINDER_PASSWORD"],
        bros_config=os.environ.get("KCFINDER_BROS_CONFIG") or None,
        brosseccheck=os.environ.get("KCFINDER_BROSSECCHECK", "Xx-ok-xX"),
        config_page_url=os.environ.get("KCFINDER_CONFIG_PAGE_URL") or None,
    )
