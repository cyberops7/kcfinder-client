# Bulk Operations

## Table of Contents

- [copy](#copy)
- [move](#move)
- [bulk_delete](#bulk_delete)
- [download_selected](#download_selected)
- [Error Handling](#error-handling)

---

Bulk operations act on multiple files at once. They are available on both
`AsyncKCFinderClient` (async) and `KCFinderClient` (sync).

Files in `copy`, `move`, and `bulk_delete` are identified by their path
relative to the file type root. For example, a file named `banner.jpg`
inside `banners/` is referenced as `"banners/banner.jpg"`. The type prefix
(e.g., `images/`) is added internally by the client.

## copy

Copy one or more files to a destination directory. The original files remain
in place. Accepts a single path string or a list.

```python
# Single file
await client.copy("banners/spring.jpg", dest="archive/2024")
client.copy("banners/spring.jpg", dest="archive/2024")

# Multiple files
files = [
    "banners/spring.jpg",
    "banners/summer.jpg",
]
await client.copy(files, dest="archive/2024")
client.copy(files, dest="archive/2024")
```

After this call, both `banners/spring.jpg` and `archive/2024/spring.jpg`
exist.

## move

Move one or more files to a destination directory. The original files are
removed. Accepts a single path string or a list.

```python
# Single file
await client.move("inbox/photo1.jpg", dest="gallery")
client.move("inbox/photo1.jpg", dest="gallery")

# Multiple files
files = [
    "inbox/photo1.jpg",
    "inbox/photo2.jpg",
]
await client.move(files, dest="gallery")
client.move(files, dest="gallery")
```

After this call, the files exist only in `gallery/`.

## bulk_delete

Delete multiple files in a single request.

```python
files = [
    "banners/old_spring.jpg",
    "banners/old_summer.jpg",
    "banners/old_fall.jpg",
]

# Async
await client.bulk_delete(files)

# Sync
client.bulk_delete(files)
```

This is more efficient than calling `delete()` in a loop for large numbers of
files. All files are deleted in one server round-trip.

## download_selected

Download a set of files from a single directory as a ZIP archive.

```python
# Async
zip_bytes = await client.download_selected(
    dir="banners",
    files=["spring.jpg", "summer.jpg"],
)

# Sync
zip_bytes = client.download_selected(
    dir="banners",
    files=["spring.jpg", "summer.jpg"],
)

with open("selected.zip", "wb") as f:
    f.write(zip_bytes)
```

> [!NOTE]
> `download_selected` takes bare filenames (e.g., `"spring.jpg"`), not
> relative paths. This is different from `copy`, `move`, and `bulk_delete`,
> which take paths that include the directory (e.g., `"banners/spring.jpg"`).

## Error Handling

Bulk operations return error details for individual files that failed. These
are joined into a single error message.

```python
from kcfinder_client import ActionError, PermissionDeniedError

try:
    await client.bulk_delete(["protected/logo.png"])
except PermissionDeniedError as e:
    print(f"Permission denied: {e.message}")
except ActionError as e:
    # Bulk errors may contain multiple messages joined by "; "
    print(f"Bulk action failed ({e.action}): {e.message}")
```

---

See also: [File Operations](files.md), [Directory Operations](directories.md)
