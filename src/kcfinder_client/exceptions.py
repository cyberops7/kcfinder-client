"""Exception hierarchy for the KCFinder client."""

import re


class KCFinderError(Exception):
    """Base exception for all KCFinder errors."""


class AuthError(KCFinderError):
    """Authentication or session initialization failed."""


class ActionError(KCFinderError):
    """A KCFinder action returned an error in the response body."""

    def __init__(self, action: str, message: str) -> None:
        self.action = action
        self.message = message
        super().__init__(f"{action}: {message}")


class DirectoryOperationError(ActionError):
    """Directory creation, rename, or deletion failed."""


class FileOperationError(ActionError):
    """File not found, cannot copy/move/delete, name conflict, etc."""


class PermissionDeniedError(ActionError):
    """Operation denied due to insufficient permissions."""


class UploadError(ActionError):
    """One or more files failed to upload."""


# ---------------------------------------------------------------------------
# Error message classification
# ---------------------------------------------------------------------------
# Patterns derived from the KCFinder PHP source (sunhater/kcfinder).
# Order matters within each group; groups are checked permission → directory
# → file → upload, with ActionError as the fallback.
# ---------------------------------------------------------------------------

_PERMISSION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"don't have permissions", re.IGNORECASE),
    re.compile(r"Cannot access or write to upload folder", re.IGNORECASE),
]

_DIR_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"Cannot (create .+ |rename the |delete the )folder", re.IGNORECASE),
    re.compile(r"enter new folder name", re.IGNORECASE),
    re.compile(r"characters in folder name", re.IGNORECASE),
    re.compile(r"Folder name shouldn't begins with", re.IGNORECASE),
    re.compile(r"Failed to delete .+ files/folders", re.IGNORECASE),
]

_FILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"does not exist", re.IGNORECASE),
    re.compile(r"Cannot (read|copy|move|delete) '", re.IGNORECASE),
    re.compile(r"cannot rename the extension", re.IGNORECASE),
    re.compile(r"already exists", re.IGNORECASE),
    re.compile(r"enter new file name", re.IGNORECASE),
    re.compile(r"characters in file name", re.IGNORECASE),
    re.compile(r"File name shouldn't begins with", re.IGNORECASE),
    re.compile(r"Denied file extension", re.IGNORECASE),
]

_UPLOAD_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"uploaded file", re.IGNORECASE),
    re.compile(r"No file was uploaded", re.IGNORECASE),
    re.compile(r"Missing a temporary folder", re.IGNORECASE),
    re.compile(r"Failed to write file", re.IGNORECASE),
    re.compile(r"Cannot move uploaded file", re.IGNORECASE),
    re.compile(r"too big and/or cannot be resized", re.IGNORECASE),
    re.compile(r"Non-existing directory type", re.IGNORECASE),
]


def classify_error(action: str, message: str) -> ActionError:
    """Return the most specific ActionError subclass for a KCFinder error message."""
    for pattern in _PERMISSION_PATTERNS:
        if pattern.search(message):
            return PermissionDeniedError(action=action, message=message)
    for pattern in _DIR_PATTERNS:
        if pattern.search(message):
            return DirectoryOperationError(action=action, message=message)
    for pattern in _FILE_PATTERNS:
        if pattern.search(message):
            return FileOperationError(action=action, message=message)
    for pattern in _UPLOAD_PATTERNS:
        if pattern.search(message):
            return UploadError(action=action, message=message)
    return ActionError(action=action, message=message)
