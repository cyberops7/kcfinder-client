# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A standalone Python client library for KCFinder, a PHP web file manager. Wraps KCFinder's HTTP action-dispatch API (`browse.php?act=<action>`) into a clean Python interface. Designed to work with any KCFinder instance, with built-in support for the HarmonySite auth extension.

## Build & Development

This is a Python package managed with `uv` and `pyproject.toml`.

```bash
uv sync                    # Install dependencies
uv run pytest              # Run all tests
uv run pytest tests/test_client.py::test_list_files  # Run a single test
uv run pytest -x           # Stop on first failure
uv run ruff check src/     # Lint
uv run ruff format src/    # Format
```

## Package Structure

```
src/kcfinder_client/
├── __init__.py          # Public exports
├── client.py            # KCFinderClient — main entry point
├── auth.py              # Auth strategies (BaseAuth, HarmonySiteAuth, SessionAuth)
├── actions.py           # Action method implementations
├── models.py            # Response dataclasses (FileInfo, DirTree, etc.)
└── exceptions.py        # KCFinderError, AuthError, etc.
```

## Architecture

### KCFinder Protocol

All operations POST to `browse.php?act=<action>` with form data (`dir`, `file`, `files[]`). Key protocol details:

- **Session-based auth**: `PHPSESSID` cookie from login step
- **Required headers**: `Referer` (full browse URL) and `X-Requested-With: XMLHttpRequest`
- **Error handling**: KCFinder returns HTTP 200 even on errors — response body must be inspected
- **File scoping**: The `type=images` param scopes to `images/` under `uploadDir` — this is the filesystem ceiling

### Auth Strategy Pattern

Auth is pluggable via `BaseAuth` subclasses. Each strategy implements `authenticate(session)` and `get_referer()`.

- **`HarmonySiteAuth`**: Logs in via `dbaction.php`, then initializes KCFinder session with `bros_config`/`brosseccheck` query params
- **`SessionAuth`**: For standard KCFinder installs where the session is pre-established

### HarmonySite Extension

HarmonySite's KCFinder fork adds two query params to the initial `browse.php` GET:
- `bros_config`: URL-encoded serialized PHP array (uploadDir, thumbsDir, etc.)
- `brosseccheck`: Static token

This replaces standard session-variable auth — the GET deserializes config into the PHP session.

## Design Principles

- The library handles HTTP/session plumbing only — no credential sourcing, no sync logic
- Consumers pass credentials in; the library doesn't depend on any secret manager
- Primary consumer is the `witnessmusic` project via local path dependency (`uv` source)
