"""Sync client for KCFinder file manager operations."""

from pathlib import Path
from types import TracebackType

import httpx

from kcfinder_client._core import (
    build_action_url,
    build_form_data,
    build_headers,
    check_action_error,
    check_upload_response,
    parse_dir_tree,
    parse_file_list,
)
from kcfinder_client.auth import BaseAuth
from kcfinder_client.models import DirTree, FileInfo


class KCFinderClient:
    """Sync client for KCFinder file manager operations."""

    def __init__(
        self,
        browse_url: str,
        auth: BaseAuth,
        file_type: str = "images",
    ) -> None:
        self._browse_url = browse_url
        self._auth = auth
        self._file_type = file_type
        self._client: httpx.Client | None = None

    def __enter__(self) -> KCFinderClient:
        self._client = httpx.Client()
        self._auth.authenticate_sync(self._client)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self._client:
            self._client.close()

    def _get_client(self) -> httpx.Client:
        """Return the active HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'with' context manager.")
        return self._client

    def _post(self, action: str, data: dict) -> httpx.Response:
        """Send a POST request to KCFinder."""
        url = build_action_url(self._browse_url, action, self._file_type)
        headers = build_headers(self._auth.get_referer())
        return self._get_client().post(url, data=data, headers=headers)

    def list_files(self, dir: str) -> list[FileInfo]:
        """List files in a directory."""
        data = build_form_data(dir=dir)
        response = self._post("chDir", data)
        return parse_file_list(response.json())

    def upload(self, dir: str, files: Path | list[Path]) -> None:
        """Upload one or more files to a directory."""
        if isinstance(files, Path):
            files = [files]
        url = build_action_url(
            self._browse_url, "upload", self._file_type
        )
        url += f"&dir={dir}"
        headers = build_headers(self._auth.get_referer())
        upload_files = [
            ("upload[]", (f.name, f.read_bytes())) for f in files
        ]
        response = self._get_client().post(
            url,
            files=upload_files,
            headers=headers,
        )
        check_upload_response(response.text)

    def delete(self, dir: str, file: str) -> None:
        """Delete a file."""
        data = build_form_data(dir=dir, file=file)
        response = self._post("delete", data)
        check_action_error("delete", response.text)

    def rename(self, dir: str, file: str, new_name: str) -> None:
        """Rename a file."""
        data = build_form_data(dir=dir, file=file, new_name=new_name)
        response = self._post("rename", data)
        check_action_error("rename", response.text)

    def download(self, dir: str, file: str) -> bytes:
        """Download a file and return its content as bytes."""
        data = build_form_data(dir=dir, file=file)
        response = self._post("download", data)
        return response.content

    def get_thumbnail(self, dir: str, file: str) -> bytes:
        """Get the thumbnail for a file as PNG bytes."""
        data = build_form_data(dir=dir, file=file)
        response = self._post("thumb", data)
        return response.content

    def get_tree(self) -> DirTree:
        """Get the full directory tree."""
        url = build_action_url(self._browse_url, "init", self._file_type)
        headers = build_headers(self._auth.get_referer())
        response = self._get_client().post(url, headers=headers)
        return parse_dir_tree(response.json())

    def expand(self, dir: str) -> list[str]:
        """Get subdirectory names within a directory."""
        data = build_form_data(dir=dir)
        response = self._post("expand", data)
        return response.json().get("dirs", [])

    def create_dir(self, dir: str, new_dir: str) -> None:
        """Create a new subdirectory."""
        data = build_form_data(dir=dir, new_dir=new_dir)
        response = self._post("newDir", data)
        check_action_error("newDir", response.text)

    def rename_dir(self, dir: str, new_name: str) -> None:
        """Rename a directory."""
        data = build_form_data(dir=dir, new_name=new_name)
        response = self._post("renameDir", data)
        body = response.json()
        if "error" in body:
            check_action_error("renameDir", body)

    def delete_dir(self, dir: str) -> None:
        """Delete a directory recursively."""
        data = build_form_data(dir=dir)
        response = self._post("deleteDir", data)
        check_action_error("deleteDir", response.text)

    def download_dir(self, dir: str) -> bytes:
        """Download a directory as a ZIP archive."""
        data = build_form_data(dir=dir)
        response = self._post("downloadDir", data)
        return response.content

    def _bulk_action(
        self, action: str, files: list[str], dest: str | None = None
    ) -> None:
        """Shared logic for bulk copy/move/delete actions."""
        data = build_form_data(files=files)
        if dest is not None:
            data["dir"] = dest
        response = self._post(action, data)
        body = response.text.strip()
        if body.lower() != "true":
            check_action_error(action, response.json())

    def copy(self, files: list[str], dest: str) -> None:
        """Copy files to a destination directory."""
        self._bulk_action("cp_cbd", files, dest)

    def move(self, files: list[str], dest: str) -> None:
        """Move files to a destination directory."""
        self._bulk_action("mv_cbd", files, dest)

    def bulk_delete(self, files: list[str]) -> None:
        """Delete multiple files."""
        self._bulk_action("rm_cbd", files)

    def download_selected(self, dir: str, files: list[str]) -> bytes:
        """Download selected files as a ZIP archive."""
        data = build_form_data(dir=dir, files=files)
        response = self._post("downloadSelected", data)
        return response.content
