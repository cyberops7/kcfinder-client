from datetime import datetime

import pytest

from kcfinder_client._core import (
    build_action_url,
    build_form_data,
    build_headers,
    check_action_error,
    parse_file_list,
)
from kcfinder_client.exceptions import ActionError


def test_build_action_url():
    url = build_action_url("https://example.com/browse.php", "chDir", "images")
    assert url == "https://example.com/browse.php?act=chDir&type=images"


def test_build_action_url_no_file_type():
    url = build_action_url("https://example.com/browse.php", "init", None)
    assert url == "https://example.com/browse.php?act=init"


def test_build_headers():
    headers = build_headers("https://example.com/browse.php?bros_config=...")
    assert headers["X-Requested-With"] == "XMLHttpRequest"
    assert headers["Referer"] == "https://example.com/browse.php?bros_config=..."


def test_build_form_data_with_dir():
    data = build_form_data(dir="2026Program")
    assert data == {"dir": "2026Program"}


def test_build_form_data_with_dir_and_file():
    data = build_form_data(dir="2026Program", file="photo.jpg")
    assert data == {"dir": "2026Program", "file": "photo.jpg"}


def test_build_form_data_with_new_name():
    data = build_form_data(dir="2026Program", file="old.jpg", new_name="new.jpg")
    assert data == {"dir": "2026Program", "file": "old.jpg", "newName": "new.jpg"}


def test_build_form_data_with_new_dir():
    data = build_form_data(dir="parent", new_dir="child")
    assert data == {"dir": "parent", "newDir": "child"}


def test_build_form_data_with_files_list():
    data = build_form_data(files=["dir/a.jpg", "dir/b.jpg"])
    assert data == {"files[]": ["dir/a.jpg", "dir/b.jpg"]}


def test_parse_file_list():
    raw = {
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
        "writable": True,
    }
    files = parse_file_list(raw)
    assert len(files) == 2
    assert files[0].name == "photo.jpg"
    assert files[0].size == 1024
    assert isinstance(files[0].mtime, datetime)
    assert files[1].is_writable is False


def test_parse_file_list_empty():
    raw = {"files": [], "writable": True}
    files = parse_file_list(raw)
    assert files == []


def test_check_action_error_with_true():
    # KCFinder returns "true" (as a string) on success for mutating actions
    check_action_error("delete", "true")  # should not raise


def test_check_action_error_with_error_string():
    with pytest.raises(ActionError, match="Access denied"):
        check_action_error("delete", "Access denied")


def test_check_action_error_with_json_error():
    with pytest.raises(ActionError, match="not found"):
        check_action_error("rename", {"error": "not found"})
