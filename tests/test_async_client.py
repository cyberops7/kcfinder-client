import pytest

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.models import FileInfo
from tests.conftest import BROWSE_URL


@pytest.mark.asyncio
async def test_async_client_context_manager(session_auth):
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        assert client is not None


@pytest.mark.asyncio
async def test_list_files(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "photo.jpg",
                    "size": 1024,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
                {
                    "name": "doc.pdf",
                    "size": 2048,
                    "mtime": 1704153600,
                    "readable": True,
                    "writable": False,
                },
            ],
            "writable": True,
        },
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        files = await client.list_files("2026Program")
    assert len(files) == 2
    assert isinstance(files[0], FileInfo)
    assert files[0].name == "photo.jpg"


@pytest.mark.asyncio
async def test_list_files_empty_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "writable": True},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        files = await client.list_files("empty-dir")
    assert files == []
