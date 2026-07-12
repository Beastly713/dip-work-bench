"""Tests for owned PNG history snapshots."""

from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from dip_workbench.core import (
    ColourModel,
    ImageAsset,
    InputValidationError,
    OperationExecutionError,
)
from dip_workbench.services import ImageIOService
from dip_workbench.state import HistorySnapshotStore


def make_asset(model: ColourModel, value: int = 10) -> ImageAsset:
    shape = (2, 3, 3) if model is ColourModel.RGB else (2, 3)
    data = np.full(shape, value, dtype=np.uint8)
    if model is ColourModel.BINARY:
        data.fill(255)
    return ImageAsset(name="state", data=data, colour_model=model, metadata={"tag": "kept"})


def create(store: HistorySnapshotStore, image: ImageAsset):
    return store.create_entry(
        image, operation_id="M01", operation_name="Demo", input_source="Current Result"
    )


@pytest.mark.parametrize("model", [ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY])
def test_snapshot_round_trip_preserves_asset(model: ColourModel, tmp_path: Path) -> None:
    store = HistorySnapshotStore(tmp_path, ImageIOService())
    original = make_asset(model)
    entry = create(store, original)
    restored = store.restore(entry)
    assert entry.snapshot_path.suffix == ".png"
    assert entry.snapshot_path.exists()
    assert restored.colour_model is model
    assert restored.id == original.id
    assert restored.name == original.name
    assert restored.metadata == original.metadata
    np.testing.assert_array_equal(restored.data, original.data)


def test_delete_clear_and_close_are_owned_and_idempotent(tmp_path: Path) -> None:
    store = HistorySnapshotStore(tmp_path, ImageIOService())
    first = create(store, make_asset(ColourModel.GRAY, 1))
    second = create(store, make_asset(ColourModel.GRAY, 2))
    store.delete(first)
    assert not first.snapshot_path.exists() and second.snapshot_path.exists()
    store.clear()
    assert not second.snapshot_path.exists() and tmp_path.exists()
    store.close()
    store.close()


def test_missing_corrupt_foreign_and_unsupported_snapshots(tmp_path: Path) -> None:
    store = HistorySnapshotStore(tmp_path, ImageIOService())
    entry = create(store, make_asset(ColourModel.GRAY))
    entry.snapshot_path.unlink()
    with pytest.raises(OperationExecutionError):
        store.restore(entry)
    corrupt = create(store, make_asset(ColourModel.GRAY))
    corrupt.snapshot_path.write_bytes(b"corrupt")
    with pytest.raises(OperationExecutionError):
        store.restore(corrupt)
    foreign = replace(corrupt, snapshot_path=tmp_path.parent / "foreign.png")
    with pytest.raises(InputValidationError):
        store.delete(foreign)
    with pytest.raises(InputValidationError):
        create(store, object())  # type: ignore[arg-type]


def test_failed_save_leaves_no_owned_snapshot(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    image_io = ImageIOService()
    store = HistorySnapshotStore(tmp_path, image_io)
    monkeypatch.setattr(image_io, "save", lambda *args, **kwargs: (_ for _ in ()).throw(OSError()))
    with pytest.raises(OSError):
        create(store, make_asset(ColourModel.GRAY))
    assert list(tmp_path.iterdir()) == []
