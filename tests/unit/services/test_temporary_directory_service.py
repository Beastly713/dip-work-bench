"""Tests for temporary-session ownership and cleanup."""

import os

import pytest

from dip_workbench.services import TemporaryDirectoryManager, temporary_directory_service


def test_session_and_child_lifecycle(tmp_path) -> None:  # type: ignore[no-untyped-def]
    manager = TemporaryDirectoryManager(tmp_path)
    session = manager.session_directory
    assert session.parent == tmp_path
    assert session.name.startswith("session-")
    assert (session / ".owner").read_text(encoding="utf-8").startswith("pid=")
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


def test_stale_cleanup_preserves_live_and_non_session_directories(tmp_path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    live = tmp_path / "session-live"
    live.mkdir()
    (live / ".owner").write_text("pid=123\n", encoding="utf-8")
    unrelated = tmp_path / "documents"
    unrelated.mkdir()
    monkeypatch.setattr(temporary_directory_service, "_is_process_running", lambda pid: True)
    manager = TemporaryDirectoryManager(tmp_path)
    try:
        assert live.exists()
        assert unrelated.exists()
    finally:
        manager.cleanup()


@pytest.mark.parametrize("marker", [None, "invalid", "pid=0", "pid=456"])
def test_stale_cleanup_removes_dead_or_invalid_sessions(tmp_path, monkeypatch, marker) -> None:  # type: ignore[no-untyped-def]
    stale = tmp_path / "session-stale"
    stale.mkdir()
    if marker is not None:
        (stale / ".owner").write_text(marker, encoding="utf-8")
    monkeypatch.setattr(temporary_directory_service, "_is_process_running", lambda pid: False)
    manager = TemporaryDirectoryManager(tmp_path)
    try:
        assert not stale.exists()
    finally:
        manager.cleanup()


def test_session_symlinks_are_not_followed(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "session-link"
    link.symlink_to(target, target_is_directory=True)
    manager = TemporaryDirectoryManager(tmp_path)
    try:
        assert link.is_symlink() and target.exists()
    finally:
        manager.cleanup()
