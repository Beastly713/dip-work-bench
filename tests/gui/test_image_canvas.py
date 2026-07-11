"""GUI tests for the reusable image canvas."""

import numpy as np
from PySide6.QtCore import QMimeData, QPoint, Qt, QUrl

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


def test_zoom_clamps_and_resize_respects_view_mode(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(400, 300)
    canvas.show()
    canvas.set_image(make_asset())
    fitted = canvas.zoom_percent
    canvas.resize(700, 500)
    qtbot.wait(10)
    assert canvas.is_fit_to_view and canvas.zoom_percent != fitted
    canvas.show_actual_size()
    canvas.resize(600, 450)
    qtbot.wait(10)
    assert abs(canvas.zoom_percent - 100) < 0.1
    for _ in range(100):
        canvas.zoom_in()
    assert canvas.zoom_percent <= canvas.MAX_ZOOM + 0.1
    for _ in range(200):
        canvas.zoom_out()
    assert canvas.zoom_percent >= canvas.MIN_ZOOM - 0.1


def test_grayscale_binary_and_outside_pixel_mapping(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(300, 200)
    canvas.show()
    values: list[object] = []
    left: list[bool] = []
    canvas.pixel_hovered.connect(lambda x, y, value: values.append(value))
    canvas.pixel_left.connect(lambda: left.append(True))
    for model in (ColourModel.GRAY, ColourModel.BINARY):
        canvas.set_image(make_asset(model))
        canvas.show_actual_size()
        position = canvas.mapFromScene(3.2, 2.2)
        canvas._emit_pixel(position)
        assert values[-1] == 255
    canvas._emit_pixel(QPoint(-100, -100))
    assert left


def test_pan_and_space_pan_do_not_mutate_asset(qtbot) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(240, 180)
    canvas.show()
    asset = make_asset()
    original = asset.data.copy()
    canvas.set_image(asset)
    canvas.show_actual_size()
    for _ in range(12):
        canvas.zoom_in()
    before = canvas.horizontalScrollBar().value()
    qtbot.mousePress(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(120, 90))
    qtbot.mouseMove(canvas.viewport(), QPoint(60, 90))
    qtbot.mouseRelease(canvas.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(60, 90))
    assert canvas.horizontalScrollBar().value() != before
    qtbot.keyPress(canvas, Qt.Key.Key_Space)
    assert canvas._space_pressed
    qtbot.keyRelease(canvas, Qt.Key.Key_Space)
    assert not canvas._space_pressed
    np.testing.assert_array_equal(asset.data, original)


class FakeDropEvent:
    def __init__(self, mime_data: QMimeData) -> None:
        self._mime_data = mime_data
        self.accepted = False

    def mimeData(self) -> QMimeData:
        return self._mime_data

    def acceptProposedAction(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.accepted = False


def test_drop_accepts_first_supported_local_path_only(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    canvas = ImageCanvas()
    qtbot.addWidget(canvas)
    emitted: list[object] = []
    canvas.file_dropped.connect(emitted.append)
    local = tmp_path / "image.png"
    local.touch()
    mime = QMimeData()
    mime.setUrls([QUrl("https://example.com/image.png"), QUrl.fromLocalFile(str(local))])
    event = FakeDropEvent(mime)
    canvas.dropEvent(event)  # type: ignore[arg-type]
    assert event.accepted and emitted == [local]
    remote = QMimeData()
    remote.setUrls([QUrl("https://example.com/image.png")])
    remote_event = FakeDropEvent(remote)
    canvas.dragEnterEvent(remote_event)  # type: ignore[arg-type]
    assert not remote_event.accepted
    text = QMimeData()
    text.setText("image.png")
    text_event = FakeDropEvent(text)
    canvas.dragEnterEvent(text_event)  # type: ignore[arg-type]
    assert not text_event.accepted
