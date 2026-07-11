"""Reusable graphics-view image canvas."""

from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import (
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QWidget

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.ui.image_qt import image_asset_to_qimage


class ImageCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    pixel_hovered = Signal(int, int, object)
    pixel_left = Signal()
    file_dropped = Signal(object)

    MIN_ZOOM = 5.0
    MAX_ZOOM = 3200.0
    ZOOM_STEP = 1.25
    SUPPORTED_EXTENSIONS: ClassVar[frozenset[str]] = frozenset(
        {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._pixmap_item: QGraphicsPixmapItem | None = None
        self._asset: ImageAsset | None = None
        self._fit_mode = False
        self._space_pressed = False
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    @property
    def current_asset(self) -> ImageAsset | None:
        return self._asset

    @property
    def zoom_percent(self) -> float:
        return self.transform().m11() * 100.0

    @property
    def is_fit_to_view(self) -> bool:
        return self._fit_mode

    def set_image(self, asset: ImageAsset) -> None:
        pixmap = QPixmap.fromImage(image_asset_to_qimage(asset))
        self._scene.clear()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._pixmap_item.setPos(0, 0)
        self._scene.setSceneRect(0, 0, asset.width, asset.height)
        self._asset = asset
        self.fit_to_view()

    def clear_image(self) -> None:
        self._scene.clear()
        self._pixmap_item = None
        self._asset = None
        self._fit_mode = False
        self.resetTransform()
        self.pixel_left.emit()

    def fit_to_view(self) -> None:
        if (
            self._pixmap_item is None
            or self.viewport().width() <= 0
            or self.viewport().height() <= 0
        ):
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        current = self.zoom_percent
        if current < self.MIN_ZOOM:
            self.scale(self.MIN_ZOOM / current, self.MIN_ZOOM / current)
        elif current > self.MAX_ZOOM:
            self.scale(self.MAX_ZOOM / current, self.MAX_ZOOM / current)
        self._fit_mode = True
        self.zoom_changed.emit(self.zoom_percent)

    def show_actual_size(self) -> None:
        if self._asset is None:
            return
        self.resetTransform()
        self._fit_mode = False
        self.zoom_changed.emit(100.0)

    def zoom_in(self) -> None:
        self._apply_zoom(self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self._apply_zoom(1.0 / self.ZOOM_STEP)

    def _apply_zoom(self, factor: float) -> None:
        if self._asset is None:
            return
        target = self.zoom_percent * factor
        target = min(max(target, self.MIN_ZOOM), self.MAX_ZOOM)
        actual_factor = target / self.zoom_percent
        self.scale(actual_factor, actual_factor)
        self._fit_mode = False
        self.zoom_changed.emit(self.zoom_percent)

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        if self._fit_mode:
            self.fit_to_view()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._asset is None:
            super().wheelEvent(event)
            return
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._apply_zoom(self.ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / self.ZOOM_STEP)
        event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        super().mouseMoveEvent(event)
        self._emit_pixel(event.position().toPoint())

    def leaveEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        self.pixel_left.emit()
        super().leaveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = True
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            event.accept()
            return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
            self._space_pressed = False
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
            event.accept()
            return
        super().keyReleaseEvent(event)

    def _emit_pixel(self, viewport_position: QPoint) -> None:
        if self._asset is None:
            self.pixel_left.emit()
            return
        point = self.mapToScene(viewport_position)
        x, y = int(point.x()), int(point.y())
        if point.x() < 0 or point.y() < 0 or x >= self._asset.width or y >= self._asset.height:
            self.pixel_left.emit()
            return
        raw = self._asset.data[y, x]
        value: object
        if self._asset.colour_model is ColourModel.RGB:
            value = tuple(int(component) for component in raw)
        else:
            value = int(raw)
        self.pixel_hovered.emit(x, y, value)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if self._first_supported_local_path(event) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        if self._first_supported_local_path(event) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        path = self._first_supported_local_path(event)
        if path is not None:
            self.file_dropped.emit(path)
            event.acceptProposedAction()
        else:
            event.ignore()

    def _first_supported_local_path(self, event: object) -> Path | None:
        mime_data = event.mimeData()  # type: ignore[attr-defined]
        if not mime_data.hasUrls():
            return None
        for url in mime_data.urls():
            if url.isLocalFile():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    return path
        return None
