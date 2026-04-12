"""Shared request-building and response-parsing logic for KCFinder clients."""

import json
from datetime import datetime, timezone
from urllib.parse import urlencode

from kcfinder_client.exceptions import ActionError
from kcfinder_client.models import DirTree, FileInfo


def prefix_dir(file_type: str, dir: str) -> str:
    """Build a type-prefixed directory path for KCFinder.

    KCFinder expects all ``dir`` parameters to start with the file type
    (e.g., ``images/subfolder``).  The PHP constructor validates this prefix
    via ``checkInputDir`` and strips it before resolving the filesystem path.
    """
    if dir:
        return f"{file_type}/{dir}"
    return file_type


def prefix_file_paths(file_type: str, paths: list[str]) -> list[str]:
    """Prepend the file type to each path for bulk clipboard operations.

    Bulk actions (cp_cbd, mv_cbd, rm_cbd) expect each file entry to be a
    type-prefixed path like ``images/subfolder/photo.jpg``.
    """
    return [f"{file_type}/{p}" for p in paths]


def build_action_url(browse_url: str, action: str, file_type: str | None) -> str:
    """Build the full URL for a KCFinder action."""
    params: dict[str, str] = {"act": action}
    if file_type is not None:
        params["type"] = file_type
    return f"{browse_url}?{urlencode(params)}"


def build_headers(referer: str) -> dict[str, str]:
    """Build the required headers for a KCFinder request."""
    return {
        "X-Requested-With": "XMLHttpRequest",
        "Referer": referer,
    }


def build_form_data(
    *,
    dir: str | None = None,
    file: str | None = None,
    new_name: str | None = None,
    new_dir: str | None = None,
    files: list[str] | None = None,
) -> dict[str, str | list[str]]:
    """Build the form data dict for a KCFinder action."""
    data: dict[str, str | list[str]] = {}
    if dir is not None:
        data["dir"] = dir
    if file is not None:
        data["file"] = file
    if new_name is not None:
        data["newName"] = new_name
    if new_dir is not None:
        data["newDir"] = new_dir
    if files is not None:
        data["files[]"] = files
    return data


def parse_file_list(raw: dict) -> list[FileInfo]:
    """Parse the response from a chDir action into FileInfo objects."""
    writable = raw.get("writable", False)
    return [
        FileInfo(
            name=f["name"],
            size=f["size"],
            mtime=datetime.fromtimestamp(f["mtime"], tz=timezone.utc),  # noqa: UP017
            is_writable=f.get("writable", writable),
        )
        for f in raw.get("files", [])
    ]


def parse_dir_tree(raw: dict) -> DirTree:
    """Parse a KCFinder init response into a DirTree.

    The init response wraps the tree in a "tree" key at the top level.
    Files are siblings of "tree", not nested under it.
    """
    tree = raw.get("tree", raw)
    files = parse_file_list(raw) if "files" in raw else []
    return _parse_tree_node(tree, files)


def _parse_tree_node(node: dict, files: list[FileInfo] | None = None) -> DirTree:
    """Parse a single tree node recursively."""
    return DirTree(
        name=node["name"],
        is_writable=node.get("writable", False),
        has_subdirs=node.get("hasDirs", False),
        children=[_parse_tree_node(child) for child in node.get("dirs", [])],
        files=files if files is not None else [],
    )


def check_upload_response(response_text: str) -> None:
    """Check an upload response for errors.

    Upload responses differ from other actions: success returns the
    uploaded filename prefixed with "/" (e.g., "/photo.jpg"). Errors
    return "filename: error message". Multiple files produce one line
    per file.
    """
    for line in response_text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("/"):
            continue  # success — uploaded filename
        raise ActionError(action="upload", message=line)


def check_action_error(action: str, response_body: str | dict) -> None:
    """Check a KCFinder response body for errors and raise if found.

    KCFinder returns HTTP 200 even on errors.  Successful mutating actions
    return the string ``{}`` (PHP echoes ``{}`` when the handler returns
    ``true``).  Query actions return valid JSON.  Errors come as plain
    strings or ``{"error": "message"}`` dicts.  Bulk clipboard actions
    return ``{"error": ["msg1", "msg2"]}`` with a list of per-file errors.
    """
    if isinstance(response_body, dict):
        if "error" in response_body:
            err = response_body["error"]
            msg = "; ".join(err) if isinstance(err, list) else str(err)
            raise ActionError(action=action, message=msg)
        return  # empty dict or success dict without "error" key
    if isinstance(response_body, str):
        stripped = response_body.strip()
        if stripped == "" or stripped == "{}":
            return
        # Try to parse as JSON — some actions return JSON error strings
        try:
            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and "error" in parsed:
                err = parsed["error"]
                msg = "; ".join(err) if isinstance(err, list) else str(err)
                raise ActionError(action=action, message=msg)
            return  # valid JSON without "error" key
        except json.JSONDecodeError:
            pass
        raise ActionError(action=action, message=stripped)


def parse_expand_response(raw: dict) -> list[DirTree]:
    """Parse a KCFinder expand response into a list of DirTree nodes.

    The expand action returns ``{"dirs": [{name, writable, hasDirs, ...}]}``.
    Each entry describes a direct subdirectory (no nested children).
    """
    return [
        DirTree(
            name=d["name"],
            is_writable=d.get("writable", False),
            has_subdirs=d.get("hasDirs", False),
            children=[],
            files=[],
        )
        for d in raw.get("dirs", [])
    ]
