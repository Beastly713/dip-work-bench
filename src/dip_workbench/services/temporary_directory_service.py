"""Safe temporary-session directory management."""

import os
import shutil
import tempfile
from pathlib import Path
from types import TracebackType


def _is_process_running(pid: int) -> bool:
    if pid == os.getpid():
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class TemporaryDirectoryManager:
    """Own one unique temporary directory for an application session."""

    def __init__(self, base_directory: Path | None = None) -> None:
        self._base_directory = base_directory or Path(tempfile.gettempdir()) / "dip-workbench"
        self._base_directory.mkdir(parents=True, exist_ok=True)
        self._cleanup_abandoned_sessions()
        self._session_directory = Path(
            tempfile.mkdtemp(prefix="session-", dir=self._base_directory)
        )
        (self._session_directory / ".owner").write_text(f"pid={os.getpid()}\n", encoding="utf-8")

    @property
    def session_directory(self) -> Path:
        """Return the directory owned by this manager."""
        return self._session_directory

    def create_subdirectory(self, name: str) -> Path:
        """Create a safe, directly nested named directory."""
        candidate = Path(name)
        if (
            not name
            or name in {".", ".."}
            or candidate.is_absolute()
            or len(candidate.parts) != 1
            or "/" in name
            or "\\" in name
        ):
            raise ValueError(f"Invalid temporary subdirectory name: {name!r}")
        child = self._session_directory / name
        child.mkdir(exist_ok=True)
        return child

    def cleanup(self) -> None:
        """Remove only this manager's session directory."""
        shutil.rmtree(self._session_directory, ignore_errors=True)

    def _cleanup_abandoned_sessions(self) -> None:
        for candidate in self._base_directory.iterdir():
            if not candidate.name.startswith("session-") or candidate.is_symlink():
                continue
            if not candidate.is_dir():
                continue
            try:
                marker = (candidate / ".owner").read_text(encoding="utf-8").strip()
                prefix, raw_pid = marker.split("=", maxsplit=1)
                pid = int(raw_pid)
                valid = prefix == "pid" and pid > 0
                running = valid and _is_process_running(pid)
            except (OSError, ValueError):
                running = False
            if not running:
                try:
                    shutil.rmtree(candidate)
                except OSError:
                    continue

    def __enter__(self) -> "TemporaryDirectoryManager":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cleanup()
