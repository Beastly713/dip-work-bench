import numpy as np
import pytest
from PySide6.QtCore import Qt

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError, RectangularRegion
from dip_workbench.ui.widgets import CanvasInteractionMode, ImageCanvas


def test_region_selection_overlay_and_clear(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(400, 300)
    canvas.show()
    asset = ImageAsset(
        name="a", data=np.zeros((100, 120), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    canvas.set_image(asset)
    canvas.show_actual_size()
    assert canvas.interaction_mode is CanvasInteractionMode.PAN
    canvas.begin_rectangle_selection()
    assert canvas.interaction_mode is CanvasInteractionMode.RECTANGLE_SELECTION
    start, end = canvas.mapFromScene(10, 20), canvas.mapFromScene(40, 60)
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(canvas.viewport(), end)
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=end)
    assert (
        canvas.selected_region == RectangularRegion(10, 20, 30, 40)
        and len(canvas.scene().items()) == 2
    )
    canvas.clear_region_selection()
    assert canvas.selected_region is None and len(canvas.scene().items()) == 1
    canvas.cancel_interaction()
    assert canvas.interaction_mode is CanvasInteractionMode.PAN
    np.testing.assert_array_equal(asset.data, 0)


def test_programmatic_region_removed_on_image_replace(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    asset = ImageAsset(
        name="a", data=np.zeros((10, 10), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    canvas.set_image(asset)
    canvas.begin_rectangle_selection(RectangularRegion(1, 1, 3, 3))
    assert canvas.selected_region is not None
    canvas.set_image(asset)
    assert canvas.selected_region is None
    assert canvas.interaction_mode is CanvasInteractionMode.PAN
    canvas.clear_region_selection()
    canvas.begin_rectangle_selection(RectangularRegion(1, 1, 2, 2))
    canvas.clear_image()
    assert canvas.selected_region is None
    assert canvas.interaction_mode is CanvasInteractionMode.PAN
    canvas.clear_region_selection()
    canvas.clear_region_selection()


def test_invalid_programmatic_region_uses_typed_error(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.set_image(
        ImageAsset(name="a", data=np.zeros((10, 10), dtype=np.uint8), colour_model=ColourModel.GRAY)
    )
    with pytest.raises(InputValidationError):
        canvas.set_selected_region(RectangularRegion(9, 9, 2, 2))
