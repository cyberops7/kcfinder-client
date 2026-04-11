"""Async client for KCFinder file manager operations."""

from pathlib import Path
from types import TracebackType

import httpx

from kcfinder_client._core import (
    build_action_url,
    build_form_data,
    build_headers,
    check_action_error,
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

    async def upload(self, dir: str, files: Path | list[Path]) -> None:
        """Upload one or more files to a directory."""
        if isinstance(files, Path):
            files = [files]
        url = build_action_url(self._browse_url, "upload", self._file_type)
        headers = build_headers(self._auth.get_referer())
        upload_files = [("upload[]", (f.name, f.read_bytes())) for f in files]
        response = await self._get_client().post(
            url,
            data={"dir": dir},
            files=upload_files,
            headers=headers,
        )
        text = response.text.strip()
        if text:
            check_action_error("upload", text)

    async def delete(self, dir: str, file: str) -> None:
        """Delete a file."""
        data = build_form_data(dir=dir, file=file)
        response = await self._post("delete", data)
        check_action_error("delete", response.text)

    async def rename(self, dir: str, file: str, new_name: str) -> None:
        """Rename a file."""
        data = build_form_data(dir=dir, file=file, new_name=new_name)
        response = await self._post("rename", data)
        check_action_error("rename", response.text)

    async def download(self, dir: str, file: str) -> bytes:
        """Download a file and return its content as bytes."""
        data = build_form_data(dir=dir, file=file)
        response = await self._post("download", data)
        return response.content

    async def get_thumbnail(self, dir: str, file: str) -> bytes:
        """Get the thumbnail for a file as PNG bytes."""
        data = build_form_data(dir=dir, file=file)
        response = await self._post("thumb", data)
        return response.content
