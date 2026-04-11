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

All directory operations are available on both `AsyncKCFinderClient` (async) and `KCFinderClient` (sync). Async examples are shown first, with sync equivalents immediately after.

Directory paths are relative to the configured `uploadDir`. For example, if `uploadDir` is `files/`, then `"images/banners"` refers to `files/images/banners/` on the server.

## get_tree

Get the full directory tree starting from the KCFinder root. Returns a `DirTree` object.

```python
# Async
tree = await client.get_tree()

# Sync
tree = client.get_tree()

print(tree.name)        # "images"
print(tree.path)        # "/files/images/"
print(tree.is_writable) # True

for child in tree.children:
    print(child.name)   # "banners", "thumbnails", ...
```

### DirTree Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Directory name |
| `path` | `str` | Full server path |
| `is_writable` | `bool` | Whether files can be written here |
| `children` | `list[DirTree]` | Immediate subdirectories (recursive) |
| `files` | `list[FileInfo]` | Files in this directory (may be empty for tree-only responses) |

### Traversing the Tree

```python
def print_tree(node: DirTree, indent: int = 0) -> None:
    prefix = "  " * indent
    print(f"{prefix}{node.name}/ {'(read-only)' if not node.is_writable else ''}")
    for child in node.children:
        print_tree(child, indent + 1)

tree = await client.get_tree()
print_tree(tree)
```

## expand

Get the names of immediate subdirectories within a directory. Lighter than `get_tree()` when you only need one level.

```python
# Async
subdirs = await client.expand("images")

# Sync
subdirs = client.expand("images")

print(subdirs)  # ["banners", "events", "headshots"]
```

Returns a `list[str]` of directory names (not full paths).

## create_dir

Create a new subdirectory inside an existing directory.

```python
# Async
await client.create_dir("images", "new_gallery")

# Sync
client.create_dir("images", "new_gallery")
```

Parameters:
- `dir` — the parent directory path
- `new_dir` — the name of the new subdirectory to create

Raises `DirectoryOperationError` if the directory already exists or the parent is not writable.

## rename_dir

Rename a directory. The directory is identified by its current path; only its final component (the name) changes.

```python
# Async
await client.rename_dir("images/old_gallery", "new_gallery")

# Sync
client.rename_dir("images/old_gallery", "new_gallery")
```

Parameters:
- `dir` — the current full path to the directory
- `new_name` — the new name (not a full path, just the final component)

After this call, `images/old_gallery` becomes `images/new_gallery`.

## delete_dir

Delete a directory and all of its contents recursively.

```python
# Async
await client.delete_dir("images/old_gallery")

# Sync
client.delete_dir("images/old_gallery")
```

This operation is irreversible. Raises `DirectoryOperationError` if the directory does not exist or is not writable.

## download_dir

Download an entire directory as a ZIP archive.

```python
# Async
zip_bytes = await client.download_dir("images/banners")

# Sync
zip_bytes = client.download_dir("images/banners")

with open("banners.zip", "wb") as f:
    f.write(zip_bytes)
```

Returns the raw bytes of a ZIP file containing all files in the directory (and subdirectories, depending on the server configuration).

## Error Handling

```python
from kcfinder_client import DirectoryOperationError, PermissionDeniedError

try:
    await client.delete_dir("images/protected")
except PermissionDeniedError as e:
    print(f"No permission to delete: {e.message}")
except DirectoryOperationError as e:
    print(f"Directory operation failed ({e.action}): {e.message}")
```

See [exceptions.md](exceptions.md) for the full error hierarchy.
