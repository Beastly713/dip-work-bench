"""Tests for single-document state and history behavior."""

from pathlib import Path

import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.services import ImageIOService
from dip_workbench.state import ActivePreview, DocumentStore, HistorySnapshotStore


def image(value: int, model: ColourModel = ColourModel.GRAY) -> ImageAsset:
    dtype = np.int32 if model is ColourModel.LABEL else np.uint8
    shape = (3, 4, 3) if model is ColourModel.RGB else (3, 4)
    data = np.full(shape, value, dtype=dtype)
    if model is ColourModel.BINARY:
        data.fill(255 if value else 0)
    return ImageAsset(name=f"image-{value}", data=data, colour_model=model)


def make_store(tmp_path: Path, limit: int = 25) -> DocumentStore:
    directory = tmp_path / "history"
    directory.mkdir()
    return DocumentStore(HistorySnapshotStore(directory, ImageIOService()), history_limit=limit)


def apply(store: DocumentStore, value: int, model: ColourModel = ColourModel.GRAY) -> ImageAsset:
    return store.apply_image(
        image(value, model), operation_id=f"op-{value}", operation_name=f"Operation {value}"
    )


def test_primary_is_independent_and_replacement_clears_state(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    assert not store.has_document and not store.can_undo and not store.can_redo
    original = image(1)
    store.set_primary_image(original)
    assert store.original_image is original
    assert store.current_image is not original
    assert store.current_image is not None
    assert store.current_image.id != original.id
    np.testing.assert_array_equal(store.current_image.data, original.data)
    store.set_auxiliary_input("reference", image(2))
    store.set_operation_state("op", {"seed": 3})
    store.set_active_preview(ActivePreview("op", (), {}, {}, object(), 0))
    apply(store, 4)
    old_snapshot = store.history[0].snapshot_path
    store.undo()
    store.set_primary_image(image(9))
    assert not store.history and not store.redo_history
    assert store.active_preview is None
    assert not store.auxiliary_inputs and not store.operation_states
    assert not old_snapshot.exists()


def test_preview_and_operation_state_are_non_destructive(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.set_primary_image(image(1))
    current = store.current_image
    preview = ActivePreview("op", (), {"x": 1}, {}, image(2), 0)
    store.set_active_preview(preview)
    store.set_active_preview(ActivePreview("op", (), {}, {}, image(3), 1))
    state = {"seed": 4}
    store.set_operation_state("op", state)
    state["seed"] = 5
    assert store.current_image is current and not store.history
    assert store.get_operation_state("op") == {"seed": 4}
    store.clear_active_preview()
    store.clear_operation_state("op")
    assert store.active_preview is None and store.get_operation_state("op") is None


def test_apply_undo_redo_order_and_original_immutability(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    original = image(0)
    store.set_primary_image(original)
    apply(store, 10)
    first_snapshot = store.history[-1].snapshot_path
    apply(store, 20)
    assert len(store.history) == 2 and first_snapshot.exists()
    np.testing.assert_array_equal(original.data, 0)
    assert int(store.undo().data[0, 0]) == 10
    assert int(store.undo().data[0, 0]) == 0
    assert int(store.redo().data[0, 0]) == 10
    assert int(store.redo().data[0, 0]) == 20


def test_binary_semantics_survive_undo_redo(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.set_primary_image(image(0, ColourModel.BINARY))
    apply(store, 1, ColourModel.BINARY)
    store.undo()
    restored = store.redo()
    assert restored.colour_model is ColourModel.BINARY
    np.testing.assert_array_equal(restored.data, 255)


def test_new_apply_invalidates_redo_and_deletes_snapshot(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.set_primary_image(image(0))
    apply(store, 1)
    apply(store, 2)
    store.undo()
    redo_path = store.redo_history[-1].snapshot_path
    apply(store, 3)
    assert not store.redo_history and not redo_path.exists()


def test_history_limit_deletes_oldest_snapshot(tmp_path: Path) -> None:
    store = make_store(tmp_path, limit=25)
    store.set_primary_image(image(0))
    first_path = None
    for value in range(1, 27):
        apply(store, value)
        if value == 1:
            first_path = store.history[0].snapshot_path
    assert len(store.history) == 25
    assert first_path is not None and not first_path.exists()


def test_reset_is_applied_and_undoable(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    store.set_primary_image(image(0))
    apply(store, 8)
    reset = store.reset_to_original()
    assert int(reset.data[0, 0]) == 0
    assert store.history[-1].operation_id == "U-11"
    assert int(store.undo().data[0, 0]) == 8


def test_auxiliary_inputs_and_validation(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    first, second = image(1), image(2)
    store.set_auxiliary_input("secondary", first)
    assert store.get_auxiliary_input("secondary") is first
    store.set_auxiliary_input("dataset", (first, second))
    assert store.get_auxiliary_input("dataset") == (first, second)
    store.remove_auxiliary_input("secondary")
    store.remove_auxiliary_input("missing")
    with pytest.raises(InputValidationError):
        store.set_auxiliary_input("dataset", ())
    with pytest.raises(InputValidationError):
        store.set_auxiliary_input("", first)


def test_invalid_actions_and_clear_close(tmp_path: Path) -> None:
    store = make_store(tmp_path)
    with pytest.raises(InputValidationError):
        apply(store, 1)
    store.set_primary_image(image(0))
    with pytest.raises(InputValidationError):
        store.undo()
    with pytest.raises(InputValidationError):
        store.redo()
    with pytest.raises(InputValidationError):
        store.apply_image(image(1, ColourModel.LABEL), operation_id="x", operation_name="x")
    apply(store, 2)
    path = store.history[0].snapshot_path
    store.clear_document()
    assert not path.exists() and not store.has_document
    store.close()
    store.close()


def test_failed_snapshot_leaves_current_and_history_unchanged(tmp_path: Path, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    store = make_store(tmp_path)
    store.set_primary_image(image(0))
    current = store.current_image
    monkeypatch.setattr(
        store._snapshot_store,
        "create_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("failed")),
    )
    with pytest.raises(RuntimeError):
        apply(store, 1)
    assert store.current_image is current and not store.history
