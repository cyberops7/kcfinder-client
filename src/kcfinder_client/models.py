from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileInfo:
    """A file entry returned by KCFinder."""

    name: str
    size: int
    mtime: datetime
    is_writable: bool


@dataclass
class DirTree:
    """A directory tree node from KCFinder's init or expand actions."""

    name: str
    is_writable: bool
    has_subdirs: bool
    children: list[DirTree]
    files: list[FileInfo]


@dataclass
class SyncResult:
    """Result of a push sync operation."""

    uploaded: list[str]
    deleted: list[str]
    skipped: list[str]
