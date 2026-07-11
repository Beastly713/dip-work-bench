from pathlib import Path

import numpy as np
import pytest

from dip_workbench.controllers import DocumentController
from dip_workbench.core import ColourModel, ImageAsset, InputValidationError, RectangularRegion
from dip_workbench.services import (
    FlipDirection,
    ImageIOService,
    ImageTransformService,
    InterpolationMode,
)
from dip_workbench.state import ActivePreview, DocumentStore, HistorySnapshotStore


def controller(tmp_path: Path) -> DocumentController:
    io = ImageIOService()
    history = tmp_path / "history"
    history.mkdir()
    result = DocumentController(
        io, ImageTransformService(), DocumentStore(HistorySnapshotStore(history, io))
    )
    result.document_store.set_primary_image(
        ImageAsset(name="a", data=np.zeros((10, 12), dtype=np.uint8), colour_model=ColourModel.GRAY)
    )
    return result


def test_roi_preview_apply_and_stale_guard(tmp_path: Path) -> None:
    ctrl = controller(tmp_path)
    region = RectangularRegion(1, 2, 4, 5)
    ctrl.set_selected_region(region)
    assert ctrl.selected_region == region and not ctrl.document_store.history
    current = ctrl.current_image
    preview = ctrl.preview_crop()
    assert ctrl.current_image is current and ctrl.document_store.active_preview is not None
    applied = ctrl.apply_active_preview()
    assert (
        applied is preview
        and len(ctrl.document_store.history) == 1
        and ctrl.selected_region is None
    )
    ctrl.preview_flip(direction=FlipDirection.HORIZONTAL)
    ctrl.document_store.apply_image(ctrl.current_image, operation_id="x", operation_name="x")  # type: ignore[arg-type]
    with pytest.raises(InputValidationError):
        ctrl.apply_active_preview()


def test_resize_preview_clear_and_apply_without_preview(tmp_path: Path) -> None:
    ctrl = controller(tmp_path)
    ctrl.preview_resize(width=6, height=5, interpolation=InterpolationMode.LINEAR)
    ctrl.clear_active_preview()
    with pytest.raises(InputValidationError):
        ctrl.apply_active_preview()


def test_unsupported_preview_is_rejected_without_history(tmp_path: Path) -> None:
    ctrl = controller(tmp_path)
    current = ctrl.current_image
    assert current is not None
    ctrl.document_store.set_active_preview(ActivePreview("X-01", (current.id,), {}, {}, current, 0))
    with pytest.raises(InputValidationError, match="supported"):
        ctrl.apply_active_preview()
    assert ctrl.current_image is current
    assert not ctrl.document_store.history
