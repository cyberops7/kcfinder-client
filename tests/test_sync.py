import pytest

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.client import KCFinderClient
from kcfinder_client.sync import SyncManager, SyncManagerSync
from tests.conftest import BROWSE_URL


@pytest.mark.asyncio
async def test_push_uploads_new_files(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "writable": True},
    )
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=upload&type=images&dir=remote_dir", text="")

    local_dir = tmp_path / "images"
    local_dir.mkdir()
    (local_dir / "new.jpg").write_bytes(b"data")

    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManager(client)
        result = await manager.push("remote_dir", local_dir)

    assert result.uploaded == ["new.jpg"]
    assert result.deleted == []
    assert result.skipped == []


@pytest.mark.asyncio
async def test_push_deletes_remote_only_files(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "old.jpg",
                    "size": 100,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
            "writable": True,
        },
    )
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=delete&type=images", text="true")

    local_dir = tmp_path / "images"
    local_dir.mkdir()

    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManager(client)
        result = await manager.push("remote_dir", local_dir)

    assert result.uploaded == []
    assert result.deleted == ["old.jpg"]
    assert result.skipped == []


@pytest.mark.asyncio
async def test_push_skips_matching_files(session_auth, httpx_mock, tmp_path):
    local_dir = tmp_path / "images"
    local_dir.mkdir()
    local_file = local_dir / "same.jpg"
    local_file.write_bytes(b"x" * 512)

    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "same.jpg",
                    "size": 512,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
            "writable": True,
        },
    )

    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManager(client)
        result = await manager.push("remote_dir", local_dir)

    assert result.uploaded == []
    assert result.deleted == []
    assert result.skipped == ["same.jpg"]


@pytest.mark.asyncio
async def test_push_uploads_size_mismatch(session_auth, httpx_mock, tmp_path):
    local_dir = tmp_path / "images"
    local_dir.mkdir()
    (local_dir / "changed.jpg").write_bytes(b"x" * 1024)

    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "changed.jpg",
                    "size": 512,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
            "writable": True,
        },
    )
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=upload&type=images&dir=remote_dir", text="")

    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManager(client)
        result = await manager.push("remote_dir", local_dir)

    assert result.uploaded == ["changed.jpg"]
    assert result.deleted == []
    assert result.skipped == []


@pytest.mark.asyncio
async def test_push_dry_run(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "old.jpg",
                    "size": 100,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
            "writable": True,
        },
    )

    local_dir = tmp_path / "images"
    local_dir.mkdir()
    (local_dir / "new.jpg").write_bytes(b"data")

    async with AsyncKCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManager(client)
        result = await manager.push("remote_dir", local_dir, dry_run=True)

    assert result.uploaded == ["new.jpg"]
    assert result.deleted == ["old.jpg"]
    assert result.skipped == []


# Sync versions
def test_push_sync_uploads_new_files(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "writable": True},
    )
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=upload&type=images&dir=remote_dir", text="")

    local_dir = tmp_path / "images"
    local_dir.mkdir()
    (local_dir / "new.jpg").write_bytes(b"data")

    with KCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManagerSync(client)
        result = manager.push("remote_dir", local_dir)

    assert result.uploaded == ["new.jpg"]
    assert result.deleted == []
    assert result.skipped == []


def test_push_sync_dry_run(session_auth, httpx_mock, tmp_path):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={
            "files": [
                {
                    "name": "old.jpg",
                    "size": 100,
                    "mtime": 1704067200,
                    "readable": True,
                    "writable": True,
                },
            ],
            "writable": True,
        },
    )

    local_dir = tmp_path / "images"
    local_dir.mkdir()
    (local_dir / "new.jpg").write_bytes(b"data")

    with KCFinderClient(BROWSE_URL, session_auth) as client:
        manager = SyncManagerSync(client)
        result = manager.push("remote_dir", local_dir, dry_run=True)

    assert result.uploaded == ["new.jpg"]
    assert result.deleted == ["old.jpg"]
