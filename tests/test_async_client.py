import pytest

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.exceptions import ActionError
from kcfinder_client.models import DirTree, FileInfo
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


@pytest.mark.asyncio
async def test_upload_single_file(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images",
        text="",
    )
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.upload("2026Program", test_file)


@pytest.mark.asyncio
async def test_upload_multiple_files(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images",
        text="",
    )
    file_a = tmp_path / "a.jpg"
    file_b = tmp_path / "b.jpg"
    file_a.write_bytes(b"data a")
    file_b.write_bytes(b"data b")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.upload("2026Program", [file_a, file_b])


@pytest.mark.asyncio
async def test_delete(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=delete&type=images",
        text="true",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.delete("2026Program", "old.jpg")


@pytest.mark.asyncio
async def test_delete_error(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=delete&type=images",
        text="File not found",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        with pytest.raises(ActionError, match="File not found"):
            await client.delete("2026Program", "missing.jpg")


@pytest.mark.asyncio
async def test_rename(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=rename&type=images",
        text="true",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.rename("2026Program", "old.jpg", "new.jpg")


@pytest.mark.asyncio
async def test_download(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=download&type=images",
        content=b"binary file content",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        content = await client.download("2026Program", "photo.jpg")
    assert content == b"binary file content"


@pytest.mark.asyncio
async def test_get_thumbnail(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=thumb&type=images",
        content=b"png data",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        thumb = await client.get_thumbnail("2026Program", "photo.jpg")
    assert thumb == b"png data"


@pytest.mark.asyncio
async def test_get_tree(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=init&type=images",
        json={
            "name": "images",
            "path": "",
            "writable": True,
            "dirs": [
                {
                    "name": "2026Program",
                    "path": "2026Program",
                    "writable": True,
                    "dirs": [],
                },
            ],
            "files": [
                {
                    "name": "root.jpg",
                    "size": 512,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
        },
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        tree = await client.get_tree()
    assert isinstance(tree, DirTree)
    assert tree.name == "images"
    assert len(tree.children) == 1
    assert tree.children[0].name == "2026Program"
    assert len(tree.files) == 1


@pytest.mark.asyncio
async def test_expand(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=expand&type=images",
        json={"dirs": ["sub1", "sub2"]},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        subdirs = await client.expand("2026Program")
    assert subdirs == ["sub1", "sub2"]


@pytest.mark.asyncio
async def test_create_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=newDir&type=images",
        text="true",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.create_dir("parent", "newdir")


@pytest.mark.asyncio
async def test_rename_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=renameDir&type=images",
        json={"name": "newname"},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.rename_dir("olddir", "newname")


@pytest.mark.asyncio
async def test_delete_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=deleteDir&type=images",
        text="true",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.delete_dir("olddir")


@pytest.mark.asyncio
async def test_download_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=downloadDir&type=images",
        content=b"zip data",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        zip_bytes = await client.download_dir("2026Program")
    assert zip_bytes == b"zip data"
