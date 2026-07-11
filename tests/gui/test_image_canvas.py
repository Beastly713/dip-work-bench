"""GUI tests for the reusable image canvas."""

import numpy as np
from PySide6.QtCore import QPoint

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.ui.widgets import ImageCanvas


def make_asset(model: ColourModel = ColourModel.RGB) -> ImageAsset:
    if model is ColourModel.RGB:
        data = np.zeros((20, 30, 3), dtype=np.uint8)
        data[2, 3] = (10, 20, 30)
    else:
        data = np.zeros((20, 30), dtype=np.uint8)
        data[2, 3] = 255
    return ImageAsset(name="canvas", data=data, colour_model=model)


def test_canvas_display_fit_zoom_actual_and_clear(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(500, 400)
    canvas.show()
    assert canvas.current_asset is None
    asset = make_asset()
    canvas.set_image(asset)
    assert canvas.current_asset is asset
    assert len(canvas.scene().items()) == 1
    assert canvas.sceneRect().width() == 30 and canvas.sceneRect().height() == 20
    assert canvas.is_fit_to_view
    canvas.show_actual_size()
    assert abs(canvas.zoom_percent - 100) < 0.1 and not canvas.is_fit_to_view
    canvas.zoom_in()
    assert canvas.zoom_percent > 100
    canvas.zoom_out()
    assert abs(canvas.zoom_percent - 100) < 0.1
    canvas.clear_image()
    assert canvas.current_asset is None and not canvas.scene().items()


def test_pixel_mapping_uses_canonical_asset(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(300, 200)
    canvas.show()
    canvas.set_image(make_asset())
    canvas.show_actual_size()
    values: list[tuple[int, int, object]] = []
    canvas.pixel_hovered.connect(lambda x, y, value: values.append((x, y, value)))
    position = canvas.mapFromScene(3.2, 2.2)
    canvas._emit_pixel(QPoint(position.x(), position.y()))
    assert values[-1] == (3, 2, (10, 20, 30))
