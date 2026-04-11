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

Files in bulk operations are identified by their full relative path from the
KCFinder root, including the directory. For example, a file named `banner.jpg`
inside `images/banners/` is referenced as `"images/banners/banner.jpg"`.

## copy

Copy one or more files to a destination directory. The original files remain
in place.

```python
files = [
    "images/banners/spring.jpg",
    "images/banners/summer.jpg",
]

# Async
await client.copy(files, dest="images/archive/2024")

# Sync
client.copy(files, dest="images/archive/2024")
```

After this call, both `images/banners/spring.jpg` and
`images/archive/2024/spring.jpg` exist.

## move

Move one or more files to a destination directory. The original files are
removed.

```python
files = [
    "images/inbox/photo1.jpg",
    "images/inbox/photo2.jpg",
]

# Async
await client.move(files, dest="images/gallery")

# Sync
client.move(files, dest="images/gallery")
```

After this call, the files exist only in `images/gallery/`.

## bulk_delete

Delete multiple files in a single request.

```python
files = [
    "images/banners/old_spring.jpg",
    "images/banners/old_summer.jpg",
    "images/banners/old_fall.jpg",
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
    dir="images/banners",
    files=["spring.jpg", "summer.jpg"],
)

# Sync
zip_bytes = client.download_selected(
    dir="images/banners",
    files=["spring.jpg", "summer.jpg"],
)

with open("selected.zip", "wb") as f:
    f.write(zip_bytes)
```

> [!NOTE]
> `download_selected` takes bare filenames (e.g., `"spring.jpg"`), not full
> relative paths. This is different from `copy`, `move`, and `bulk_delete`,
> which all use full paths from the KCFinder root.

## Error Handling

```python
from kcfinder_client import ActionError, PermissionDeniedError

try:
    await client.bulk_delete(["images/protected/logo.png"])
except PermissionDeniedError as e:
    print(f"Permission denied: {e.message}")
except ActionError as e:
    print(f"Bulk action failed ({e.action}): {e.message}")
```

---

See also: [File Operations](files.md), [Directory Operations](directories.md)
