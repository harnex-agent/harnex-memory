import pytest

from harnex_memory.core.paths import PathSafetyError, ensure_inside_project, resolve_project_root


def test_ensure_inside_project_allows_relative_child(tmp_path):
    assert ensure_inside_project(tmp_path, "nested/file.md") == tmp_path / "nested/file.md"


def test_ensure_inside_project_blocks_parent_escape(tmp_path):
    with pytest.raises(PathSafetyError):
        ensure_inside_project(tmp_path, "../outside.md")


def test_resolve_project_root_requires_directory(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("x", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        resolve_project_root(file_path)
