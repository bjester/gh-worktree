import os
import pytest
from gh_worktree.utils import find_up


def test_find_up_success(tmp_path):
    # Create a directory structure:
    # root/
    #   target_file
    #   subdir/
    #     subsubdir/

    root = tmp_path
    (root / "target_file").touch()
    subdir = root / "subdir"
    subdir.mkdir()
    subsubdir = subdir / "subsubdir"
    subsubdir.mkdir()

    # Test finding from subsubdir
    found_path = find_up("target_file", str(subsubdir))
    assert found_path == str(root / "target_file")

    # Test finding from root
    found_path = find_up("target_file", str(root))
    assert found_path == str(root / "target_file")


def test_find_up_failure(tmp_path):
    # Create a directory structure without the target file
    root = tmp_path
    subdir = root / "subdir"
    subdir.mkdir()

    with pytest.raises(RuntimeError, match="Could not find non_existent_file"):
        find_up("non_existent_file", str(subdir))
