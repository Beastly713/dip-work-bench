"""Sharpening operation presenters."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, MatrixArtifact, OperationResult
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.widgets import DisplayedExportTarget, ImageCanvas, MatrixViewer


class LaplacianSharpeningPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Sharpened Result", parent=parent)
        self._response: ImageArtifact | None = None
        self._kernel: MatrixArtifact | None = None
        self.details_toggle = QToolButton()
        self.details_toggle.setText("Laplacian Details")
        self.details_toggle.setCheckable(True)
        self.details_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.response_canvas = ImageCanvas()
        self.kernel_viewer = MatrixViewer()
        self.tabs.addTab(self.response_canvas, "Response")
        self.tabs.addTab(self.kernel_viewer, "Kernel")
        self.tabs.hide()
        self.details_toggle.toggled.connect(self._toggle_details)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())
        self.layout().addWidget(self.details_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._response = next(
            (
                item
                for item in result.artifacts
                if isinstance(item, ImageArtifact) and item.key == "laplacian_display"
            ),
            None,
        )
        self._kernel = next(
            (item for item in result.artifacts if isinstance(item, MatrixArtifact)), None
        )
        if self._response is not None and isinstance(self._response.data, ImageAsset):
            self.response_canvas.set_image(self._response.data)
        if self._kernel is not None:
            self.kernel_viewer.set_matrix_data(self._kernel.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._response = None
        self._kernel = None
        self.response_canvas.clear_image()
        self.kernel_viewer.clear()
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
            if self._image_artifact is not None:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        if self.tabs.currentIndex() == 0 and self._response is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._response))
        elif self._kernel is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._kernel))
        else:
            self._set_displayed_export_target(None)


class DetailSharpeningPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, _primary_key: str = "unsharp_image", parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Sharpened Result", parent=parent)
        self._blurred: ImageArtifact | None = None
        self._detail: ImageArtifact | None = None
        self.stages_toggle = QToolButton()
        self.stages_toggle.setText("Sharpening Stages")
        self.stages_toggle.setCheckable(True)
        self.stages_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.blurred_canvas = ImageCanvas()
        self.detail_canvas = ImageCanvas()
        self.tabs.addTab(self.blurred_canvas, "Blurred Image")
        self.tabs.addTab(self.detail_canvas, "Detail Mask")
        self.tabs.hide()
        self.stages_toggle.toggled.connect(self._toggle_stages)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())
        self.layout().addWidget(self.stages_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        image_artifacts = {
            item.key: item for item in result.artifacts if isinstance(item, ImageArtifact)
        }
        self._blurred = image_artifacts.get("blurred_image")
        self._detail = image_artifacts.get("detail_display")
        if self._blurred is not None and isinstance(self._blurred.data, ImageAsset):
            self.blurred_canvas.set_image(self._blurred.data)
        if self._detail is not None and isinstance(self._detail.data, ImageAsset):
            self.detail_canvas.set_image(self._detail.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._blurred = None
        self._detail = None
        self.blurred_canvas.clear_image()
        self.detail_canvas.clear_image()
        self.stages_toggle.setChecked(False)
        super().clear_result()

    def _toggle_stages(self, visible: bool) -> None:
        self.stages_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.tabs.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if not self.stages_toggle.isChecked():
            if self._image_artifact is not None:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        if self.tabs.currentIndex() == 0 and self._blurred is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._blurred))
        elif self._detail is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._detail))
        else:
            self._set_displayed_export_target(None)
