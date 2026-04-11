import pytest

from kcfinder_client.client import KCFinderClient
from kcfinder_client.exceptions import ActionError
from kcfinder_client.models import DirTree, FileInfo
from tests.conftest import BROWSE_URL


def test_sync_client_context_manager(session_auth):
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        assert client is not None


def test_list_files(session_auth, httpx_mock):
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
            ],
            "writable": True,
        },
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        files = client.list_files("2026Program")
    assert len(files) == 1
    assert isinstance(files[0], FileInfo)


def test_upload(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=upload&type=images", text="")
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.upload("2026Program", test_file)


def test_delete(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=delete&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.delete("2026Program", "old.jpg")


def test_delete_error(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=delete&type=images", text="File not found"
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        with pytest.raises(ActionError, match="File not found"):
            client.delete("2026Program", "missing.jpg")


def test_rename(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=rename&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.rename("2026Program", "old.jpg", "new.jpg")


def test_download(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=download&type=images", content=b"binary content"
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        content = client.download("2026Program", "photo.jpg")
    assert content == b"binary content"


def test_get_thumbnail(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=thumb&type=images", content=b"png data"
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        thumb = client.get_thumbnail("2026Program", "photo.jpg")
    assert thumb == b"png data"


def test_get_tree(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=init&type=images",
        json={"name": "images", "path": "", "writable": True, "dirs": [], "files": []},
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        tree = client.get_tree()
    assert isinstance(tree, DirTree)


def test_expand(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=expand&type=images", json={"dirs": ["sub1"]}
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        subdirs = client.expand("2026Program")
    assert subdirs == ["sub1"]


def test_create_dir(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=newDir&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.create_dir("parent", "newdir")


def test_rename_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=renameDir&type=images", json={"name": "newname"}
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.rename_dir("olddir", "newname")


def test_delete_dir(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=deleteDir&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.delete_dir("olddir")


def test_download_dir(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=downloadDir&type=images", content=b"zip data"
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        zip_bytes = client.download_dir("2026Program")
    assert zip_bytes == b"zip data"


def test_copy(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=cp_cbd&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.copy(["dir/a.jpg", "dir/b.jpg"], dest="archive")


def test_move(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=mv_cbd&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.move(["dir/a.jpg", "dir/b.jpg"], dest="archive")


def test_bulk_delete(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=rm_cbd&type=images", text="true")
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        client.bulk_delete(["dir/a.jpg", "dir/b.jpg"])


def test_download_selected(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=downloadSelected&type=images", content=b"zip data"
    )
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        zip_bytes = client.download_selected("2026Program", ["a.jpg", "b.jpg"])
    assert zip_bytes == b"zip data"
