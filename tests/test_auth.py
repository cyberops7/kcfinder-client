import base64
import json
import os
from datetime import UTC, datetime
from unittest.mock import patch

import httpx
import pytest

from kcfinder_client.auth import (
    BaseAuth,
    HarmonySiteAuth,
    SessionAuth,
    harmonysite_auth_from_env,
    parse_signed_bros_params,
)
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


BROS_CONFIG = (
    'a:6:{s:8:"disabled";b:0;s:9:"uploadURL";s:0:"";'
    's:9:"uploadDir";s:27:"/home/user/public_html";'
    's:9:"thumbsDir";s:15:"/images/.thumbs";'
    's:15:"denyUpdateCheck";b:1;s:19:"denyExtensionRename";b:1;}'
)


def test_session_auth_get_query_params():
    auth = SessionAuth(
        session_id="abc123", referer="https://example.com/kcfinder/browse.php"
    )
    assert auth.get_query_params() == {}


def test_harmonysite_auth_is_base_auth_subclass():
    assert issubclass(HarmonySiteAuth, BaseAuth)


def test_harmonysite_auth_get_query_params():
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="pass",
        bros_config=BROS_CONFIG,
        brosseccheck="Xx-ok-xX",
    )
    params = auth.get_query_params()
    assert params == {"bros_config": BROS_CONFIG, "brosseccheck": "Xx-ok-xX"}


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
    httpx_mock.add_response(
        url="https://example.com/dbaction.php",
        status_code=200,
        headers=[("Set-Cookie", "PHPSESSID=abc123"), ("Set-Cookie", "fakelevel=4")],
    )
    # Serves the config page (no signed URL, so legacy params) and the init GET
    httpx_mock.add_response(status_code=200, is_reusable=True)
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


def test_harmonysite_auth_success_sync(httpx_mock):
    httpx_mock.add_response(
        url="https://example.com/dbaction.php",
        status_code=200,
        headers=[("Set-Cookie", "PHPSESSID=abc123"), ("Set-Cookie", "fakelevel=4")],
    )
    # Serves the config page (no signed URL, so legacy params) and the init GET
    httpx_mock.add_response(status_code=200, is_reusable=True)
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="pass",
        bros_config=BROS_CONFIG,
    )
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    # If we get here without AuthError, auth succeeded


@pytest.mark.asyncio
async def test_harmonysite_auth_bad_credentials_200(httpx_mock):
    """HarmonySite returns 200 on bad credentials but omits the fakelevel cookie."""
    httpx_mock.add_response(
        url="https://example.com/dbaction.php",
        status_code=200,
        headers=[("Set-Cookie", "PHPSESSID=abc123")],
    )
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="wrong",
        bros_config=BROS_CONFIG,
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(AuthError, match="invalid credentials"):
            await auth.authenticate(client)


def test_harmonysite_auth_bad_credentials_200_sync(httpx_mock):
    """HarmonySite returns 200 on bad credentials but omits the fakelevel cookie."""
    httpx_mock.add_response(
        url="https://example.com/dbaction.php",
        status_code=200,
        headers=[("Set-Cookie", "PHPSESSID=abc123")],
    )
    auth = HarmonySiteAuth(
        login_url="https://example.com/dbaction.php",
        browse_url="https://example.com/kcfinder/browse.php",
        username="user",
        password="wrong",
        bros_config=BROS_CONFIG,
    )
    with httpx.Client() as client:
        with pytest.raises(AuthError, match="invalid credentials"):
            auth.authenticate_sync(client)


def test_harmonysite_auth_from_env():
    env = {
        "KCFINDER_LOGIN_URL": "https://example.com/dbaction.php",
        "KCFINDER_BROWSE_URL": "https://example.com/kcfinder/browse.php",
        "KCFINDER_USERNAME": "testuser",
        "KCFINDER_PASSWORD": "testpass",
        "KCFINDER_BROS_CONFIG": 'a:1:{s:9:"uploadDir";s:27:"/home/user/public_html";}',
        "KCFINDER_BROSSECCHECK": "Xx-ok-xX",
    }
    with patch.dict(os.environ, env, clear=False):
        auth = harmonysite_auth_from_env()
    assert isinstance(auth, HarmonySiteAuth)
    assert "browse.php" in auth.get_referer()


def test_harmonysite_auth_from_env_missing_var():
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(KeyError):
            harmonysite_auth_from_env()


def test_harmonysite_auth_from_env_default_brosseccheck():
    env = {
        "KCFINDER_LOGIN_URL": "https://example.com/dbaction.php",
        "KCFINDER_BROWSE_URL": "https://example.com/kcfinder/browse.php",
        "KCFINDER_USERNAME": "testuser",
        "KCFINDER_PASSWORD": "testpass",
        "KCFINDER_BROS_CONFIG": 'a:1:{s:8:"disabled";b:0;}',
    }
    with patch.dict(os.environ, env, clear=False):
        auth = harmonysite_auth_from_env()
    assert isinstance(auth, HarmonySiteAuth)
    assert "brosseccheck" in auth.get_referer()


# --- Signed bros_config (HarmonySite, 2026-11) ---

LOGIN_URL = "https://example.com/dbaction.php"
BROWSE_URL = "https://example.com/brostools/jquery/kcfinder/browse.php"
CONFIG_PAGE_URL = "https://example.com/dbpage.php?pg=form&dbase=pages"
EXP = 1793775267
SIGNED_CONFIG = (
    base64.b64encode(json.dumps({"c": {"disabled": False}, "exp": EXP}).encode())
    .decode()
    .rstrip("=")
)
SIGNATURE = "59a2a9d3276f8d0ed370ebe4b3407c6eac628dcc009b701bf921081f063a7892"
CONFIG_PAGE = (
    "<script>var kc = '/brostools/jquery/kcfinder/browse.php?type=images"
    f"&bros_config={SIGNED_CONFIG}&bros_sig={SIGNATURE}';</script>"
)
REFUSED_INIT = (
    "<html><body><script type='text/javascript'>\n"
    "alert('You don\\'t have permissions to browse server.');\n"
    "if (window.opener) window.close();\n</script></body></html>"
)
KCFINDER_PAGE = "<!DOCTYPE html><html><head><title>KCFinder</title></head></html>"


def _signed_auth(**kwargs) -> HarmonySiteAuth:
    return HarmonySiteAuth(
        login_url=LOGIN_URL,
        browse_url=BROWSE_URL,
        username="user",
        password="pass",
        **kwargs,
    )


def _mock_login(httpx_mock) -> None:
    httpx_mock.add_response(
        url=LOGIN_URL,
        headers=[("Set-Cookie", "PHPSESSID=abc123"), ("Set-Cookie", "fakelevel=4")],
    )


def _mock_init(httpx_mock, text: str = KCFINDER_PAGE) -> None:
    httpx_mock.add_response(
        url=f"{BROWSE_URL}?bros_config={SIGNED_CONFIG}&bros_sig={SIGNATURE}",
        text=text,
    )


def test_parse_signed_bros_params():
    assert parse_signed_bros_params(CONFIG_PAGE) == {
        "bros_config": SIGNED_CONFIG,
        "bros_sig": SIGNATURE,
    }


def test_parse_signed_bros_params_html_escaped():
    page = CONFIG_PAGE.replace("&", "&amp;")
    assert parse_signed_bros_params(page) == {
        "bros_config": SIGNED_CONFIG,
        "bros_sig": SIGNATURE,
    }


def test_parse_signed_bros_params_absent():
    assert parse_signed_bros_params("<html>no kcfinder here</html>") is None


def test_harmonysite_auth_discovers_signed_params_sync(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock)
    auth = _signed_auth()
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    assert auth.get_query_params() == {
        "bros_config": SIGNED_CONFIG,
        "bros_sig": SIGNATURE,
    }
    assert "bros_sig" in auth.get_referer()
    assert "brosseccheck" not in auth.get_referer()


@pytest.mark.asyncio
async def test_harmonysite_auth_discovers_signed_params_async(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock)
    auth = _signed_auth()
    async with httpx.AsyncClient() as client:
        await auth.authenticate(client)
    assert auth.get_query_params() == {
        "bros_config": SIGNED_CONFIG,
        "bros_sig": SIGNATURE,
    }


def test_harmonysite_auth_signed_params_win_over_legacy(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock)
    auth = _signed_auth(bros_config=BROS_CONFIG)
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    assert auth.get_query_params()["bros_sig"] == SIGNATURE


def test_harmonysite_auth_expires_at(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock)
    auth = _signed_auth()
    assert auth.expires_at is None
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    assert auth.expires_at == datetime.fromtimestamp(EXP, tz=UTC)


def test_harmonysite_auth_custom_config_page_url(httpx_mock):
    custom = "https://example.com/dbpage.php?pg=form&dbase=news"
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=custom, text=CONFIG_PAGE)
    _mock_init(httpx_mock)
    auth = _signed_auth(config_page_url=custom)
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    assert auth.get_query_params()["bros_sig"] == SIGNATURE


def test_harmonysite_auth_falls_back_to_legacy_params(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text="<html>no kcfinder</html>")
    httpx_mock.add_response(text=KCFINDER_PAGE)  # legacy init GET
    auth = _signed_auth(bros_config=BROS_CONFIG)
    with httpx.Client() as client:
        auth.authenticate_sync(client)
    assert auth.get_query_params() == {
        "bros_config": BROS_CONFIG,
        "brosseccheck": "Xx-ok-xX",
    }
    assert auth.expires_at is None


def test_harmonysite_auth_no_signed_and_no_legacy_raises(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text="<html>no kcfinder</html>")
    auth = _signed_auth()
    with httpx.Client() as client:
        with pytest.raises(AuthError, match="signed KCFinder"):
            auth.authenticate_sync(client)


def test_harmonysite_auth_refused_init_raises_sync(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock, text=REFUSED_INIT)
    auth = _signed_auth()
    with httpx.Client() as client:
        with pytest.raises(AuthError, match="refused"):
            auth.authenticate_sync(client)


@pytest.mark.asyncio
async def test_harmonysite_auth_refused_init_raises_async(httpx_mock):
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text=CONFIG_PAGE)
    _mock_init(httpx_mock, text=REFUSED_INIT)
    auth = _signed_auth()
    async with httpx.AsyncClient() as client:
        with pytest.raises(AuthError, match="refused"):
            await auth.authenticate(client)


def test_harmonysite_auth_from_env_without_bros_config():
    env = {
        "KCFINDER_LOGIN_URL": LOGIN_URL,
        "KCFINDER_BROWSE_URL": BROWSE_URL,
        "KCFINDER_USERNAME": "testuser",
        "KCFINDER_PASSWORD": "testpass",
    }
    with patch.dict(os.environ, env, clear=True):
        auth = harmonysite_auth_from_env()
    assert isinstance(auth, HarmonySiteAuth)


def test_harmonysite_auth_from_env_empty_bros_config_is_unset(httpx_mock):
    """An empty KCFINDER_BROS_CONFIG must not count as a legacy fallback."""
    env = {
        "KCFINDER_LOGIN_URL": LOGIN_URL,
        "KCFINDER_BROWSE_URL": BROWSE_URL,
        "KCFINDER_USERNAME": "testuser",
        "KCFINDER_PASSWORD": "testpass",
        "KCFINDER_BROS_CONFIG": "",
        "KCFINDER_CONFIG_PAGE_URL": "",
    }
    with patch.dict(os.environ, env, clear=True):
        auth = harmonysite_auth_from_env()
    _mock_login(httpx_mock)
    httpx_mock.add_response(url=CONFIG_PAGE_URL, text="<html>no kcfinder</html>")
    with httpx.Client() as client:
        with pytest.raises(AuthError, match="signed KCFinder"):
            auth.authenticate_sync(client)
