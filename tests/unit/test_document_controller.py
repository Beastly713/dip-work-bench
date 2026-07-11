"""Tests for primary-document coordination."""

from pathlib import Path

import numpy as np
import pytest

from dip_workbench.controllers import DocumentController
from dip_workbench.core import ColourModel, ImageAsset, InputValidationError, UnsupportedImageError
from dip_workbench.services import ImageIOService, ImageTransformService
from dip_workbench.state import DocumentStore, HistorySnapshotStore


def setup_controller(tmp_path: Path) -> DocumentController:
    history = tmp_path / "history"
    history.mkdir()
    image_io = ImageIOService()
    return DocumentController(
        image_io,
        ImageTransformService(),
        DocumentStore(HistorySnapshotStore(history, image_io)),
    )


def source(value: int = 10) -> ImageAsset:
    return ImageAsset(
        name="source", data=np.full((3, 4), value, dtype=np.uint8), colour_model=ColourModel.GRAY
    )


def test_open_save_and_failed_open_preserve_state(tmp_path: Path) -> None:
    controller = setup_controller(tmp_path)
    input_path = tmp_path / "input.png"
    controller.image_io.save(source(), input_path)
    current = controller.open_primary_image(input_path)
    assert current is controller.current_image and controller.has_document
    previous = controller.current_image
    with pytest.raises(UnsupportedImageError):
        controller.open_primary_image(tmp_path / "missing.png")
    assert controller.current_image is previous
    output = tmp_path / "output.png"
    assert controller.save_current_image(output) == output
    assert output.exists() and not controller.document_store.history


def test_save_without_document_and_history_delegation(tmp_path: Path) -> None:
    controller = setup_controller(tmp_path)
    with pytest.raises(InputValidationError):
        controller.save_current_image(tmp_path / "none.png")
    controller.document_store.set_primary_image(source(0))
    controller.document_store.apply_image(source(50), operation_id="test", operation_name="Test")
    assert int(controller.undo().data[0, 0]) == 0
    assert int(controller.redo().data[0, 0]) == 50
    assert int(controller.reset_to_original().data[0, 0]) == 0
    assert controller.original_image is not None
