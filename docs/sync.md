# Sync Manager

## Table of Contents

- [Async Usage](#async-usage)
- [Sync Usage](#sync-usage)
- [Dry Run](#dry-run)
- [SyncResult](#syncresult)
- [Comparison Strategy](#comparison-strategy)
- [Subdirectories](#subdirectories)

---

The sync manager performs a one-way push sync: it makes a remote KCFinder directory match a local directory. Files that exist locally but not remotely are uploaded; files that exist remotely but not locally are deleted; files that match by name and size are skipped.

Two classes are available:

| Class | Use with |
|-------|----------|
| `SyncManager` | `AsyncKCFinderClient` (async) |
| `SyncManagerSync` | `KCFinderClient` (sync) |

## Async Usage

```python
import asyncio
from pathlib import Path
from kcfinder_client import AsyncKCFinderClient, SyncManager, harmonysite_auth_from_env

async def main():
    auth = harmonysite_auth_from_env()
    async with AsyncKCFinderClient(auth.get_referer(), auth) as client:
        sync = SyncManager(client)
        result = await sync.push(
            remote_dir="images/banners",
            local_dir=Path("./banners"),
        )
        print(f"Uploaded: {result.uploaded}")
        print(f"Deleted:  {result.deleted}")
        print(f"Skipped:  {result.skipped}")

asyncio.run(main())
```

## Sync Usage

```python
from pathlib import Path
from kcfinder_client import KCFinderClient, SyncManagerSync, harmonysite_auth_from_env

auth = harmonysite_auth_from_env()

with KCFinderClient(auth.get_referer(), auth) as client:
    sync = SyncManagerSync(client)
    result = sync.push(
        remote_dir="images/banners",
        local_dir=Path("./banners"),
    )
    print(f"Uploaded: {result.uploaded}")
    print(f"Deleted:  {result.deleted}")
    print(f"Skipped:  {result.skipped}")
```

## Dry Run

Pass `dry_run=True` to compute what would change without actually uploading or deleting anything. This is useful for previewing a sync before applying it.

```python
# Async dry run
result = await sync.push("images/banners", Path("./banners"), dry_run=True)

# Sync dry run
result = sync.push("images/banners", Path("./banners"), dry_run=True)

print("Changes that would be made:")
for name in result.uploaded:
    print(f"  + {name}  (upload)")
for name in result.deleted:
    print(f"  - {name}  (delete)")
for name in result.skipped:
    print(f"  = {name}  (no change)")
```

## SyncResult

The `push()` method always returns a `SyncResult`, whether or not `dry_run` is set.

| Field | Type | Description |
|-------|------|-------------|
| `uploaded` | `list[str]` | Files uploaded (or that would be uploaded in dry run) |
| `deleted` | `list[str]` | Files deleted (or that would be deleted in dry run) |
| `skipped` | `list[str]` | Files with matching name and size — no action taken |

## Comparison Strategy

Files are compared by **name and size**. A file is considered up to date if a remote file with the same name has the same byte size as the local file. If the sizes differ, the local version is uploaded (overwriting the remote copy).

Modification times are not compared. If you update a file's contents without changing its size, the sync will not detect the change. In practice this is rarely an issue for image uploads.

## Subdirectories

`SyncManager` operates on a single flat directory. It does not recurse into subdirectories. To sync a directory tree, call `push()` once per subdirectory:

```python
base_local = Path("./images")
base_remote = "images"

dirs = ["banners", "events", "headshots"]

for d in dirs:
    result = await sync.push(f"{base_remote}/{d}", base_local / d)
    print(f"{d}: +{len(result.uploaded)} -{len(result.deleted)} ={len(result.skipped)}")
```
