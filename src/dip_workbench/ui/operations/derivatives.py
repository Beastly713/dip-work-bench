"""Derivative operation presenters."""

from __future__ import annotations

from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QLabel, QToolButton, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, MaskArtifact, MatrixArtifact, OperationResult
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.widgets import (
    DisplayedExportTarget,
    MatrixViewer,
    MetricsPanel,
    OperationResultPresenter,
    TripleComparisonWidget,
)


class DerivativeTriplePresenter(OperationResultPresenter):
    def __init__(
        self,
        horizontal_key: str,
        vertical_key: str,
        result_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._horizontal_key = horizontal_key
        self._vertical_key = vertical_key
        self._result_key = result_key
        self._artifacts: dict[str, ImageArtifact | MaskArtifact] = {}
        layout = QVBoxLayout(self)
        self.triple = TripleComparisonWidget()
        self.selector = QComboBox()
        self.selector.addItem("Horizontal", horizontal_key)
        self.selector.addItem("Vertical", vertical_key)
        self.selector.addItem("Magnitude / Edge Result", result_key)
        self.selector.setCurrentIndex(2)
        self.metrics_panel = MetricsPanel()
        layout.addWidget(self.triple, 1)
        layout.addWidget(QLabel("Displayed/export response:"))
        layout.addWidget(self.selector)
        layout.addWidget(self.metrics_panel)
        self.selector.currentIndexChanged.connect(lambda _index: self._refresh_export_target())

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        del input_asset
        artifacts = {
            item.key: item
            for item in result.all_artifacts
            if isinstance(item, (ImageArtifact, MaskArtifact)) and isinstance(item.data, ImageAsset)
        }
        try:
            horizontal = artifacts[self._horizontal_key]
            vertical = artifacts[self._vertical_key]
            output = artifacts[self._result_key]
        except KeyError:
            self.clear_result()
            return
        self._artifacts = artifacts
        self.triple.set_images(
            (
                ("Horizontal Response", cast(ImageAsset, horizontal.data)),
                ("Vertical Response", cast(ImageAsset, vertical.data)),
                ("Magnitude / Edge Result", cast(ImageAsset, output.data)),
            )
        )
        self.metrics_panel.set_metrics(result.metrics, processing_time_ms=result.processing_time_ms)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._artifacts = {}
        self.triple.clear()
        self.metrics_panel.clear()
        super().clear_result()

    def _refresh_export_target(self) -> None:
        key = self.selector.currentData()
        artifact = self._artifacts.get(key)
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)


class LaplacianResponsePresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Laplacian Response", parent=parent)
        self._kernel: MatrixArtifact | None = None
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Response Details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.kernel_viewer = MatrixViewer()
        self.kernel_viewer.hide()
        self.details_toggle.toggled.connect(self._toggle_details)
        self.layout().addWidget(self.details_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.kernel_viewer)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._kernel = next(
            (item for item in result.artifacts if isinstance(item, MatrixArtifact)), None
        )
        if self._kernel is not None:
            self.kernel_viewer.set_matrix_data(self._kernel.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._kernel = None
        self.kernel_viewer.clear()
        self.details_toggle.setChecked(False)
        super().clear_result()

    def _toggle_details(self, visible: bool) -> None:
        self.details_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.kernel_viewer.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if self.details_toggle.isChecked() and self._kernel is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._kernel))
        elif self._image_artifact is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
        else:
            self._set_displayed_export_target(None)
