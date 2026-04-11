"""One-way push sync: make a remote directory match a local directory."""

from pathlib import Path

from kcfinder_client.async_client import AsyncKCFinderClient
from kcfinder_client.client import KCFinderClient
from kcfinder_client.models import FileInfo, SyncResult


def _compute_sync_actions(
    local_files: dict[str, int],
    remote_files: dict[str, int],
) -> SyncResult:
    """Compare local and remote file sets by name and size."""
    uploaded = []
    skipped = []
    deleted = []

    for name, local_size in sorted(local_files.items()):
        if name in remote_files and remote_files[name] == local_size:
            skipped.append(name)
        else:
            uploaded.append(name)

    for name in sorted(remote_files):
        if name not in local_files:
            deleted.append(name)

    return SyncResult(uploaded=uploaded, deleted=deleted, skipped=skipped)


def _scan_local_dir(local_dir: Path) -> dict[str, int]:
    """Scan a local directory and return a dict of filename -> size."""
    return {f.name: f.stat().st_size for f in local_dir.iterdir() if f.is_file()}


def _remote_file_map(files: list[FileInfo]) -> dict[str, int]:
    """Convert a list of FileInfo to a dict of filename -> size."""
    return {f.name: f.size for f in files}


class SyncManager:
    """Async one-way push sync manager."""

    def __init__(self, client: AsyncKCFinderClient) -> None:
        self._client = client

    async def push(
        self, remote_dir: str, local_dir: Path, *, dry_run: bool = False
    ) -> SyncResult:
        """Sync local directory to remote, making remote match local."""
        remote_files = await self._client.list_files(remote_dir)
        local_map = _scan_local_dir(local_dir)
        remote_map = _remote_file_map(remote_files)
        result = _compute_sync_actions(local_map, remote_map)

        if dry_run:
            return result

        for name in result.uploaded:
            await self._client.upload(remote_dir, local_dir / name)

        for name in result.deleted:
            await self._client.delete(remote_dir, name)

        return result


class SyncManagerSync:
    """Sync (non-async) one-way push sync manager."""

    def __init__(self, client: KCFinderClient) -> None:
        self._client = client

    def push(
        self, remote_dir: str, local_dir: Path, *, dry_run: bool = False
    ) -> SyncResult:
        """Sync local directory to remote, making remote match local."""
        remote_files = self._client.list_files(remote_dir)
        local_map = _scan_local_dir(local_dir)
        remote_map = _remote_file_map(remote_files)
        result = _compute_sync_actions(local_map, remote_map)

        if dry_run:
            return result

        for name in result.uploaded:
            self._client.upload(remote_dir, local_dir / name)

        for name in result.deleted:
            self._client.delete(remote_dir, name)

        return result
