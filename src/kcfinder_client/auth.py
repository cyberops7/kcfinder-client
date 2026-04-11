from abc import ABC, abstractmethod

import httpx


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
