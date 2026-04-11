import pytest

from kcfinder_client.auth import SessionAuth


@pytest.fixture
def session_auth():
    return SessionAuth(
        session_id="test-session-id", referer="https://example.com/browse.php"
    )


BROWSE_URL = "https://example.com/browse.php"
