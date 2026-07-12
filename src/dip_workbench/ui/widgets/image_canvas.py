"""Reusable graphics-view image canvas."""

import math
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDragMoveEvent,
    QDropEvent,
    QKeyEvent,
    QMouseEvent,
    QPen,
    QPixmap,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError, RectangularRegion
from dip_workbench.ui.image_qt import image_asset_to_qimage


class CanvasInteractionMode(StrEnum):
    PAN = "pan"
    RECTANGLE_SELECTION = "rectangle_selection"


class ImageCanvas(QGraphicsView):
    zoom_changed = Signal(float)
    pixel_hovered = Signal(int, int, object)
    pixel_left = Signal()
    file_dropped = Signal(object)
    region_changed = Signal(object)
    region_finished = Signal(object)
    interaction_cancelled = Signal()

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
        self._interaction_mode = CanvasInteractionMode.PAN
        self._selected_region: RectangularRegion | None = None
        self._selection_item: QGraphicsRectItem | None = None
        self._drag_start: QPointF | None = None
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

    @property
    def interaction_mode(self) -> CanvasInteractionMode:
        return self._interaction_mode

    @property
    def selected_region(self) -> RectangularRegion | None:
        return self._selected_region

    def set_image(self, asset: ImageAsset) -> None:
        pixmap = QPixmap.fromImage(image_asset_to_qimage(asset))
        self._scene.clear()
        self._reset_interaction_state()
        self._pixmap_item = self._scene.addPixmap(pixmap)
        self._pixmap_item.setPos(0, 0)
        self._scene.setSceneRect(0, 0, asset.width, asset.height)
        self._asset = asset
        self.fit_to_view()

    def clear_image(self) -> None:
        self._scene.clear()
        self._reset_interaction_state()
        self._pixmap_item = None
        self._asset = None
        self._fit_mode = False
        self.resetTransform()
        self._scene.setSceneRect(0, 0, 0, 0)
        self.pixel_left.emit()

    def _reset_interaction_state(self) -> None:
        self._drag_start = None
        self._selected_region = None
        self._selection_item = None
        self._space_pressed = False
        self._interaction_mode = CanvasInteractionMode.PAN
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def begin_rectangle_selection(self, region: RectangularRegion | None = None) -> None:
        self._interaction_mode = CanvasInteractionMode.RECTANGLE_SELECTION
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.set_selected_region(region)

    def set_selected_region(self, region: RectangularRegion | None) -> None:
        if region is not None and (
            self._asset is None or not region.fits_within(self._asset.width, self._asset.height)
        ):
            raise InputValidationError("Region does not fit the displayed image.")
        self.clear_region_selection()
        self._selected_region = region
        if region is not None:
            self._selection_item = self._scene.addRect(
                region.x,
                region.y,
                region.width,
                region.height,
                QPen(QColor("#3b82f6"), 0),
            )
            self._selection_item.setZValue(10)

    def clear_region_selection(self) -> None:
        if self._selection_item is not None:
            self._scene.removeItem(self._selection_item)
        self._selection_item = None
        self._selected_region = None

    def cancel_interaction(self) -> None:
        self._drag_start = None
        self._interaction_mode = CanvasInteractionMode.PAN
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.interaction_cancelled.emit()

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

    def set_zoom_percent(self, percent: float) -> None:
        if self._pixmap_item is None or not math.isfinite(percent):
            return
        target = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(percent)))
        if math.isclose(target, self.zoom_percent, rel_tol=1e-6):
            return
        self._fit_mode = False
        self.scale(target / self.zoom_percent, target / self.zoom_percent)
        self.zoom_changed.emit(self.zoom_percent)

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
        if self._drag_start is not None and not self._space_pressed:
            region = self._region_from_points(
                self._drag_start, self.mapToScene(event.position().toPoint())
            )
            if region is not None:
                self.set_selected_region(region)
                self.region_changed.emit(region)
            event.accept()
            return
        super().mouseMoveEvent(event)
        self._emit_pixel(event.position().toPoint())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if (
            self._interaction_mode is CanvasInteractionMode.RECTANGLE_SELECTION
            and not self._space_pressed
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self._drag_start = self.mapToScene(event.position().toPoint())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._drag_start is not None and event.button() == Qt.MouseButton.LeftButton:
            region = self._region_from_points(
                self._drag_start, self.mapToScene(event.position().toPoint())
            )
            self._drag_start = None
            if region is not None:
                self.set_selected_region(region)
                self.region_finished.emit(region)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _region_from_points(self, first: QPointF, second: QPointF) -> RectangularRegion | None:
        if self._asset is None:
            return None
        x1 = max(0.0, min(float(self._asset.width), first.x()))
        y1 = max(0.0, min(float(self._asset.height), first.y()))
        x2 = max(0.0, min(float(self._asset.width), second.x()))
        y2 = max(0.0, min(float(self._asset.height), second.y()))
        left, top = math.floor(min(x1, x2)), math.floor(min(y1, y2))
        right, bottom = math.ceil(max(x1, x2)), math.ceil(max(y1, y2))
        if right <= left or bottom <= top:
            return None
        return RectangularRegion(left, top, right - left, bottom - top)

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
            self.setDragMode(
                QGraphicsView.DragMode.NoDrag
                if self._interaction_mode is CanvasInteractionMode.RECTANGLE_SELECTION
                else QGraphicsView.DragMode.ScrollHandDrag
            )
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
