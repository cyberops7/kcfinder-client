import pytest

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.exceptions import ActionError, UploadError
from kcfinder_client.models import DirTree, FileInfo
from tests.conftest import BROWSE_URL


@pytest.mark.asyncio
async def test_async_client_context_manager(session_auth):
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        assert client is not None


@pytest.mark.asyncio
async def test_async_client_raises_outside_context_manager(session_auth):
    client = AsyncKCFinderClient(BROWSE_URL, session_auth)
    with pytest.raises(RuntimeError, match="context manager"):
        await client.list_files()


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
            "dirWritable": True,
        },
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        files = await client.list_files("test_dir")
    assert len(files) == 2
    assert isinstance(files[0], FileInfo)
    assert files[0].name == "photo.jpg"


@pytest.mark.asyncio
async def test_list_files_empty_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        files = await client.list_files("empty-dir")
    assert files == []


@pytest.mark.asyncio
async def test_upload_single_file(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images&dir=images%2Ftest_dir",
        text="",
    )
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.upload("test_dir", test_file)


@pytest.mark.asyncio
async def test_upload_multiple_files(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images&dir=images%2Ftest_dir",
        text="",
    )
    file_a = tmp_path / "a.jpg"
    file_b = tmp_path / "b.jpg"
    file_a.write_bytes(b"data a")
    file_b.write_bytes(b"data b")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.upload("test_dir", [file_a, file_b])


@pytest.mark.asyncio
async def test_upload_root_dir(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images&dir=images",
        text="",
    )
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.upload("", test_file)


@pytest.mark.asyncio
async def test_upload_error(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=upload&type=images&dir=images%2Ftest_dir",
        text="notes.txt: File type not allowed",
    )
    test_file = tmp_path / "notes.txt"
    test_file.write_bytes(b"not an image")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        with pytest.raises(UploadError, match="File type not allowed"):
            await client.upload("test_dir", test_file)


@pytest.mark.asyncio
async def test_delete(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=delete&type=images",
        text="{}",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.delete("test_dir", "old.jpg")


@pytest.mark.asyncio
async def test_delete_error(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=delete&type=images",
        json={"error": "Unknown error."},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        with pytest.raises(ActionError, match="Unknown error"):
            await client.delete("test_dir", "missing.jpg")


@pytest.mark.asyncio
async def test_rename(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=rename&type=images",
        text="{}",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.rename("test_dir", "old.jpg", "new.jpg")


@pytest.mark.asyncio
async def test_download(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=download&type=images",
        content=b"binary file content",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        content = await client.download("test_dir", "photo.jpg")
    assert content == b"binary file content"


@pytest.mark.asyncio
async def test_get_thumbnail(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=thumb&type=images&dir=images%2Ftest_dir&file=photo.jpg",
        content=b"png data",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        thumb = await client.get_thumbnail("test_dir", "photo.jpg")
    assert thumb == b"png data"


@pytest.mark.asyncio
async def test_get_tree(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=init&type=images",
        json={
            "tree": {
                "name": "images",
                "writable": True,
                "hasDirs": True,
                "dirs": [
                    {
                        "name": "test_dir",
                        "writable": True,
                        "hasDirs": False,
                    },
                ],
            },
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
    assert tree.children[0].name == "test_dir"
    assert len(tree.files) == 1


@pytest.mark.asyncio
async def test_expand(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=expand&type=images",
        json={
            "dirs": [
                {
                    "name": "sub1",
                    "readable": True,
                    "writable": True,
                    "removable": True,
                    "hasDirs": False,
                },
                {
                    "name": "sub2",
                    "readable": True,
                    "writable": True,
                    "removable": True,
                    "hasDirs": True,
                },
            ],
        },
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        subdirs = await client.expand("test_dir")
    assert len(subdirs) == 2
    assert isinstance(subdirs[0], DirTree)
    assert subdirs[0].name == "sub1"
    assert subdirs[1].has_subdirs is True


@pytest.mark.asyncio
async def test_create_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=newDir&type=images",
        text="{}",
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
        text="{}",
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
        zip_bytes = await client.download_dir("test_dir")
    assert zip_bytes == b"zip data"


@pytest.mark.asyncio
async def test_copy(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=cp_cbd&type=images",
        text="{}",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.copy(["dir/a.jpg", "dir/b.jpg"], dest="archive")


@pytest.mark.asyncio
async def test_move(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=mv_cbd&type=images",
        text="{}",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.move(["dir/a.jpg", "dir/b.jpg"], dest="archive")


@pytest.mark.asyncio
async def test_bulk_delete(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=rm_cbd&type=images",
        text="{}",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        await client.bulk_delete(["dir/a.jpg", "dir/b.jpg"])


@pytest.mark.asyncio
async def test_bulk_delete_error(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=rm_cbd&type=images",
        json={"error": ["Cannot delete 'a.jpg'", "Cannot delete 'b.jpg'"]},
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        with pytest.raises(ActionError, match="Cannot delete 'a.jpg'"):
            await client.bulk_delete(["dir/a.jpg", "dir/b.jpg"])


@pytest.mark.asyncio
async def test_download_selected(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=downloadSelected&type=images",
        content=b"zip data",
    )
    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        zip_bytes = await client.download_selected("test_dir", ["a.jpg", "b.jpg"])
    assert zip_bytes == b"zip data"
