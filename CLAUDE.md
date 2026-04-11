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
inv check      # Lint + format check + typecheck (run this frequently)
inv scan       # Security scan (bandit + pip-audit)
inv build      # Build package with uv
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
- **Error handling**: KCFinder returns HTTP 200 even on errors — response body
  must be inspected
- **File scoping**: The `type=images` param scopes to `images/` under
  `uploadDir` — this is the filesystem ceiling

### Auth Strategy Pattern

Auth is pluggable via `BaseAuth` subclasses. Each strategy implements
`authenticate(session)`, `authenticate_sync(session)`, and `get_referer()`.

- **`HarmonySiteAuth`**: Logs in via `dbaction.php`, then initializes KCFinder
  session with `bros_config`/`brosseccheck` query params
- **`SessionAuth`**: For standard KCFinder installs where the session is
  pre-established
- **`harmonysite_auth_from_env()`**: Factory that reads credentials from
  environment variables

### SyncManager

One-way push sync on top of the client. Compares local vs remote files by
name + size. Supports dry run. Available in both async (`SyncManager`) and
sync (`SyncManagerSync`) variants.

## Design Principles

- Dual sync/async clients sharing logic via `_core.py` (same pattern as
  anthropic/openai SDKs)
- Auth classes take explicit args — no credential sourcing; consumers handle
  that
- `harmonysite_auth_from_env()` factory for deployment contexts (n8n, CI)
- Primary consumer is the `witnessmusic` project via local path dependency
  (`uv` source)
