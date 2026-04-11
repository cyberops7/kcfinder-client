import httpx
import pytest

from kcfinder_client.auth import BaseAuth, HarmonySiteAuth, SessionAuth
from kcfinder_client.exceptions import AuthError


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


BROS_CONFIG = {
    "disabled": False,
    "uploadURL": "",
    "uploadDir": "/home/user/public_html",
    "thumbsDir": "/images/.thumbs",
    "denyUpdateCheck": True,
    "denyExtensionRename": True,
}


def test_harmonysite_auth_is_base_auth_subclass():
    assert issubclass(HarmonySiteAuth, BaseAuth)


def test_harmonysite_auth_get_referer():
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="pass",
        bros_config=BROS_CONFIG,
    )
    referer = auth.get_referer()
    assert "browse.php" in referer
    assert "bros_config" in referer
    assert "brosseccheck" in referer


@pytest.mark.asyncio
async def test_harmonysite_auth_login_failure(httpx_mock):
    httpx_mock.add_response(url="https://example.com/dbaction.php", status_code=403)
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="wrong",
        bros_config=BROS_CONFIG,
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(AuthError):
            await auth.authenticate(client)


def test_harmonysite_auth_login_failure_sync(httpx_mock):
    httpx_mock.add_response(url="https://example.com/dbaction.php", status_code=403)
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="wrong",
        bros_config=BROS_CONFIG,
    )
    with httpx.Client() as client:
        with pytest.raises(AuthError):
            auth.authenticate_sync(client)


@pytest.mark.asyncio
async def test_harmonysite_auth_success(httpx_mock):
    httpx_mock.add_response(url="https://example.com/dbaction.php", status_code=200)
    httpx_mock.add_response(status_code=200)  # Matches browse.php GET with query params
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="pass",
        bros_config=BROS_CONFIG,
    )
    async with httpx.AsyncClient() as client:
        await auth.authenticate(client)
    # If we get here without AuthError, auth succeeded
