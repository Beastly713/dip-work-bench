"""Frequency-domain operation presenters."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, MaskArtifact, OperationResult
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.widgets import (
    DisplayedExportTarget,
    ImageCanvas,
    MetricsPanel,
    OperationResultPresenter,
    SideBySideComparisonWidget,
)


class FourierSpectrumPresenter(OperationResultPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self._magnitude: ImageArtifact | None = None
        self._phase: ImageArtifact | None = None
        layout = QVBoxLayout(self)
        self.comparison = SideBySideComparisonWidget()
        self.metrics = MetricsPanel()
        self.toggle = QToolButton()
        self.toggle.setText("Phase Spectrum")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.phase_canvas = ImageCanvas()
        self.toggle.hide()
        self.phase_canvas.hide()
        self.toggle.toggled.connect(self._toggle)
        layout.addWidget(self.comparison, 1)
        layout.addWidget(self.metrics)
        layout.addWidget(self.toggle)
        layout.addWidget(self.phase_canvas)

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        self._magnitude = (
            result.primary_artifact if isinstance(result.primary_artifact, ImageArtifact) else None
        )
        self._phase = next(
            (
                a
                for a in result.artifacts
                if isinstance(a, ImageArtifact) and a.key == "fourier_phase"
            ),
            None,
        )
        if self._magnitude and isinstance(self._magnitude.data, ImageAsset):
            self.comparison.set_images(
                "Input", input_asset, "Magnitude Spectrum", self._magnitude.data
            )
        self.metrics.set_metrics(result.metrics, processing_time_ms=result.processing_time_ms)
        self.toggle.setVisible(self._phase is not None)
        if self._phase and isinstance(self._phase.data, ImageAsset):
            self.phase_canvas.set_image(self._phase.data)
        else:
            self.toggle.setChecked(False)
            self.phase_canvas.clear_image()
        self._refresh()

    def _toggle(self, visible: bool) -> None:
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.phase_canvas.setVisible(visible)
        self._refresh()

    def _refresh(self) -> None:
        if self.toggle.isChecked() and self._phase:
            self._set_displayed_export_target(DisplayedExportTarget(self._phase))
        elif self._magnitude:
            self._set_displayed_export_target(DisplayedExportTarget(self._magnitude))


class FrequencyFilterPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(
        self,
        _primary_key: str,
        label: str,
        input_key: str,
        mask_key: str,
        filtered_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(result_label=label, parent=parent)
        self._keys = (input_key, mask_key, filtered_key)
        self._artifacts: dict[str, ImageArtifact | MaskArtifact] = {}
        self.toggle = QToolButton()
        self.toggle.setText("Frequency-Domain Stages")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.canvases = [ImageCanvas(), ImageCanvas(), ImageCanvas()]
        for canvas, title in zip(
            self.canvases, ("Input Spectrum", "Frequency Mask", "Filtered Spectrum"), strict=True
        ):
            self.tabs.addTab(canvas, title)
        self.tabs.hide()
        self.toggle.toggled.connect(self._toggle)
        self.tabs.currentChanged.connect(lambda _index: self._refresh())
        self.layout().addWidget(self.toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._artifacts = {
            a.key: a
            for a in result.artifacts
            if isinstance(a, (ImageArtifact, MaskArtifact)) and isinstance(a.data, ImageAsset)
        }
        for canvas, key in zip(self.canvases, self._keys, strict=True):
            artifact = self._artifacts.get(key)
            if artifact and isinstance(artifact.data, ImageAsset):
                canvas.set_image(artifact.data)
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
        artifact = self._artifacts.get(self._keys[self.tabs.currentIndex()])
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)
