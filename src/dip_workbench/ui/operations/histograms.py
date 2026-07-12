"""Histogram operation presenters."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ImageAsset
from dip_workbench.operations import (
    CurveArtifact,
    GraphData,
    HistogramArtifact,
    ImageArtifact,
    OperationResult,
)
from dip_workbench.ui.operations.common import BeforeAfterImagePresenter
from dip_workbench.ui.widgets import (
    DisplayedExportTarget,
    GraphWidget,
    MetricsPanel,
    OperationResultPresenter,
    TransformationCurveWidget,
)


def _subset_graph(graph: GraphData, labels: set[str]) -> GraphData:
    return GraphData(
        tuple(series for series in graph.series if series.label in labels),
        title=graph.title,
        x_label=graph.x_label,
        y_label=graph.y_label,
        style=graph.style,
    )


class HistogramAnalysisPresenter(OperationResultPresenter):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.view_selector = QComboBox()
        self.channel_toggles = {
            "Red": QCheckBox("Red"),
            "Green": QCheckBox("Green"),
            "Blue": QCheckBox("Blue"),
        }
        for toggle in self.channel_toggles.values():
            toggle.setChecked(True)
            toggle.toggled.connect(self._refresh_view)
        self.view_selector.currentIndexChanged.connect(self._refresh_view)
        controls.addWidget(self.view_selector)
        for toggle in self.channel_toggles.values():
            controls.addWidget(toggle)
        controls.addStretch()
        self.graph = GraphWidget()
        self.metrics = MetricsPanel()
        layout.addLayout(controls)
        layout.addWidget(self.graph, 1)
        layout.addWidget(self.metrics)
        self._artifacts: dict[str, HistogramArtifact] = {}
        self._metrics: dict[str, object] = {}

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        del input_asset
        self.clear_result()
        self._artifacts = {
            artifact.key: artifact
            for artifact in result.all_artifacts
            if isinstance(artifact, HistogramArtifact)
        }
        self._metrics = dict(result.metrics)
        self.view_selector.blockSignals(True)
        self.view_selector.clear()
        self.view_selector.addItem("Grayscale", "grayscale_histogram")
        if "rgb_histogram" in self._artifacts:
            self.view_selector.addItem("RGB", "rgb_histogram")
            self.view_selector.setCurrentIndex(1)
        self.view_selector.blockSignals(False)
        self.metrics.set_metrics(result.metrics)
        self._refresh_view()

    def clear_result(self) -> None:
        self.graph.clear()
        self.metrics.clear()
        self._artifacts = {}
        self._metrics = {}
        super().clear_result()

    def _refresh_view(self) -> None:
        key = self.view_selector.currentData()
        artifact = self._artifacts.get(key) if isinstance(key, str) else None
        rgb_visible = key == "rgb_histogram"
        for toggle in self.channel_toggles.values():
            toggle.setVisible(rgb_visible)
        if artifact is None:
            self._set_displayed_export_target(None)
            return
        graph = artifact.data
        if rgb_visible and isinstance(graph, GraphData):
            checked = {
                label for label, toggle in self.channel_toggles.items() if toggle.isChecked()
            }
            if not checked:
                sender = self.sender()
                if isinstance(sender, QCheckBox):
                    sender.blockSignals(True)
                    sender.setChecked(True)
                    sender.blockSignals(False)
                    checked.add(sender.text())
                else:
                    checked.add("Red")
                    self.channel_toggles["Red"].setChecked(True)
            graph = _subset_graph(graph, checked)
            artifact = HistogramArtifact("visible_histogram", "Visible Histogram", graph)
        self.graph.set_graph_data(graph)
        self._set_displayed_export_target(DisplayedExportTarget(artifact, self.graph))


class HistogramEqualizationPresenter(BeforeAfterImagePresenter):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(result_label="Equalized Result", parent=parent)
        self._image_artifact: ImageArtifact | None = None
        self._analysis_artifacts: dict[str, HistogramArtifact | CurveArtifact] = {}
        self.analysis_toggle = QToolButton()
        self.analysis_toggle.setText("Equalization Analysis")
        self.analysis_toggle.setCheckable(True)
        self.analysis_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.histogram_graph = GraphWidget()
        self.cdf_graph = TransformationCurveWidget()
        self.mapping_graph = TransformationCurveWidget()
        self.tabs.addTab(self.histogram_graph, "Histogram")
        self.tabs.addTab(self.cdf_graph, "CDF")
        self.tabs.addTab(self.mapping_graph, "Mapping")
        self.tabs.hide()
        self.analysis_toggle.toggled.connect(self._toggle)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())
        self.layout().addWidget(self.analysis_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._image_artifact = (
            result.primary_artifact if isinstance(result.primary_artifact, ImageArtifact) else None
        )
        self._analysis_artifacts = {
            artifact.key: artifact
            for artifact in result.artifacts
            if isinstance(artifact, (HistogramArtifact, CurveArtifact))
        }
        if "histogram_comparison" in self._analysis_artifacts:
            self.histogram_graph.set_graph_data(
                self._analysis_artifacts["histogram_comparison"].data
            )
        if "input_cdf" in self._analysis_artifacts:
            self.cdf_graph.set_curve_data(self._analysis_artifacts["input_cdf"].data)
        if "equalization_mapping" in self._analysis_artifacts:
            self.mapping_graph.set_curve_data(self._analysis_artifacts["equalization_mapping"].data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self.histogram_graph.clear()
        self.cdf_graph.clear()
        self.mapping_graph.clear()
        self.analysis_toggle.setChecked(False)
        self._analysis_artifacts = {}
        super().clear_result()

    def _toggle(self, visible: bool) -> None:
        self.analysis_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.tabs.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if not self.analysis_toggle.isChecked():
            if self._image_artifact is not None:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        keys = ("histogram_comparison", "input_cdf", "equalization_mapping")
        widgets = (self.histogram_graph, self.cdf_graph, self.mapping_graph)
        key = keys[self.tabs.currentIndex()]
        artifact = self._analysis_artifacts.get(key)
        self._set_displayed_export_target(
            DisplayedExportTarget(artifact, widgets[self.tabs.currentIndex()]) if artifact else None
        )
