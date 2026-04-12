"""Live tests for validating KCFinderClient against a real server."""

import base64
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv
from invoke import task

from kcfinder_client import ActionError, KCFinderClient
from kcfinder_client.auth import harmonysite_auth_from_env

TEST_PREFIX = "_test_"

REQUIRED_ENV_VARS = [
    "KCFINDER_LOGIN_URL",
    "KCFINDER_BROWSE_URL",
    "KCFINDER_USERNAME",
    "KCFINDER_PASSWORD",
    "KCFINDER_BROS_CONFIG",
]

# Minimal valid 1x1 white JPEG
_JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJ"
    "CQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcp"
    "LDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwh"
    "MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIy"
    "MjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QA"
    "HwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAA"
    "AgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKB"
    "kaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6"
    "Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWG"
    "h4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG"
    "x8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QA"
    "HwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREA"
    "AgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEI"
    "FEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5"
    "OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOE"
    "hYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPE"
    "xcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oA"
    "DAMBAAIRAxEAPwD3+iiigD//2Q=="
)


def _check_env() -> None:
    """Exit with a clear message if required env vars are missing."""
    load_dotenv()
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        print(f"Missing required env vars: {', '.join(missing)}")
        sys.exit(1)


@contextmanager
def _get_client():
    """Authenticate and yield a KCFinderClient."""
    _check_env()
    auth = harmonysite_auth_from_env()
    browse_url = os.environ["KCFINDER_BROWSE_URL"]
    with KCFinderClient(browse_url, auth) as client:
        yield client


def _make_test_jpeg() -> Path:
    """Write a minimal JPEG to a temp file and return the path."""
    f = tempfile.NamedTemporaryFile(
        prefix=TEST_PREFIX, suffix=".jpg", delete=False
    )
    f.write(base64.b64decode(_JPEG_B64))
    f.close()
    return Path(f.name)


def _ensure_dir(client: KCFinderClient, name: str) -> None:
    """Create a directory, ignoring errors if it already exists."""
    try:
        client.create_dir("", name)
    except ActionError:
        pass


@task
def auth(c):
    """Authenticate and confirm the session is valid."""
    with _get_client() as client:
        tree = client.get_tree()
        print(f"Authenticated. Root: {tree.name}")
