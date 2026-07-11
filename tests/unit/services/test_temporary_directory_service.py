"""Tests for temporary-session ownership and cleanup."""

import os

import pytest

from dip_workbench.services import TemporaryDirectoryManager


def test_session_and_child_lifecycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = TemporaryDirectoryManager(tmp_path)
    session = manager.session_directory
    assert session.parent == tmp_path
    assert session.name.startswith("session-")
    assert manager.create_subdirectory("exports").is_dir()
    assert manager.create_subdirectory("exports").is_dir()
    manager.cleanup()
    manager.cleanup()
    assert not session.exists()
    assert tmp_path.exists()


def test_sessions_are_unique(tmp_path) -> None:  # type: ignore[no-untyped-def]
    first = TemporaryDirectoryManager(tmp_path)
    second = TemporaryDirectoryManager(tmp_path)
    try:
        assert first.session_directory != second.session_directory
    finally:
        first.cleanup()
        second.cleanup()


def test_context_manager_cleans_session(tmp_path) -> None:  # type: ignore[no-untyped-def]
    with TemporaryDirectoryManager(tmp_path) as manager:
        session = manager.session_directory
    assert not session.exists()


@pytest.mark.parametrize("name", ["", ".", "..", "/absolute", "../escape", "a/b", "a\\b"])
def test_invalid_child_names_are_rejected(tmp_path, name: str) -> None:  # type: ignore[no-untyped-def]
    manager = TemporaryDirectoryManager(tmp_path)
    try:
        with pytest.raises(ValueError, match="Invalid"):
            manager.create_subdirectory(name)
    finally:
        manager.cleanup()


@pytest.mark.skipif(os.sep == "/", reason="alternate separator is covered explicitly")
def test_platform_separator_is_rejected(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = TemporaryDirectoryManager(tmp_path)
    try:
        with pytest.raises(ValueError):
            manager.create_subdirectory(f"a{os.sep}b")
    finally:
        manager.cleanup()
