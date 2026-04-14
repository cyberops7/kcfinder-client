"""Live tests for validating KCFinderClient against a real server."""

import base64
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import httpx
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
    f = tempfile.NamedTemporaryFile(prefix=TEST_PREFIX, suffix=".jpg", delete=False)
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
    """Authenticate with valid credentials, then verify bad credentials fail."""
    from kcfinder_client.auth import HarmonySiteAuth
    from kcfinder_client.exceptions import AuthError

    # Step 1: valid credentials should succeed
    with _get_client() as client:
        tree = client.get_tree()
        print(f"Valid login succeeded. Root: {tree.name}")

    # Step 2: bad credentials should raise AuthError
    _check_env()
    bad_auth = HarmonySiteAuth(
        login_url=os.environ["KCFINDER_LOGIN_URL"],
        browse_url=os.environ["KCFINDER_BROWSE_URL"],
        username=os.environ["KCFINDER_USERNAME"],
        password="definitely-wrong-password-12345",
        bros_config=os.environ["KCFINDER_BROS_CONFIG"],
        brosseccheck=os.environ.get("KCFINDER_BROSSECCHECK", "Xx-ok-xX"),
    )
    browse_url = os.environ["KCFINDER_BROWSE_URL"]
    try:
        with KCFinderClient(browse_url, bad_auth) as client:
            client.get_tree()
        print("ERROR: Bad credentials were accepted!")
        sys.exit(1)
    except AuthError as e:
        print(f"Bad login rejected: {e}")


# ---------------------------------------------------------------------------
# Read-only subcommands
# ---------------------------------------------------------------------------


@task(name="list", optional=["dir"])
def list_(c, dir=""):
    """List files in a directory (root by default)."""
    with _get_client() as client:
        files = client.list_files(dir)
        print(f"Root directory: {len(files)} files")
        for f in files:
            print(f"  {f.name} ({f.size:,} bytes)")


@task
def tree(c):
    """Get the root directory node with immediate subdirectories."""
    with _get_client() as client:
        t = client.get_tree()
        _print_tree(t, indent=0)


def _print_tree(node, indent=0):
    """Recursively print a DirTree."""
    prefix = "  " * indent
    writable = "w" if node.is_writable else "r"
    print(f"{prefix}{node.name}/ [{writable}]")
    for child in node.children:
        _print_tree(child, indent + 1)
    for f in node.files:
        print(f"{prefix}  {f.name} ({f.size:,} bytes)")


@task(optional=["dir"])
def expand(c, dir=""):
    """List subdirectories of a directory (root by default)."""
    with _get_client() as client:
        dirs = client.expand(dir)
        label = dir if dir else "Root"
        print(f"{label} subdirectories: {len(dirs)}")
        for d in dirs:
            subdirs = " (has subdirs)" if d.has_subdirs else ""
            writable = "w" if d.is_writable else "r"
            print(f"  {d.name}/ [{writable}]{subdirs}")


# ---------------------------------------------------------------------------
# Directory mutation subcommands
# ---------------------------------------------------------------------------


@task
def mkdir(c):
    """Create a test directory."""
    name = f"{TEST_PREFIX}mkdir"
    with _get_client() as client:
        client.create_dir("", name)
        print(f"Created: {name}/")
        dirs = client.expand("")
        found = any(d.name == name for d in dirs)
        print(f"Visible in tree: {found}")


@task(name="list-dir")
def list_dir(c):
    """Create a test directory with a file, then list its contents."""
    name = f"{TEST_PREFIX}list"
    with _get_client() as client:
        _ensure_dir(client, name)
        jpeg = _make_test_jpeg()
        client.upload(name, jpeg)
        jpeg.unlink()
        files = client.list_files(name)
        print(f"Directory {name}/: {len(files)} files")
        for f in files:
            print(f"  {f.name} ({f.size:,} bytes)")


@task(name="rename-dir")
def rename_dir(c):
    """Create a test directory, rename it, and verify."""
    old_name = f"{TEST_PREFIX}renamedir"
    new_name = f"{TEST_PREFIX}renamedir_new"
    with _get_client() as client:
        _ensure_dir(client, old_name)
        print(f"Created: {old_name}/")
        client.rename_dir(old_name, new_name)
        print(f"Renamed: {old_name}/ -> {new_name}/")
        dirs = client.expand("")
        found = any(d.name == new_name for d in dirs)
        print(f"Visible as {new_name}/: {found}")


@task(name="delete-dir")
def delete_dir(c):
    """Create a test directory, delete it, and verify it's gone."""
    name = f"{TEST_PREFIX}deletedir"
    with _get_client() as client:
        _ensure_dir(client, name)
        print(f"Created: {name}/")
        client.delete_dir(name)
        print(f"Deleted: {name}/")
        dirs = client.expand("")
        found = any(d.name == name for d in dirs)
        print(f"Still visible: {found}")


# ---------------------------------------------------------------------------
# File mutation subcommands
# ---------------------------------------------------------------------------


@task
def upload(c):
    """Upload a test JPEG file."""
    dir_name = f"{TEST_PREFIX}upload"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name} -> {dir_name}/")
        files = client.list_files(dir_name)
        found = any(f.name == jpeg.name for f in files)
        print(f"Visible in listing: {found}")
        jpeg.unlink()


@task
def download(c):
    """Upload a file, download it, and verify the bytes match."""
    dir_name = f"{TEST_PREFIX}download"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        original_bytes = jpeg.read_bytes()
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name} ({len(original_bytes)} bytes)")
        downloaded = client.download(dir_name, jpeg.name)
        match = downloaded == original_bytes
        print(f"Downloaded: {len(downloaded)} bytes, match: {match}")
        jpeg.unlink()


@task
def thumb(c):
    """Upload an image, then get its thumbnail."""
    dir_name = f"{TEST_PREFIX}thumb"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name}")
        data = client.get_thumbnail(dir_name, jpeg.name)
        print(f"Thumbnail: {len(data)} bytes")
        jpeg.unlink()


@task
def rename(c):
    """Upload a file, rename it, and verify the new name."""
    dir_name = f"{TEST_PREFIX}rename"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        new_name = jpeg.stem + "_renamed.jpg"
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name}")
        client.rename(dir_name, jpeg.name, new_name)
        print(f"Renamed: {jpeg.name} -> {new_name}")
        files = client.list_files(dir_name)
        found = any(f.name == new_name for f in files)
        print(f"Visible as {new_name}: {found}")
        jpeg.unlink()


@task
def delete(c):
    """Upload a file, delete it, and verify it's gone."""
    dir_name = f"{TEST_PREFIX}delete"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name}")
        client.delete(dir_name, jpeg.name)
        print(f"Deleted: {jpeg.name}")
        files = client.list_files(dir_name)
        found = any(f.name == jpeg.name for f in files)
        print(f"Still visible: {found}")
        jpeg.unlink()


# ---------------------------------------------------------------------------
# Bulk operation subcommands
# ---------------------------------------------------------------------------


@task
def copy(c):
    """Upload a file, copy it to another directory, and verify."""
    src_dir = f"{TEST_PREFIX}copy"
    dest_dir = f"{TEST_PREFIX}copy_dest"
    with _get_client() as client:
        _ensure_dir(client, src_dir)
        _ensure_dir(client, dest_dir)
        jpeg = _make_test_jpeg()
        client.upload(src_dir, jpeg)
        print(f"Uploaded: {jpeg.name} -> {src_dir}/")
        client.copy([f"{src_dir}/{jpeg.name}"], dest=dest_dir)
        print(f"Copied to: {dest_dir}/")
        files = client.list_files(dest_dir)
        found = any(f.name == jpeg.name for f in files)
        print(f"Visible in {dest_dir}/: {found}")
        jpeg.unlink()


@task
def move(c):
    """Upload a file, move it to another directory, and verify."""
    src_dir = f"{TEST_PREFIX}move"
    dest_dir = f"{TEST_PREFIX}move_dest"
    with _get_client() as client:
        _ensure_dir(client, src_dir)
        _ensure_dir(client, dest_dir)
        jpeg = _make_test_jpeg()
        client.upload(src_dir, jpeg)
        print(f"Uploaded: {jpeg.name} -> {src_dir}/")
        client.move([f"{src_dir}/{jpeg.name}"], dest=dest_dir)
        print(f"Moved to: {dest_dir}/")
        src_files = client.list_files(src_dir)
        gone = not any(f.name == jpeg.name for f in src_files)
        print(f"Gone from {src_dir}/: {gone}")
        dest_files = client.list_files(dest_dir)
        arrived = any(f.name == jpeg.name for f in dest_files)
        print(f"Visible in {dest_dir}/: {arrived}")
        jpeg.unlink()


@task(name="bulk-delete")
def bulk_delete(c):
    """Upload two files, bulk delete both, and verify they're gone."""
    dir_name = f"{TEST_PREFIX}bulkdel"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg1 = _make_test_jpeg()
        jpeg2 = _make_test_jpeg()
        client.upload(dir_name, jpeg1)
        client.upload(dir_name, jpeg2)
        print(f"Uploaded: {jpeg1.name}, {jpeg2.name}")
        client.bulk_delete(
            [
                f"{dir_name}/{jpeg1.name}",
                f"{dir_name}/{jpeg2.name}",
            ]
        )
        print("Bulk deleted both")
        files = client.list_files(dir_name)
        remaining = [f.name for f in files]
        print(f"Remaining in {dir_name}/: {remaining}")
        jpeg1.unlink()
        jpeg2.unlink()


# ---------------------------------------------------------------------------
# Download archive subcommands
# ---------------------------------------------------------------------------


@task(name="download-dir")
def download_dir(c):
    """Create a test directory with a file, download it as ZIP."""
    dir_name = f"{TEST_PREFIX}dldir"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg = _make_test_jpeg()
        client.upload(dir_name, jpeg)
        print(f"Uploaded: {jpeg.name} -> {dir_name}/")
        zip_bytes = client.download_dir(dir_name)
        print(f"Downloaded ZIP: {len(zip_bytes):,} bytes")
        valid = zip_bytes[:2] == b"PK"
        print(f"Valid ZIP: {valid}")
        jpeg.unlink()


@task(name="download-sel")
def download_sel(c):
    """Upload files, download a selection as ZIP."""
    dir_name = f"{TEST_PREFIX}dlsel"
    with _get_client() as client:
        _ensure_dir(client, dir_name)
        jpeg1 = _make_test_jpeg()
        jpeg2 = _make_test_jpeg()
        client.upload(dir_name, jpeg1)
        client.upload(dir_name, jpeg2)
        print(f"Uploaded: {jpeg1.name}, {jpeg2.name}")
        zip_bytes = client.download_selected(dir_name, [jpeg1.name, jpeg2.name])
        print(f"Downloaded ZIP: {len(zip_bytes):,} bytes")
        valid = zip_bytes[:2] == b"PK"
        print(f"Valid ZIP: {valid}")
        jpeg1.unlink()
        jpeg2.unlink()


# ---------------------------------------------------------------------------
# Meta subcommands
# ---------------------------------------------------------------------------


@task
def cleanup(c):
    """Remove all _test_* files and directories from the server."""
    with _get_client() as client:
        found = False

        # Remove _test_* files in root
        files = client.list_files()
        test_files = [f.name for f in files if f.name.startswith(TEST_PREFIX)]
        for name in test_files:
            client.delete("", name)
            print(f"Deleted file: {name}")
            found = True

        # Remove _test_* directories (recursive)
        dirs = client.expand()
        test_dirs = [d.name for d in dirs if d.name.startswith(TEST_PREFIX)]
        for name in test_dirs:
            try:
                client.delete_dir(name)
                print(f"Deleted dir: {name}/")
                found = True
            except ActionError as e:
                print(f"Could not delete {name}/: {e.message}")

        if not found:
            print("No test artifacts found.")


@task(name="diagnose-login")
def diagnose_login(c):
    """Probe login responses to identify the failure signature.

    Sends one request with valid credentials and one with a bad password,
    then prints the response details for comparison. Used to determine
    how to detect login failure in HarmonySiteAuth.
    """
    _check_env()
    login_url = os.environ["KCFINDER_LOGIN_URL"]

    def _probe(label, password):
        data = {
            "dbase": "users",
            "action": "login",
            "username": os.environ["KCFINDER_USERNAME"],
            "password": password,
            "nextpage": login_url.rsplit("/", 1)[0],
            "login": "Log In",
            "remember": "1",
        }
        with httpx.Client() as client:
            r = client.post(login_url, data=data, follow_redirects=True)
            print(f"\n{'=' * 60}")
            print(f"  {label}")
            print(f"{'=' * 60}")
            print(f"status:      {r.status_code}")
            print(f"final url:   {r.url}")
            history = [(h.status_code, h.headers.get("location")) for h in r.history]
            print(f"history:     {history}")
            print(f"resp cookies: {list(r.cookies.keys())}")
            print(f"jar cookies:  {dict(client.cookies)}")
            print(f"body len:    {len(r.text)}")
            # Look for login-related indicators in the body
            body_lower = r.text.lower()
            print(f"has 'log in' form: {'name="login"' in body_lower}")
            print(f"has 'password' field: {'name="password"' in body_lower}")
            print(f"has 'logged in': {'logged in' in body_lower}")
            print(f"has 'invalid': {'invalid' in body_lower}")
            print(f"has 'incorrect': {'incorrect' in body_lower}")
            print(f"has 'error': {'error' in body_lower}")
            print(f"has 'welcome': {'welcome' in body_lower}")

    _probe("VALID LOGIN", os.environ["KCFINDER_PASSWORD"])
    _probe("INVALID LOGIN", "definitely-wrong-password-12345")


@task(name="all")
def all_(c):
    """Run all live tests in order, stopping on first failure."""
    tests = [
        auth,
        list_,
        tree,
        expand,
        mkdir,
        list_dir,
        upload,
        download,
        thumb,
        rename,
        delete,
        rename_dir,
        delete_dir,
        copy,
        move,
        bulk_delete,
        download_dir,
        download_sel,
        cleanup,
    ]
    for t in tests:
        name = t.__name__.rstrip("_").replace("_", "-")
        print(f"\n{'=' * 60}")
        print(f"inv live.{name}")
        print("=" * 60)
        t(c)
