# Exceptions

## Table of Contents

- [Why KCFinder Returns HTTP 200 for Errors](#why-kcfinder-returns-http-200-for-errors)
- [Exception Hierarchy](#exception-hierarchy)
- [Exception Reference](#exception-reference)
  - [KCFinderError](#kcfindererror)
  - [AuthError](#autherror)
  - [ActionError](#actionerror)
  - [FileOperationError](#fileoperationerror)
  - [DirectoryOperationError](#directoryoperationerror)
  - [PermissionDeniedError](#permissiondeniederror)
  - [UploadError](#uploaderror)
- [Catching Patterns](#catching-patterns)

---

## Why KCFinder Returns HTTP 200 for Errors

> [!IMPORTANT]
> KCFinder always returns HTTP 200, even when an operation fails. Do not check the HTTP status code — this library inspects every response body and raises a Python exception when an error is detected.

Errors are communicated in the response body — either as a plain error string or as a JSON object like `{"error": "File not found"}`.

## Exception Hierarchy

```
KCFinderError
├── AuthError
└── ActionError
    ├── FileOperationError
    ├── DirectoryOperationError
    ├── PermissionDeniedError
    └── UploadError
```

All exceptions are importable directly from `kcfinder_client`:

```python
from kcfinder_client import (
    KCFinderError,
    AuthError,
    ActionError,
    FileOperationError,
    DirectoryOperationError,
    PermissionDeniedError,
    UploadError,
)
```

## Exception Reference

### KCFinderError

Base class for all exceptions in this library. Catch this to handle any error from the library.

```python
try:
    await client.upload("images", Path("photo.jpg"))
except KCFinderError as e:
    print(f"Something went wrong: {e}")
```

### AuthError

Raised when authentication fails — either the login request returned a non-200 status, or the KCFinder session initialization failed.

```python
from kcfinder_client import AsyncKCFinderClient, HarmonySiteAuth, AuthError

auth = HarmonySiteAuth(...)

try:
    async with AsyncKCFinderClient(auth.get_referer(), auth) as client:
        ...
except AuthError as e:
    print(f"Could not log in: {e}")
```

Common causes:
- Wrong username or password
- Login URL or browse URL is incorrect
- Server is unreachable

### ActionError

Raised when a KCFinder action returns an error in the response body. This is the base class for all action-specific errors.

#### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `action` | `str` | The KCFinder action name (e.g., `"delete"`, `"upload"`) |
| `message` | `str` | The error message from the server |

```python
from kcfinder_client import ActionError

try:
    await client.delete("images", "missing.jpg")
except ActionError as e:
    print(f"Action '{e.action}' failed: {e.message}")
```

### FileOperationError

A subclass of `ActionError` raised for file-level failures: file not found, delete failed, rename conflict, etc.

```python
from kcfinder_client import FileOperationError

try:
    await client.rename("images", "old.jpg", "new.jpg")
except FileOperationError as e:
    print(f"Rename failed: {e.message}")
```

### DirectoryOperationError

A subclass of `ActionError` raised for directory-level failures: directory not found, creation failed, rename conflict, etc.

```python
from kcfinder_client import DirectoryOperationError

try:
    await client.create_dir("images", "already_exists")
except DirectoryOperationError as e:
    print(f"Could not create directory: {e.message}")
```

### PermissionDeniedError

A subclass of `ActionError` raised when a write operation is attempted on a directory that KCFinder has marked as read-only.

```python
from kcfinder_client import PermissionDeniedError

try:
    await client.upload("images/protected", Path("photo.jpg"))
except PermissionDeniedError as e:
    print(f"Directory is not writable: {e.message}")
```

### UploadError

A subclass of `ActionError` raised when one or more files fail to upload. The `message` attribute contains the server's error detail.

```python
from kcfinder_client import UploadError

try:
    await client.upload("images", Path("too_large.jpg"))
except UploadError as e:
    print(f"Upload rejected: {e.message}")
```

Common causes:
- File type not allowed by KCFinder configuration
- File size exceeds the server limit
- Destination directory is not writable

## Catching Patterns

### Broad catch (any library error)

```python
from kcfinder_client import KCFinderError

try:
    result = await sync.push("images/banners", Path("./banners"))
except KCFinderError as e:
    print(f"KCFinder error: {e}")
```

### Specific catch (permission vs. other errors)

```python
from kcfinder_client import PermissionDeniedError, ActionError, AuthError

try:
    await client.delete("images/banners", "logo.png")
except AuthError:
    print("Session expired — re-authenticate and retry")
except PermissionDeniedError as e:
    print(f"Not allowed: {e.message}")
except ActionError as e:
    print(f"Operation failed ({e.action}): {e.message}")
```

<details>
<summary><strong>Re-raising after logging</strong></summary>

```python
import logging
from kcfinder_client import KCFinderError

log = logging.getLogger(__name__)

try:
    await client.upload("images", Path("photo.jpg"))
except KCFinderError:
    log.exception("Upload failed")
    raise
```

</details>

---

See also: [File Operations](files.md), [Directory Operations](directories.md)
