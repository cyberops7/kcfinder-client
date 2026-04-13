# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

A standalone Python client library for KCFinder, a PHP web file manager.
Wraps KCFinder's HTTP action-dispatch API (`browse.php?act=<action>`) into a
clean Python interface with both sync and async clients. Designed to work with
any KCFinder instance, with built-in support for the HarmonySite auth
extension.

## Build & Development

Python package managed with `uv` and `pyproject.toml`. Requires Python 3.14+.

```bash
uv sync                    # Install dependencies
uv run pytest              # Run all tests
uv run pytest tests/test_client.py::test_list_files  # Run a single test
uv run pytest -x           # Stop on first failure
```

### Invoke Tasks

```bash
inv test       # Run pytest
inv lint       # Run ruff linter
inv format     # Run ruff formatter
inv tc         # Run pyrefly type checker
inv mdlint     # Run markdownlint on docs (requires Docker)
inv check      # Lint + format + typecheck + mdlint (run this frequently)
inv scan       # Security scan (bandit + pip-audit)
inv build      # Build package with uv
```

### Live Testing

Atomic live tests for every client method against a real KCFinder server.
Requires env vars (see `live.py` for details). Credentials are loaded via
`python-dotenv` from a `.env` file.

```bash
inv live.auth          # Authenticate, confirm session
inv live.list          # List files in root (--dir for subdirs)
inv live.tree          # Root directory node with immediate subdirs
inv live.expand        # List subdirectories (--dir for subdirs)
inv live.upload        # Upload a test JPEG
inv live.download      # Upload, download, verify bytes match
inv live.thumb         # Upload image, get thumbnail
inv live.rename        # Upload, rename, verify
inv live.delete        # Upload, delete, verify gone
inv live.mkdir         # Create test directory
inv live.list-dir      # Create dir with file, list contents
inv live.rename-dir    # Create dir, rename, verify
inv live.delete-dir    # Create dir, delete, verify gone
inv live.copy          # Upload, copy to dest dir
inv live.move          # Upload, move to dest dir
inv live.bulk-delete   # Upload 2 files, bulk delete
inv live.download-dir  # Download dir as ZIP
inv live.download-sel  # Download selected files as ZIP
inv live.cleanup       # Remove all _test_* artifacts
inv live.all           # Run all tests in order
```

## Package Structure

```text
src/kcfinder_client/
├── __init__.py          # Public exports
├── _core.py             # Shared request building, response parsing, error checking
├── async_client.py      # AsyncKCFinderClient (httpx.AsyncClient)
├── client.py            # KCFinderClient (httpx.Client, sync)
├── auth.py              # BaseAuth, HarmonySiteAuth, SessionAuth, harmonysite_auth_from_env
├── models.py            # FileInfo, DirTree, SyncResult dataclasses
├── exceptions.py        # KCFinderError hierarchy
└── sync.py              # SyncManager, SyncManagerSync (one-way push)

live.py                  # Live test tasks (inv live.*)
tasks.py                 # Invoke task definitions + live namespace registration
```

## Architecture

### Dual Client Pattern

Two client classes share core logic via private helpers in `_core.py`:

- **`AsyncKCFinderClient`** — async methods, uses `httpx.AsyncClient`
- **`KCFinderClient`** — sync methods, uses `httpx.Client`

Both are context managers that handle auth and cleanup. All request building,
response parsing, and error detection lives in `_core.py`.

### KCFinder Protocol

All operations POST to `browse.php?act=<action>` with form data (`dir`,
`file`, `files[]`). Key protocol details:

- **Session-based auth**: `PHPSESSID` cookie from login step
- **Required headers**: `Referer` (full browse URL) and
  `X-Requested-With: XMLHttpRequest`
- **Auth query params**: HarmonySite's fork requires `bros_config` and
  `brosseccheck` as query params on every request, not just the session init.
  This is handled by `BaseAuth.get_query_params()`.
- **Dir param type prefix**: All `dir` params must include the file type
  prefix (e.g., `images/subfolder`). The client handles this internally via
  `prefix_dir()` — callers pass bare paths like `"subfolder"`.
- **Error handling**: KCFinder returns HTTP 200 even on errors — response body
  must be inspected. Success is `{}` for mutating actions, JSON for queries.
  Bulk action errors are arrays joined with `"; "`.
- **Thumbnail via GET**: `act=thumb` uses GET query params (dir, file), not
  POST form data.
- **File scoping**: The `type=images` param scopes to `images/` under
  `uploadDir` — this is the filesystem ceiling

### Auth Strategy Pattern

Auth is pluggable via `BaseAuth` subclasses. Each strategy implements
`authenticate(session)`, `authenticate_sync(session)`, `get_referer()`, and
optionally `get_query_params()`.

- **`HarmonySiteAuth`**: Logs in via `dbaction.php`, then initializes KCFinder
  session with `bros_config`/`brosseccheck` query params. These params are
  also sent on every subsequent request via `get_query_params()`.
- **`SessionAuth`**: For standard KCFinder installs where the session is
  pre-established
- **`harmonysite_auth_from_env()`**: Factory that reads credentials from
  environment variables

### SyncManager

One-way push sync on top of the client. Compares local vs remote files by
name + size. Supports dry run. Available in both async (`SyncManager`) and
sync (`SyncManagerSync`) variants.

## Releasing

Published to [PyPI](https://pypi.org/project/kcfinder-client/) via trusted
publishing (OIDC). No API tokens — auth is configured in PyPI account settings.

1. Bump `version` in `pyproject.toml`
2. Commit and push to main
3. Create a GitHub release with tag (e.g., `v0.2.0`)
4. `.github/workflows/publish.yml` triggers automatically — re-runs all CI
   checks, builds with `uv build`, publishes via `pypa/gh-action-pypi-publish`

CI (`.github/workflows/ci.yml`) runs lint, format check, typecheck, and tests
on every push and PR to main.

## Design Principles

- Dual sync/async clients sharing logic via `_core.py` (same pattern as
  anthropic/openai SDKs)
- Auth classes take explicit args — no credential sourcing; consumers handle
  that
- `harmonysite_auth_from_env()` factory for deployment contexts (n8n, CI)
- Primary consumer is the `witnessmusic` project (`uv add kcfinder-client`)
