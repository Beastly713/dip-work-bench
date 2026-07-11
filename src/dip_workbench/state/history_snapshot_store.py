"""Owned lossless history snapshot storage."""

from collections.abc import Mapping
from pathlib import Path
from uuid import uuid4

from dip_workbench.core import (
    ColourModel,
    ImageAsset,
    InputValidationError,
    OperationExecutionError,
)
from dip_workbench.services import ImageIOService
from dip_workbench.state.models import HistoryEntry


class HistorySnapshotStore:
    """Persist applied canonical image states as owned PNG files."""

    def __init__(self, directory: Path, image_io: ImageIOService) -> None:
        self.directory = Path(directory)
        if not self.directory.is_dir():
            raise InputValidationError("History snapshot directory must already exist.")
        self._resolved_directory = self.directory.resolve()
        self._image_io = image_io
        self._owned_paths: set[Path] = set()

    def create_entry(
        self,
        asset: ImageAsset,
        *,
        operation_id: str,
        operation_name: str,
        parameters: Mapping[str, object] | None = None,
        input_source: str,
        metadata: Mapping[str, object] | None = None,
    ) -> HistoryEntry:
        if not isinstance(asset, ImageAsset) or asset.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
            ColourModel.BINARY,
        }:
            raise InputValidationError(
                "History snapshots require an RGB, grayscale, or binary asset."
            )
        path = self.directory / f"{uuid4()}.png"
        self._image_io.save(asset, path)
        resolved = path.resolve()
        self._owned_paths.add(resolved)
        try:
            return HistoryEntry(
                operation_id=operation_id,
                operation_name=operation_name,
                parameters=parameters or {},
                input_source=input_source,
                snapshot_path=path,
                asset_id=asset.id,
                asset_name=asset.name,
                colour_model=asset.colour_model,
                source_path=asset.source_path,
                asset_metadata=asset.metadata,
                metadata=metadata or {},
            )
        except Exception:
            path.unlink(missing_ok=True)
            self._owned_paths.discard(resolved)
            raise

    def restore(self, entry: HistoryEntry) -> ImageAsset:
        path = self._owned_path(entry)
        try:
            decoded = self._image_io.load(path)
            return ImageAsset(
                id=entry.asset_id,
                name=entry.asset_name,
                data=decoded.data,
                colour_model=entry.colour_model,
                source_path=entry.source_path,
                metadata=entry.asset_metadata,
            )
        except Exception as error:
            if isinstance(error, InputValidationError):
                raise
            raise OperationExecutionError("History snapshot could not be restored.") from error

    def delete(self, entry: HistoryEntry) -> None:
        path = self._owned_path(entry)
        path.unlink(missing_ok=True)
        self._owned_paths.discard(path)

    def clear(self) -> None:
        for path in tuple(self._owned_paths):
            path.unlink(missing_ok=True)
        self._owned_paths.clear()

    def close(self) -> None:
        self.clear()

    def _owned_path(self, entry: HistoryEntry) -> Path:
        if not isinstance(entry, HistoryEntry):
            raise InputValidationError("A valid history entry is required.")
        path = entry.snapshot_path.resolve()
        if path.parent != self._resolved_directory or path not in self._owned_paths:
            raise InputValidationError("History snapshot is not owned by this store.")
        return path
