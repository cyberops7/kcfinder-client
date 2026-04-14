"""Tests for timeout and retry behavior on both sync and async clients."""

from unittest.mock import patch

import httpx
import pytest

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.client import KCFinderClient
from tests.conftest import BROWSE_URL

# --- Sync client tests ---


def test_timeout_passed_to_httpx_client(session_auth):
    client = KCFinderClient(BROWSE_URL, session_auth, timeout=30.0)
    with client:
        assert client._client.timeout == httpx.Timeout(30.0)  # type: ignore[union-attr]


def test_timeout_object_passed_to_httpx_client(session_auth):
    timeout = httpx.Timeout(5.0, connect=10.0)
    client = KCFinderClient(BROWSE_URL, session_auth, timeout=timeout)
    with client:
        assert client._client.timeout == timeout  # type: ignore[union-attr]


def test_default_timeout_uses_httpx_default(session_auth):
    with KCFinderClient(BROWSE_URL, session_auth) as client:
        assert client._client.timeout == httpx.Timeout(5.0)  # type: ignore[union-attr]


def test_retries_default_zero(session_auth):
    client = KCFinderClient(BROWSE_URL, session_auth)
    assert client._retries == 0


def test_retry_on_503_then_success(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=503)
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
            files = client.list_files()
    assert files == []


def test_retry_on_connect_error_then_success(session_auth, httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            files = client.list_files()
    assert files == []


def test_retry_exhausted_returns_last_5xx(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=503)
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=502)
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            resp = client._post("chDir", {"dir": "images"})
    assert resp.status_code == 502


def test_retry_exhausted_raises_last_exception(session_auth, httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("fail 1"))
    httpx_mock.add_exception(httpx.ConnectError("fail 2"))
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            with pytest.raises(httpx.ConnectError, match="fail 2"):
                client.list_files()


def test_no_retry_on_4xx(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=404)
    with KCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
        resp = client._post("chDir", {"dir": "images"})
    assert resp.status_code == 404
    assert len(httpx_mock.get_requests()) == 1


def test_no_retry_on_success(session_auth, httpx_mock):
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    with KCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
        client.list_files()
    assert len(httpx_mock.get_requests()) == 1


def test_retry_on_get_thumbnail(session_auth, httpx_mock):
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(content=b"png data")
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            thumb = client.get_thumbnail("dir", "photo.jpg")
    assert thumb == b"png data"


def test_retry_on_get_tree(session_auth, httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(
        json={
            "tree": {"name": "images", "writable": True, "hasDirs": False},
            "files": [],
        },
    )
    with patch("kcfinder_client._retry.time.sleep"):
        with KCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            tree = client.get_tree()
    assert tree.name == "images"


def test_upload_not_retried(session_auth, httpx_mock, tmp_path):
    """Upload should not be retried since file handles may be consumed."""
    httpx_mock.add_response(status_code=503)
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    with KCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
        # Upload bypasses _post, so the 503 is returned directly
        # without triggering a retry. The response text will be
        # checked by check_upload_response which won't error on
        # non-error text, but the key point is only 1 request was made.
        client.upload("test_dir", test_file)
    assert len(httpx_mock.get_requests()) == 1


# --- Async client tests ---


@pytest.mark.asyncio
async def test_async_timeout_passed_to_httpx_client(session_auth):
    client = AsyncKCFinderClient(BROWSE_URL, session_auth, timeout=30.0)
    async with client:
        assert client._client.timeout == httpx.Timeout(30.0)  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_async_retries_default_zero(session_auth):
    client = AsyncKCFinderClient(BROWSE_URL, session_auth)
    assert client._retries == 0


@pytest.mark.asyncio
async def test_async_retry_on_503_then_success(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=503)
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    with patch("kcfinder_client._retry.asyncio.sleep"):
        async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
            files = await client.list_files()
    assert files == []


@pytest.mark.asyncio
async def test_async_retry_on_connect_error_then_success(session_auth, httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("connection refused"))
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?act=chDir&type=images",
        json={"files": [], "dirWritable": True},
    )
    with patch("kcfinder_client._retry.asyncio.sleep"):
        async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            files = await client.list_files()
    assert files == []


@pytest.mark.asyncio
async def test_async_retry_exhausted_raises_last_exception(session_auth, httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("fail 1"))
    httpx_mock.add_exception(httpx.ConnectError("fail 2"))
    with patch("kcfinder_client._retry.asyncio.sleep"):
        async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            with pytest.raises(httpx.ConnectError, match="fail 2"):
                await client.list_files()


@pytest.mark.asyncio
async def test_async_no_retry_on_4xx(session_auth, httpx_mock):
    httpx_mock.add_response(url=f"{BROWSE_URL}?act=chDir&type=images", status_code=404)
    async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
        resp = await client._post("chDir", {"dir": "images"})
    assert resp.status_code == 404
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_async_retry_on_get_thumbnail(session_auth, httpx_mock):
    httpx_mock.add_response(status_code=503)
    httpx_mock.add_response(content=b"png data")
    with patch("kcfinder_client._retry.asyncio.sleep"):
        async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            thumb = await client.get_thumbnail("dir", "photo.jpg")
    assert thumb == b"png data"


@pytest.mark.asyncio
async def test_async_retry_on_get_tree(session_auth, httpx_mock):
    httpx_mock.add_response(status_code=500)
    httpx_mock.add_response(
        json={
            "tree": {"name": "images", "writable": True, "hasDirs": False},
            "files": [],
        },
    )
    with patch("kcfinder_client._retry.asyncio.sleep"):
        async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=1) as client:
            tree = await client.get_tree()
    assert tree.name == "images"


@pytest.mark.asyncio
async def test_async_upload_not_retried(session_auth, httpx_mock, tmp_path):
    """Upload should not be retried since file handles may be consumed."""
    httpx_mock.add_response(status_code=503)
    test_file = tmp_path / "photo.jpg"
    test_file.write_bytes(b"fake image data")
    async with AsyncKCFinderClient(BROWSE_URL, session_auth, retries=2) as client:
        await client.upload("test_dir", test_file)
    assert len(httpx_mock.get_requests()) == 1
