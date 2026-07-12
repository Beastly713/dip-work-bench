"""GUI tests for reusable comparison widgets."""

import numpy as np
from PySide6.QtCore import Qt

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.ui.widgets import (
    BeforeAfterComparisonWidget,
    ComparisonMode,
    SideBySideComparisonWidget,
    SplitComparisonCanvas,
    TripleComparisonWidget,
)


def image(name: str, width: int = 8, height: int = 6) -> ImageAsset:
    return ImageAsset(name, np.zeros((height, width), dtype=np.uint8), ColourModel.GRAY)


def test_side_by_side_zoom_maximize_and_clear(qtbot) -> None:  # type: ignore[no-untyped-def]
    widget = SideBySideComparisonWidget()
    qtbot.addWidget(widget)
    widget.show()
    widget.set_images("Input", image("a"), "Result", image("b", 10, 4))
    assert widget.panels[0].label.text() == "Input"
    assert widget.panels[1].label.text() == "Result"
    widget.panels[0].canvas.set_zoom_percent(150)
    assert round(widget.panels[1].canvas.zoom_percent) == 150
    widget.panels[0].max_button.click()
    assert widget.panels[0].isVisible() and not widget.panels[1].isVisible()
    widget.panels[0].max_button.click()
    assert all(panel.isVisible() for panel in widget.panels)
    widget.clear()
    assert widget.panels[0].canvas.current_asset is None


def test_triple_comparison_and_split_modes(qtbot) -> None:  # type: ignore[no-untyped-def]
    triple = TripleComparisonWidget()
    qtbot.addWidget(triple)
    triple.show()
    triple.set_images((("A", image("a")), ("B", image("b")), ("Result", image("c"))))
    triple.panels[2].canvas.set_zoom_percent(125)
    assert round(triple.panels[0].canvas.zoom_percent) == 125

    split = SplitComparisonCanvas()
    qtbot.addWidget(split)
    split.set_images(image("a"), image("b"))
    for percent in (0, 50, 100):
        split.set_split_percent(percent)
        assert split.split_percent == percent
    split.set_images(image("a"), image("wide", 10, 6))
    assert not split.enabled_split


def test_before_after_hold_b_is_scoped(qtbot) -> None:  # type: ignore[no-untyped-def]
    widget = BeforeAfterComparisonWidget()
    qtbot.addWidget(widget)
    widget.show()
    source = image("source")
    result = ImageAsset("result", np.full((6, 8), 255, dtype=np.uint8), ColourModel.GRAY)
    widget.set_images(source, result, result_label="Negative Result")
    widget.set_mode(ComparisonMode.SIDE_BY_SIDE)
    qtbot.keyPress(widget, Qt.Key.Key_B)
    assert widget.side_by_side.panels[1].label.text() == "Input - Hold B"
    qtbot.keyRelease(widget, Qt.Key.Key_B)
    assert widget.side_by_side.panels[1].label.text() == "Negative Result"
