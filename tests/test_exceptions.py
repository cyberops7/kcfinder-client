import pytest

from kcfinder_client.exceptions import (
    ActionError,
    AuthError,
    DirectoryOperationError,
    FileOperationError,
    KCFinderError,
    PermissionDeniedError,
    UploadError,
)


@pytest.mark.parametrize(
    "exc_class",
    [
        AuthError,
        ActionError,
        FileOperationError,
        DirectoryOperationError,
        PermissionDeniedError,
        UploadError,
    ],
)
def test_all_exceptions_inherit_from_kcfinder_error(exc_class):
    assert issubclass(exc_class, KCFinderError)


@pytest.mark.parametrize(
    "exc_class",
    [
        FileOperationError,
        DirectoryOperationError,
        PermissionDeniedError,
        UploadError,
    ],
)
def test_specific_errors_inherit_from_action_error(exc_class):
    assert issubclass(exc_class, ActionError)


def test_action_error_carries_action_and_message():
    err = ActionError(action="chDir", message="Directory not found")
    assert err.action == "chDir"
    assert err.message == "Directory not found"
    assert "chDir" in str(err)
    assert "Directory not found" in str(err)
