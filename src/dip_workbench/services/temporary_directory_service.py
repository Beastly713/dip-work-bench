"""Safe temporary-session directory management."""

import shutil
import tempfile
from pathlib import Path
from types import TracebackType


class TemporaryDirectoryManager:
    """Own one unique temporary directory for an application session."""

    def __init__(self, base_directory: Path | None = None) -> None:
        self._base_directory = base_directory or Path(tempfile.gettempdir()) / "dip-workbench"
        self._base_directory.mkdir(parents=True, exist_ok=True)
        self._session_directory = Path(
            tempfile.mkdtemp(prefix="session-", dir=self._base_directory)
        )

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

    def __enter__(self) -> "TemporaryDirectoryManager":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.cleanup()
