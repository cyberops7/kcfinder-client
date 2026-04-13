from datetime import datetime

import pytest

from kcfinder_client._core import (
    build_action_url,
    build_form_data,
    build_headers,
    check_action_error,
    parse_dir_tree,
    parse_expand_response,
    parse_file_list,
    prefix_dir,
    prefix_file_paths,
)
from kcfinder_client.exceptions import ActionError
from kcfinder_client.models import DirTree


def test_prefix_dir_with_subdir():
    assert prefix_dir("images", "subfolder") == "images/subfolder"


def test_prefix_dir_with_nested_subdir():
    assert prefix_dir("images", "a/b/c") == "images/a/b/c"


def test_prefix_dir_root():
    assert prefix_dir("images", "") == "images"


def test_prefix_file_paths():
    result = prefix_file_paths("images", ["dir/a.jpg", "dir/b.jpg"])
    assert result == ["images/dir/a.jpg", "images/dir/b.jpg"]


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
    data = build_form_data(dir="images/test_dir")
    assert data == {"dir": "images/test_dir"}


def test_build_form_data_with_dir_and_file():
    data = build_form_data(dir="images/test_dir", file="photo.jpg")
    assert data == {"dir": "images/test_dir", "file": "photo.jpg"}


def test_build_form_data_with_new_name():
    data = build_form_data(dir="images/test_dir", file="old.jpg", new_name="new.jpg")
    assert data == {"dir": "images/test_dir", "file": "old.jpg", "newName": "new.jpg"}


def test_build_form_data_with_new_dir():
    data = build_form_data(dir="images/parent", new_dir="child")
    assert data == {"dir": "images/parent", "newDir": "child"}


def test_build_form_data_with_files_list():
    data = build_form_data(files=["images/dir/a.jpg", "images/dir/b.jpg"])
    assert data == {"files[]": ["images/dir/a.jpg", "images/dir/b.jpg"]}


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
        "dirWritable": True,
    }
    files = parse_file_list(raw)
    assert len(files) == 2
    assert files[0].name == "photo.jpg"
    assert files[0].size == 1024
    assert isinstance(files[0].mtime, datetime)
    assert files[1].is_writable is False


def test_parse_file_list_falls_back_to_dir_writable():
    raw = {
        "files": [
            {
                "name": "photo.jpg",
                "size": 1024,
                "mtime": 1704067200,
                "readable": True,
                # no per-file "writable" key — should fall back to dirWritable
            },
        ],
        "dirWritable": True,
    }
    files = parse_file_list(raw)
    assert files[0].is_writable is True


def test_parse_file_list_empty():
    raw = {"files": [], "dirWritable": True}
    files = parse_file_list(raw)
    assert files == []


def test_check_action_error_with_empty_dict():
    check_action_error("delete", "{}")  # should not raise


def test_check_action_error_with_empty_string():
    check_action_error("delete", "")  # should not raise


def test_check_action_error_with_error_string():
    with pytest.raises(ActionError, match="Access denied"):
        check_action_error("delete", "Access denied")


def test_check_action_error_with_json_error():
    with pytest.raises(ActionError, match="not found"):
        check_action_error("rename", {"error": "not found"})


def test_check_action_error_with_error_list():
    with pytest.raises(ActionError, match="Cannot copy 'a.jpg'; Cannot copy 'b.jpg'"):
        check_action_error(
            "cp_cbd", {"error": ["Cannot copy 'a.jpg'", "Cannot copy 'b.jpg'"]}
        )


def test_check_action_error_rejects_json_array():
    with pytest.raises(ActionError, match="unexpected response"):
        check_action_error("test", '["unexpected", "array"]')


def test_check_action_error_rejects_json_null():
    with pytest.raises(ActionError, match="unexpected response"):
        check_action_error("test", "null")


def test_check_action_error_rejects_json_number():
    with pytest.raises(ActionError, match="unexpected response"):
        check_action_error("test", "42")


def test_check_action_error_rejects_json_string():
    with pytest.raises(ActionError, match="unexpected response"):
        check_action_error("test", '"bare string"')


def test_check_action_error_rejects_non_dict_object():
    with pytest.raises(ActionError, match="unexpected response"):
        check_action_error("test", ["unexpected", "list"])


def test_parse_dir_tree():
    raw = {
        "tree": {
            "name": "images",
            "readable": True,
            "writable": True,
            "removable": False,
            "hasDirs": True,
            "current": True,
            "dirs": [
                {
                    "name": "test_dir",
                    "readable": True,
                    "writable": True,
                    "removable": True,
                    "hasDirs": False,
                },
            ],
        },
        "files": [
            {
                "name": "root.jpg",
                "size": 512,
                "mtime": 1704067200,
                "readable": True,
                "writable": True,
            },
        ],
    }
    tree = parse_dir_tree(raw)
    assert isinstance(tree, DirTree)
    assert tree.name == "images"
    assert tree.is_writable is True
    assert tree.has_subdirs is True
    assert len(tree.children) == 1
    assert tree.children[0].name == "test_dir"
    assert tree.children[0].has_subdirs is False
    assert len(tree.files) == 1
    assert tree.files[0].name == "root.jpg"


def test_parse_expand_response():
    raw = {
        "dirs": [
            {
                "name": "sub1",
                "readable": True,
                "writable": True,
                "removable": True,
                "hasDirs": False,
            },
            {
                "name": "sub2",
                "readable": True,
                "writable": False,
                "removable": False,
                "hasDirs": True,
            },
        ],
    }
    dirs = parse_expand_response(raw)
    assert len(dirs) == 2
    assert isinstance(dirs[0], DirTree)
    assert dirs[0].name == "sub1"
    assert dirs[0].has_subdirs is False
    assert dirs[1].name == "sub2"
    assert dirs[1].has_subdirs is True
    assert dirs[1].is_writable is False


def test_parse_expand_response_empty():
    assert parse_expand_response({"dirs": []}) == []
