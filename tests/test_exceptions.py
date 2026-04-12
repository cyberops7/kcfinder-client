import pytest

from kcfinder_client.exceptions import (
    ActionError,
    AuthError,
    DirectoryOperationError,
    FileOperationError,
    KCFinderError,
    PermissionDeniedError,
    UploadError,
    classify_error,
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


# ---------------------------------------------------------------------------
# classify_error tests — one per pattern group, plus fallback
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "message",
    [
        "You don't have permissions to browse server.",
        "You don't have permissions to upload files.",
        "Cannot access or write to upload folder.",
    ],
)
def test_classify_error_permission(message):
    err = classify_error("test", message)
    assert isinstance(err, PermissionDeniedError)


@pytest.mark.parametrize(
    "message",
    [
        "Cannot create myfolder folder.",
        "Cannot rename the folder.",
        "Cannot delete the folder.",
        "Please enter new folder name.",
        "Unallowable characters in folder name.",
        "Folder name shouldn't begins with '.'",
        "Failed to delete 3 files/folders.",
    ],
)
def test_classify_error_directory(message):
    err = classify_error("newDir", message)
    assert isinstance(err, DirectoryOperationError)


@pytest.mark.parametrize(
    "message",
    [
        "The file 'photo.jpg' does not exist.",
        "Cannot read 'photo.jpg'.",
        "Cannot copy 'photo.jpg'.",
        "Cannot move 'photo.jpg'.",
        "Cannot delete 'photo.jpg'.",
        "You cannot rename the extension of files!",
        "A file or folder with that name already exists.",
        "Please enter new file name.",
        "Unallowable characters in file name.",
        "File name shouldn't begins with '.'",
        "Denied file extension.",
    ],
)
def test_classify_error_file(message):
    err = classify_error("rename", message)
    assert isinstance(err, FileOperationError)


@pytest.mark.parametrize(
    "message",
    [
        "The uploaded file exceeds 2M bytes.",
        "The uploaded file was only partially uploaded.",
        "No file was uploaded.",
        "Missing a temporary folder.",
        "Failed to write file.",
        "Cannot move uploaded file to target folder.",
        "The image is too big and/or cannot be resized.",
        "Non-existing directory type.",
    ],
)
def test_classify_error_upload(message):
    err = classify_error("upload", message)
    assert isinstance(err, UploadError)


def test_classify_error_unknown_falls_back_to_action_error():
    err = classify_error("delete", "Unknown error.")
    assert type(err) is ActionError


def test_classify_error_preserves_action_and_message():
    err = classify_error("rename", "A file or folder with that name already exists.")
    assert err.action == "rename"
    assert err.message == "A file or folder with that name already exists."
