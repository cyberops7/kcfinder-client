"""Exception hierarchy for the KCFinder client."""


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


class FileOperationError(ActionError):
    """File not found, delete failed, etc."""


class DirectoryOperationError(ActionError):
    """Directory not found, creation failed, etc."""


class PermissionDeniedError(ActionError):
    """Operation denied (directory not writable)."""


class UploadError(ActionError):
    """One or more files failed to upload."""
