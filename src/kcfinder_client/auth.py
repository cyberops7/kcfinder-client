import json
from abc import ABC, abstractmethod
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


class HarmonySiteAuth(BaseAuth):
    """Auth for HarmonySite's KCFinder fork.

    Authenticates in two steps:
    1. POST to login_url with credentials to establish a web session
    2. GET browse_url with bros_config and brosseccheck to init the KCFinder session
    """

    def __init__(
        self,
        login_url: str,
        browse_url: str,
        username: str,
        password: str,
        bros_config: dict,
        brosseccheck: str = "Xx-ok-xX",
    ) -> None:
        self._login_url = login_url
        self._browse_url = browse_url
        self._username = username
        self._password = password
        self._bros_config = bros_config
        self._brosseccheck = brosseccheck

    async def authenticate(self, session: httpx.AsyncClient) -> None:
        login_resp = await session.post(
            self._login_url,
            data={"username": self._username, "password": self._password},
        )
        if login_resp.status_code != 200:
            raise AuthError(f"Login failed with status {login_resp.status_code}")

        init_resp = await session.get(self._init_url())
        if init_resp.status_code != 200:
            raise AuthError(
                f"KCFinder session init failed with status {init_resp.status_code}"
            )

    def authenticate_sync(self, session: httpx.Client) -> None:
        login_resp = session.post(
            self._login_url,
            data={"username": self._username, "password": self._password},
        )
        if login_resp.status_code != 200:
            raise AuthError(f"Login failed with status {login_resp.status_code}")

        init_resp = session.get(self._init_url())
        if init_resp.status_code != 200:
            raise AuthError(
                f"KCFinder session init failed with status {init_resp.status_code}"
            )

    def get_referer(self) -> str:
        return self._init_url()

    def _init_url(self) -> str:
        params = urlencode(
            {
                "bros_config": json.dumps(self._bros_config),
                "brosseccheck": self._brosseccheck,
            }
        )
        return f"{self._browse_url}?{params}"
