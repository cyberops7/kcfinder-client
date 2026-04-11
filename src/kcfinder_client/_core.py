"""Shared request-building and response-parsing logic for KCFinder clients."""

from datetime import datetime, timezone
from urllib.parse import urlencode

from kcfinder_client.exceptions import ActionError
from kcfinder_client.models import DirTree, FileInfo


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


def _parse_tree_node(
    node: dict, files: list[FileInfo] | None = None
) -> DirTree:
    """Parse a single tree node recursively."""
    return DirTree(
        name=node["name"],
        is_writable=node.get("writable", False),
        has_subdirs=node.get("hasDirs", False),
        children=[
            _parse_tree_node(child) for child in node.get("dirs", [])
        ],
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

    KCFinder returns HTTP 200 even on errors. Success is indicated by the
    string "true" for mutating actions, or valid JSON for query actions.
    Errors are returned as plain strings or as {"error": "message"} dicts.
    """
    if isinstance(response_body, dict):
        if "error" in response_body:
            raise ActionError(
                action=action, message=response_body["error"]
            )
        return  # empty dict or success dict without "error" key
    if isinstance(response_body, str):
        stripped = response_body.strip()
        if stripped.lower() == "true" or stripped == "" or stripped == "{}":
            return
        # Try to parse as JSON — some actions return JSON error strings
        try:
            import json

            parsed = json.loads(stripped)
            if isinstance(parsed, dict) and "error" in parsed:
                raise ActionError(
                    action=action, message=parsed["error"]
                )
            return  # valid JSON without "error" key
        except (json.JSONDecodeError, TypeError):
            pass
        raise ActionError(action=action, message=stripped)
