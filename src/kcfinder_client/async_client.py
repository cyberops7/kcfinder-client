"""Async client for KCFinder file manager operations."""

from types import TracebackType

import httpx

from kcfinder_client._core import (
    build_action_url,
    build_form_data,
    build_headers,
    parse_file_list,
)
from kcfinder_client.auth import BaseAuth
from kcfinder_client.models import FileInfo


class AsyncKCFinderClient:
    """Async client for KCFinder file manager operations."""

    def __init__(
        self,
        browse_url: str,
        auth: BaseAuth,
        file_type: str = "images",
    ) -> None:
        self._browse_url = browse_url
        self._auth = auth
        self._file_type = file_type
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> AsyncKCFinderClient:
        self._client = httpx.AsyncClient()
        await self._auth.authenticate(self._client)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            await self._client.aclose()

    def _get_client(self) -> httpx.AsyncClient:
        """Return the active HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError(
                "Client not initialized. Use 'async with' context manager."
            )
        return self._client

    async def _post(self, action: str, data: dict) -> httpx.Response:
        """Send a POST request to KCFinder."""
        url = build_action_url(self._browse_url, action, self._file_type)
        headers = build_headers(self._auth.get_referer())
        return await self._get_client().post(url, data=data, headers=headers)

    async def list_files(self, dir: str) -> list[FileInfo]:
        """List files in a directory."""
        data = build_form_data(dir=dir)
        response = await self._post("chDir", data)
        return parse_file_list(response.json())
