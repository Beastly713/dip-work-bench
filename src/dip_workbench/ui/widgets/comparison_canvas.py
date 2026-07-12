"""Overlaid split-image comparison canvas."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.ui.image_qt import image_asset_to_qimage


class SplitComparisonCanvas(QGraphicsView):
    split_changed = Signal(float)

    MIN_ZOOM = 5.0
    MAX_ZOOM = 3200.0
    ZOOM_STEP = 1.25

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._input_pixmap: QPixmap | None = None
        self._result_pixmap: QPixmap | None = None
        self._split_percent = 50.0
        self._message = "No images to compare"
        self._input_label = "Input"
        self._result_label = "Result"
        self._dragging_split = False
        self._fit_mode = False
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    @property
    def split_percent(self) -> float:
        return self._split_percent

    @property
    def enabled_split(self) -> bool:
        return self._input_pixmap is not None and self._result_pixmap is not None

    def set_images(self, input_asset: ImageAsset, result_asset: ImageAsset) -> None:
        self.clear()
        if (input_asset.width, input_asset.height) != (result_asset.width, result_asset.height):
            self._message = "Split comparison requires matching image dimensions."
            self.viewport().update()
            return
        self._input_pixmap = QPixmap.fromImage(image_asset_to_qimage(input_asset))
        self._result_pixmap = QPixmap.fromImage(image_asset_to_qimage(result_asset))
        self._scene.setSceneRect(0, 0, input_asset.width, input_asset.height)
        self.set_split_percent(50.0)
        self.fit_to_view()

    def set_split_percent(self, percent: float) -> None:
        self._split_percent = max(0.0, min(100.0, float(percent)))
        self.split_changed.emit(self._split_percent)
        self.viewport().update()

    def set_labels(self, input_label: str, result_label: str) -> None:
        self._input_label = input_label
        self._result_label = result_label
        self.viewport().update()

    def clear(self) -> None:
        self._input_pixmap = None
        self._result_pixmap = None
        self._message = "No images to compare"
        self._dragging_split = False
        self._split_percent = 50.0
        self.resetTransform()
        self._scene.setSceneRect(0, 0, 0, 0)
        self.viewport().update()

    def fit_to_view(self) -> None:
        if not self.enabled_split:
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_mode = True
        self.viewport().update()

    def show_actual_size(self) -> None:
        if not self.enabled_split:
            return
        self.resetTransform()
        self._fit_mode = False
        self.viewport().update()

    def zoom_in(self) -> None:
        self._zoom(self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self._zoom(1.0 / self.ZOOM_STEP)

    def _zoom(self, factor: float) -> None:
        if not self.enabled_split:
            return
        current = self.transform().m11() * 100.0
        target = min(max(current * factor, self.MIN_ZOOM), self.MAX_ZOOM)
        self.scale(target / current, target / current)
        self._fit_mode = False
        self.viewport().update()

    def drawForeground(self, painter: QPainter, rect: QRectF | QRect) -> None:
        del rect
        if not self.enabled_split:
            painter.resetTransform()
            painter.setPen(Qt.GlobalColor.white)
            painter.drawText(self.viewport().rect(), Qt.AlignmentFlag.AlignCenter, self._message)
            return
        assert self._input_pixmap is not None and self._result_pixmap is not None
        scene_rect = self._scene.sceneRect()
        split_x = scene_rect.left() + scene_rect.width() * (self._split_percent / 100.0)
        painter.drawPixmap(QPointF(0, 0), self._result_pixmap)
        painter.save()
        painter.setClipRect(
            QRectF(scene_rect.left(), scene_rect.top(), split_x, scene_rect.height())
        )
        painter.drawPixmap(QPointF(0, 0), self._input_pixmap)
        painter.restore()
        painter.setPen(Qt.GlobalColor.yellow)
        painter.drawLine(QPointF(split_x, scene_rect.top()), QPointF(split_x, scene_rect.bottom()))
        self._draw_labels(painter)

    def _draw_labels(self, painter: QPainter) -> None:
        painter.resetTransform()
        painter.setPen(Qt.GlobalColor.white)
        painter.setBrush(QColor(15, 23, 42, 190))
        left_rect = QRect(12, 12, 96, 28)
        right_rect = QRect(max(12, self.viewport().width() - 108), 12, 96, 28)
        painter.drawRoundedRect(left_rect, 4, 4)
        painter.drawRoundedRect(right_rect, 4, 4)
        painter.drawText(left_rect, Qt.AlignmentFlag.AlignCenter, self._input_label)
        painter.drawText(right_rect, Qt.AlignmentFlag.AlignCenter, self._result_label)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.enabled_split and event.button() == Qt.MouseButton.LeftButton:
            point = self.mapToScene(event.position().toPoint())
            split_x = self._scene.sceneRect().width() * (self._split_percent / 100.0)
            if abs(point.x() - split_x) <= 8 / max(self.transform().m11(), 0.001):
                self._dragging_split = True
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._dragging_split:
            point = self.mapToScene(event.position().toPoint())
            width = max(self._scene.sceneRect().width(), 1.0)
            self.set_split_percent(point.x() / width * 100.0)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._dragging_split and event.button() == Qt.MouseButton.LeftButton:
            self._dragging_split = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        self._zoom(self.ZOOM_STEP if event.angleDelta().y() > 0 else 1.0 / self.ZOOM_STEP)
        event.accept()

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        if self._fit_mode:
            self.fit_to_view()
