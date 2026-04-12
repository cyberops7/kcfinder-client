# kcfinder-client

[![CI](https://github.com/cyberops7/kcfinder-client/actions/workflows/ci.yml/badge.svg)](https://github.com/cyberops7/kcfinder-client/actions/workflows/ci.yml)
![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

A Python client library for [KCFinder](https://github.com/sunhater/kcfinder),
a PHP web file manager. Wraps KCFinder's HTTP action-dispatch API into a clean
Python interface with both async and sync clients.

> [!NOTE]
> Designed for and tested against HarmonySite's KCFinder fork.
> May work with other KCFinder instances via `SessionAuth`, but this
> has not been tested.

## Table of Contents

- [Install](#install)
- [Quick Start](#quick-start)
- [Auth from Environment Variables](#auth-from-environment-variables)
- [Sync Files with SyncManager](#sync-files-with-syncmanager)
- [Documentation](#documentation)

## Install

```bash
# uv
uv add kcfinder-client

# pip
pip install kcfinder-client
```

## Quick Start

### Async (recommended)

```python
import asyncio
import os
from kcfinder_client import AsyncKCFinderClient, HarmonySiteAuth

auth = HarmonySiteAuth(
    login_url="https://example.harmonysong.com/dbaction.php",
    browse_url="https://example.harmonysong.com/kcfinder/browse.php",
    username="admin",
    password="secret",
    bros_config=(
        'a:3:{s:9:"uploadDir";s:6:"files/";'
        's:9:"thumbsDir";s:14:"files/.thumbs/";'
        's:9:"uploadURL";s:0:"";}'
    ),
)

async def main():
    browse_url = "https://example.harmonysong.com/kcfinder/browse.php"
    async with AsyncKCFinderClient(browse_url, auth) as client:
        files = await client.list_files("banners")
        for f in files:
            print(f.name, f.size)

asyncio.run(main())
```

### Sync

```python
from kcfinder_client import KCFinderClient, HarmonySiteAuth

auth = HarmonySiteAuth(
    login_url="https://example.harmonysong.com/dbaction.php",
    browse_url="https://example.harmonysong.com/kcfinder/browse.php",
    username="admin",
    password="secret",
    bros_config=(
        'a:3:{s:9:"uploadDir";s:6:"files/";'
        's:9:"thumbsDir";s:14:"files/.thumbs/";'
        's:9:"uploadURL";s:0:"";}'
    ),
)

browse_url = "https://example.harmonysong.com/kcfinder/browse.php"
with KCFinderClient(browse_url, auth) as client:
    files = client.list_files("banners")
    for f in files:
        print(f.name, f.size)
```

## Auth from Environment Variables

Load credentials from the environment rather than hardcoding them:

```bash
export KCFINDER_LOGIN_URL=https://example.harmonysong.com/dbaction.php
export KCFINDER_BROWSE_URL=https://example.harmonysong.com/kcfinder/browse.php
export KCFINDER_USERNAME=admin
export KCFINDER_PASSWORD=secret
export KCFINDER_BROS_CONFIG='a:3:{s:9:"uploadDir";s:6:"files/";s:9:"thumbsDir";s:14:"files/.thumbs/";s:9:"uploadURL";s:0:"";}'
```

```python
import os
from kcfinder_client import AsyncKCFinderClient, harmonysite_auth_from_env
import asyncio

async def main():
    auth = harmonysite_auth_from_env()
    browse_url = os.environ["KCFINDER_BROWSE_URL"]
    async with AsyncKCFinderClient(browse_url, auth) as client:
        files = await client.list_files()
        print(f"Found {len(files)} files")

asyncio.run(main())
```

## Sync Files with SyncManager

One-way push sync to make a remote directory match a local one:

```python
import os
from pathlib import Path
from kcfinder_client import KCFinderClient, SyncManagerSync, harmonysite_auth_from_env

auth = harmonysite_auth_from_env()
browse_url = os.environ["KCFINDER_BROWSE_URL"]

with KCFinderClient(browse_url, auth) as client:
    sync = SyncManagerSync(client)

    # Dry run first to preview changes
    result = sync.push("banners", Path("./banners"), dry_run=True)
    print(f"Would upload: {result.uploaded}")
    print(f"Would delete: {result.deleted}")
    print(f"Would skip:   {result.skipped}")

    # Apply the sync
    result = sync.push("banners", Path("./banners"))
```

## Documentation

- [Auth setup](docs/auth.md) — HarmonySiteAuth, SessionAuth, env vars
- [File operations](docs/files.md) — list, upload, download, delete, rename,
  thumbnails
- [Directory operations](docs/directories.md) — tree, expand, create, rename,
  delete
- [Bulk operations](docs/bulk.md) — copy, move, bulk delete, download selected
- [Sync manager](docs/sync.md) — push sync, dry run, SyncResult
- [Exceptions](docs/exceptions.md) — error handling, exception hierarchy

## License

MIT
