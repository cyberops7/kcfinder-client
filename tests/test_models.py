from datetime import datetime

from kcfinder_client.models import DirTree, FileInfo, SyncResult


def test_file_info_construction():
    f = FileInfo(
        name="photo.jpg",
        size=1024,
        mtime=datetime(2026, 1, 15, 10, 30),
        is_writable=True,
    )
    assert f.name == "photo.jpg"
    assert f.size == 1024
    assert f.mtime == datetime(2026, 1, 15, 10, 30)
    assert f.is_writable is True


def test_dir_tree_construction():
    child = DirTree(
        name="sub",
        is_writable=True,
        has_subdirs=False,
        children=[],
        files=[],
    )
    tree = DirTree(
        name="root",
        is_writable=True,
        has_subdirs=True,
        children=[child],
        files=[
            FileInfo(
                name="a.jpg",
                size=100,
                mtime=datetime(2026, 1, 1),
                is_writable=True,
            ),
        ],
    )
    assert tree.name == "root"
    assert tree.has_subdirs is True
    assert len(tree.children) == 1
    assert tree.children[0].name == "sub"
    assert tree.children[0].has_subdirs is False
    assert len(tree.files) == 1


def test_sync_result_construction():
    result = SyncResult(
        uploaded=["a.jpg", "b.jpg"], deleted=["old.jpg"], skipped=["same.jpg"]
    )
    assert len(result.uploaded) == 2
    assert len(result.deleted) == 1
    assert len(result.skipped) == 1
