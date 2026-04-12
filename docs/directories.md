# Directory Operations

## Table of Contents

- [get_tree](#get_tree)
- [expand](#expand)
- [create_dir](#create_dir)
- [rename_dir](#rename_dir)
- [delete_dir](#delete_dir)
- [download_dir](#download_dir)
- [Error Handling](#error-handling)

---

All directory operations are available on both `AsyncKCFinderClient` (async)
and `KCFinderClient` (sync). Async examples are shown first, with sync
equivalents immediately after.

Directory paths are relative to the file type root (e.g., `images/`). For
example, to work with `images/banners/`, the `dir` argument is `"banners"`.
The type prefix is added internally by the client. An empty string `""` (or
omitting the argument where optional) refers to the root of the type
directory.

## get_tree

Initialize the browser view and return the root directory node. Returns a
`DirTree` object with the root's immediate subdirectories and files.

> [!NOTE]
> The server returns only one level of subdirectories. To explore deeper
> levels, use [`expand()`](#expand) on individual subdirectories.

```python
# Async
tree = await client.get_tree()

# Sync
tree = client.get_tree()

print(tree.name)        # "images"
print(tree.is_writable) # True

for child in tree.children:
    print(child.name)   # "banners", "thumbnails", ...
```

### DirTree Fields

| Field         | Type              | Description                                                      |
|---------------|-------------------|------------------------------------------------------------------|
| `name`        | `str`             | Directory name                                                   |
| `is_writable` | `bool`            | Whether files can be written here                                |
| `has_subdirs` | `bool`            | Whether the directory contains subdirectories                    |
| `children`    | `list[DirTree]`   | Immediate subdirectories (one level only)                        |
| `files`       | `list[FileInfo]`  | Files in this directory (populated for root node only)           |

## expand

List the subdirectories of a directory. Returns a list of `DirTree` objects
with metadata about each subdirectory.

```python
# Async
subdirs = await client.expand("banners")
subdirs = await client.expand()  # root

# Sync
subdirs = client.expand("banners")
subdirs = client.expand()  # root

for d in subdirs:
    print(d.name, d.has_subdirs, d.is_writable)
```

The `dir` parameter defaults to `""` (root). Returns an empty list if the
directory has no subdirectories.

## create_dir

Create a new subdirectory inside an existing directory.

```python
# Async
await client.create_dir("", "new_gallery")        # in root
await client.create_dir("banners", "2024")         # in banners/

# Sync
client.create_dir("", "new_gallery")
client.create_dir("banners", "2024")
```

| Parameter | Description                                  |
|-----------|----------------------------------------------|
| `dir`     | The parent directory path                    |
| `new_dir` | The name of the new subdirectory to create   |

Raises `DirectoryOperationError` if the directory already exists or the
parent is not writable.

## rename_dir

Rename a directory. The directory is identified by its current path; only
its final component (the name) changes.

```python
# Async
await client.rename_dir("old_gallery", "new_gallery")

# Sync
client.rename_dir("old_gallery", "new_gallery")
```

| Parameter  | Description                                                |
|------------|------------------------------------------------------------|
| `dir`      | The current path to the directory                          |
| `new_name` | The new name (not a full path — just the final component)  |

## delete_dir

Delete a directory and all of its contents recursively, including files
and nested subdirectories.

> [!WARNING]
> This operation is irreversible. All files and subdirectories within the
> target are permanently removed with no trash or undo mechanism.

```python
# Async
await client.delete_dir("old_gallery")

# Sync
client.delete_dir("old_gallery")
```

Raises `DirectoryOperationError` if the directory does not exist or is not
writable.

## download_dir

Download an entire directory as a ZIP archive.

```python
# Async
zip_bytes = await client.download_dir("banners")

# Sync
zip_bytes = client.download_dir("banners")

with open("banners.zip", "wb") as f:
    f.write(zip_bytes)
```

Returns the raw bytes of a ZIP file containing all files in the directory
(and subdirectories, depending on the server configuration).

## Error Handling

```python
from kcfinder_client import DirectoryOperationError, PermissionDeniedError

try:
    await client.delete_dir("protected")
except PermissionDeniedError as e:
    print(f"No permission to delete: {e.message}")
except DirectoryOperationError as e:
    print(f"Directory operation failed ({e.action}): {e.message}")
```

---

See also: [File Operations](files.md), [Exceptions](exceptions.md)
