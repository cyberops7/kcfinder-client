import httpx
import pytest

from kcfinder_client.auth import BaseAuth, SessionAuth


def test_session_auth_is_base_auth_subclass():
    assert issubclass(SessionAuth, BaseAuth)


def test_session_auth_get_referer():
    auth = SessionAuth(
        session_id="abc123", referer="https://example.com/kcfinder/browse.php"
    )
    assert auth.get_referer() == "https://example.com/kcfinder/browse.php"


def test_session_auth_sets_cookie_sync():
    auth = SessionAuth(
        session_id="abc123", referer="https://example.com/kcfinder/browse.php"
    )
    client = httpx.Client()
    auth.authenticate_sync(client)
    assert client.cookies.get("PHPSESSID") == "abc123"
    client.close()


@pytest.mark.asyncio
async def test_session_auth_sets_cookie_async():
    auth = SessionAuth(
        session_id="abc123", referer="https://example.com/kcfinder/browse.php"
    )
    client = httpx.AsyncClient()
    await auth.authenticate(client)
    assert client.cookies.get("PHPSESSID") == "abc123"
    await client.aclose()
