"""Segmentation operation presenters."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, MaskArtifact, OperationResult
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.widgets import DisplayedExportTarget, ImageCanvas


class RangeThresholdPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Intensity-Range Mask", parent=parent)
        self._overlay: ImageArtifact | None = None
        self.toggle = QToolButton()
        self.toggle.setText("Segmentation View")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.canvas = ImageCanvas()
        self.canvas.hide()
        self.toggle.toggled.connect(self._toggle)
        self.layout().addWidget(self.toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.canvas)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._overlay = next(
            (
                a
                for a in result.artifacts
                if isinstance(a, ImageArtifact) and a.key == "range_overlay"
            ),
            None,
        )
        if self._overlay and isinstance(self._overlay.data, ImageAsset):
            self.canvas.set_image(self._overlay.data)
        self._refresh()

    def _toggle(self, visible: bool) -> None:
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.canvas.setVisible(visible)
        self._refresh()

    def _refresh(self) -> None:
        if self.toggle.isChecked() and self._overlay:
            self._set_displayed_export_target(DisplayedExportTarget(self._overlay))
        elif self._image_artifact:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))


class ColourRangePresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Colour-Range Mask", parent=parent)
        self._artifacts: dict[str, ImageArtifact] = {}
        self.toggle = QToolButton()
        self.toggle.setText("Segmentation Views")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.extracted = ImageCanvas()
        self.overlay = ImageCanvas()
        self.tabs.addTab(self.extracted, "Extracted Region")
        self.tabs.addTab(self.overlay, "Overlay")
        self.tabs.hide()
        self.toggle.toggled.connect(self._toggle)
        self.tabs.currentChanged.connect(lambda _index: self._refresh())
        self.layout().addWidget(self.toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._artifacts = {a.key: a for a in result.artifacts if isinstance(a, ImageArtifact)}
        if "extracted_region" in self._artifacts:
            self.extracted.set_image(self._artifacts["extracted_region"].data)  # type: ignore[arg-type]
        if "colour_overlay" in self._artifacts:
            self.overlay.set_image(self._artifacts["colour_overlay"].data)  # type: ignore[arg-type]
        self._refresh()

    def _toggle(self, visible: bool) -> None:
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.tabs.setVisible(visible)
        self._refresh()

    def _refresh(self) -> None:
        if not self.toggle.isChecked():
            if self._image_artifact:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        key = ("extracted_region", "colour_overlay")[self.tabs.currentIndex()]
        artifact = self._artifacts.get(key)
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)


class AdaptiveThresholdPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Adaptive Threshold Mask", parent=parent)
        self._otsu: MaskArtifact | None = None
        self.toggle = QToolButton()
        self.toggle.setText("Global Otsu Comparison")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.canvas = ImageCanvas()
        self.toggle.hide()
        self.canvas.hide()
        self.toggle.toggled.connect(self._toggle)
        self.layout().addWidget(self.toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.canvas)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._otsu = next(
            (
                a
                for a in result.artifacts
                if isinstance(a, MaskArtifact) and a.key == "global_otsu_mask"
            ),
            None,
        )
        self.toggle.setVisible(self._otsu is not None)
        if self._otsu and isinstance(self._otsu.data, ImageAsset):
            self.canvas.set_image(self._otsu.data)
        else:
            self.canvas.clear_image()
            self.toggle.setChecked(False)
        self._refresh()

    def _toggle(self, visible: bool) -> None:
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.canvas.setVisible(visible)
        self._refresh()

    def _refresh(self) -> None:
        if self.toggle.isChecked() and self._otsu:
            self._set_displayed_export_target(DisplayedExportTarget(self._otsu))
        elif self._image_artifact:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
