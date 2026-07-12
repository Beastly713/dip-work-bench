"""Focused image overlay viewer for lines, circles, and points."""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QGraphicsEllipseItem,
    QGraphicsLineItem,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.operations import CircleOverlay, LineOverlay, OverlayData, PointOverlay
from dip_workbench.ui.image_qt import image_asset_to_qimage


class OverlayCanvas(QGraphicsView):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._base_item: QGraphicsPixmapItem | None = None
        self._overlay_items: list[QGraphicsLineItem | QGraphicsEllipseItem] = []
        self._base_asset: ImageAsset | None = None
        self._overlay_data: OverlayData | None = None
        self._fit_mode = False
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
        self.resetTransform()
        self._scene.setSceneRect(0, 0, 0, 0)

    def fit_to_view(self) -> None:
        if self._base_item is None:
            return
        self.resetTransform()
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_mode = True

    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage:
        del minimum_width, minimum_height
        asset = self._base_asset
        if asset is None:
            return QImage()
        return self._render_at(asset.width, asset.height)

    def baked_image(self, name: str) -> ImageAsset:
        asset = self._base_asset
        if asset is None:
            raise ValueError("No overlay content is available.")
        image = self._render_at(asset.width, asset.height).convertToFormat(
            QImage.Format.Format_RGB888
        )
        ptr = image.constBits()
        data = np.frombuffer(ptr, dtype=np.uint8).reshape((image.height(), image.width(), 3)).copy()
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


class OverlayViewer(QWidget):
    bake_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.visible_toggle = QCheckBox("Show overlay")
        self.visible_toggle.setChecked(True)
        self.canvas = OverlayCanvas()
        layout.addWidget(self.visible_toggle)
        layout.addWidget(self.canvas, 1)
        self.visible_toggle.toggled.connect(self.canvas.set_overlay_visible)

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
