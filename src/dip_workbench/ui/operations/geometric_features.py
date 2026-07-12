"""Geometric feature overlay presenter."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import (
    ImageArtifact,
    MaskArtifact,
    OperationResult,
    OverlayArtifact,
    OverlayData,
    TableArtifact,
)
from dip_workbench.ui.widgets import (
    DataTableWidget,
    DisplayedExportTarget,
    ImageCanvas,
    MetricsPanel,
    OperationResultPresenter,
    OverlayViewer,
)


class GeometricFeaturePresenter(OperationResultPresenter):
    def __init__(
        self,
        stage_artifact_key: str,
        stage_tab_label: str,
        table_artifact_key: str,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._stage_key = stage_artifact_key
        self._table_key = table_artifact_key
        self._overlay: OverlayArtifact | None = None
        self._stage: ImageArtifact | MaskArtifact | None = None
        self._table: TableArtifact | None = None
        layout = QVBoxLayout(self)
        self.viewer = OverlayViewer()
        self.metrics_panel = MetricsPanel()
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Detection Details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.stage_canvas = ImageCanvas()
        self.table = DataTableWidget()
        self.tabs.addTab(self.stage_canvas, stage_tab_label)
        self.tabs.addTab(self.table, "Detections Table")
        self.tabs.hide()
        layout.addWidget(self.viewer, 1)
        layout.addWidget(self.metrics_panel)
        layout.addWidget(self.details_toggle)
        layout.addWidget(self.tabs)
        self.details_toggle.toggled.connect(self._toggle_details)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        overlay = result.primary_artifact
        if not isinstance(overlay, OverlayArtifact) or not isinstance(overlay.data, OverlayData):
            self.clear_result()
            return
        self._overlay = overlay
        self.viewer.set_content(input_asset, overlay.data)
        self.metrics_panel.set_metrics(result.metrics, processing_time_ms=result.processing_time_ms)
        self._stage = next(
            (
                item
                for item in result.artifacts
                if isinstance(item, (ImageArtifact, MaskArtifact)) and item.key == self._stage_key
            ),
            None,
        )
        if self._stage is not None and isinstance(self._stage.data, ImageAsset):
            self.stage_canvas.set_image(self._stage.data)
        self._table = next(
            (
                item
                for item in result.artifacts
                if isinstance(item, TableArtifact) and item.key == self._table_key
            ),
            None,
        )
        if self._table is not None:
            self.table.set_table_data(self._table.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._overlay = None
        self._stage = None
        self._table = None
        self.viewer.clear()
        self.stage_canvas.clear_image()
        self.table.clear()
        self.metrics_panel.clear()
        self.details_toggle.setChecked(False)
        super().clear_result()

    def _toggle_details(self, visible: bool) -> None:
        self.details_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.tabs.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if not self.details_toggle.isChecked():
            self._set_displayed_export_target(
                DisplayedExportTarget(self._overlay, self.viewer) if self._overlay else None
            )
            return
        if self.tabs.currentIndex() == 0 and self._stage is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._stage))
        elif self._table is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._table))
        else:
            self._set_displayed_export_target(None)
