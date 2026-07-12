"""Focused image overlay viewer for lines, circles, and points."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations import CircleOverlay, LineOverlay, OverlayData, PointOverlay
from dip_workbench.ui.image_qt import image_asset_to_qimage


class OverlayCanvas(QGraphicsView):
    MIN_ZOOM = 0.05
    MAX_ZOOM = 32.0

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._base_item: QGraphicsPixmapItem | None = None
        self._overlay_items: list[QGraphicsLineItem | QGraphicsEllipseItem] = []
        self._base_asset: ImageAsset | None = None
        self._overlay_data: OverlayData | None = None
        self._fit_mode = False
        self._zoom = 1.0
        self.setBackgroundBrush(Qt.GlobalColor.darkGray)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    def set_content(self, base: ImageAsset, overlays: OverlayData) -> None:
        self.clear()
        self._base_asset = base
        self._overlay_data = overlays
        self._base_item = self._scene.addPixmap(QPixmap.fromImage(image_asset_to_qimage(base)))
        self._scene.setSceneRect(0, 0, base.width, base.height)
        self._populate_overlays(overlays)
        self.fit_to_view()

    def set_overlay_visible(self, visible: bool) -> None:
        for item in self._overlay_items:
            item.setVisible(visible)

    def clear(self) -> None:
        self._scene.clear()
        self._base_item = None
        self._overlay_items = []
        self._base_asset = None
        self._overlay_data = None
        self._fit_mode = False
        self._zoom = 1.0
        self.resetTransform()
        self._scene.setSceneRect(0, 0, 0, 0)

    def fit_to_view(self) -> None:
        if self._base_item is None:
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.transform().m11()))
        self._fit_mode = True

    def show_actual_size(self) -> None:
        if self._base_item is None:
            return
        self.resetTransform()
        self._zoom = 1.0
        self._fit_mode = False

    def zoom_in(self) -> None:
        self._zoom_by(1.25)

    def zoom_out(self) -> None:
        self._zoom_by(0.8)

    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage:
        del minimum_width, minimum_height
        asset = self._base_asset
        if asset is None:
            return QImage()
        return self._render_at(asset.width, asset.height)

    def baked_image(self, name: str) -> ImageAsset:
        asset = self._base_asset
        if asset is None:
            raise InputValidationError("No overlay content is available.")
        image = self._render_at(asset.width, asset.height).convertToFormat(
            QImage.Format.Format_RGB888
        )
        bytes_per_line = image.bytesPerLine()
        height = image.height()
        width = image.width()
        buffer = np.frombuffer(image.constBits(), dtype=np.uint8, count=bytes_per_line * height)
        rows = buffer.reshape((height, bytes_per_line))
        data = rows[:, : width * 3].reshape((height, width, 3)).copy()
        metadata = dict(asset.metadata)
        metadata["overlay_baked"] = True
        return ImageAsset(
            name=name,
            data=np.ascontiguousarray(data),
            colour_model=ColourModel.RGB,
            source_path=asset.source_path,
            metadata=metadata,
        )

    def resizeEvent(self, event) -> None:  # type: ignore[no-untyped-def]
        super().resizeEvent(event)
        if self._fit_mode:
            self.fit_to_view()

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() == 0:
            super().wheelEvent(event)
            return
        self._zoom_by(1.25 if event.angleDelta().y() > 0 else 0.8)
        event.accept()

    def _render_at(self, width: int, height: int) -> QImage:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(0xFFFFFFFF)
        painter = QPainter(image)
        self._scene.render(painter, QRectF(0, 0, width, height), self._scene.sceneRect())
        painter.end()
        return image

    def _populate_overlays(self, overlays: OverlayData) -> None:
        line_pen = QPen(QColor("#ef4444"), 2)
        circle_pen = QPen(QColor("#22c55e"), 2)
        point_pen = QPen(QColor("#f59e0b"), 1)
        point_brush = QColor("#f59e0b")
        for primitive in overlays.items:
            item: QGraphicsLineItem | QGraphicsEllipseItem
            if isinstance(primitive, LineOverlay):
                item = self._scene.addLine(
                    primitive.x1, primitive.y1, primitive.x2, primitive.y2, line_pen
                )
            elif isinstance(primitive, CircleOverlay):
                item = self._scene.addEllipse(
                    primitive.center_x - primitive.radius,
                    primitive.center_y - primitive.radius,
                    primitive.radius * 2,
                    primitive.radius * 2,
                    circle_pen,
                )
            else:
                assert isinstance(primitive, PointOverlay)
                item = self._scene.addEllipse(
                    primitive.x - primitive.radius,
                    primitive.y - primitive.radius,
                    primitive.radius * 2,
                    primitive.radius * 2,
                    point_pen,
                    point_brush,
                )
            item.setZValue(10)
            self._overlay_items.append(item)

    def _zoom_by(self, factor: float) -> None:
        if self._base_item is None:
            return
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self._zoom * factor))
        factor = new_zoom / self._zoom if self._zoom else 1.0
        if factor == 1.0:
            return
        self.scale(factor, factor)
        self._zoom = new_zoom
        self._fit_mode = False


class OverlayViewer(QWidget):
    bake_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.visible_toggle = QCheckBox("Show overlay")
        self.visible_toggle.setChecked(True)
        self.fit_button = QPushButton("Fit")
        self.actual_button = QPushButton("100%")
        self.zoom_out_button = QPushButton("-")
        self.zoom_in_button = QPushButton("+")
        controls.addWidget(self.visible_toggle)
        controls.addStretch()
        controls.addWidget(self.fit_button)
        controls.addWidget(self.actual_button)
        controls.addWidget(self.zoom_out_button)
        controls.addWidget(self.zoom_in_button)
        self.canvas = OverlayCanvas()
        layout.addLayout(controls)
        layout.addWidget(self.canvas, 1)
        self.visible_toggle.toggled.connect(self.canvas.set_overlay_visible)
        self.fit_button.clicked.connect(self.canvas.fit_to_view)
        self.actual_button.clicked.connect(self.canvas.show_actual_size)
        self.zoom_out_button.clicked.connect(self.canvas.zoom_out)
        self.zoom_in_button.clicked.connect(self.canvas.zoom_in)

    def set_content(self, base: ImageAsset, overlays: OverlayData) -> None:
        self.visible_toggle.setChecked(True)
        self.canvas.set_content(base, overlays)

    def clear(self) -> None:
        self.canvas.clear()
        self.visible_toggle.setChecked(True)

    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage:
        return self.canvas.render_image(minimum_width=minimum_width, minimum_height=minimum_height)

    def baked_image(self, name: str) -> ImageAsset:
        return self.canvas.baked_image(name)
