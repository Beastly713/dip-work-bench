"""Advanced edge operation presenters."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, MaskArtifact, OperationResult
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.widgets import DisplayedExportTarget, ImageCanvas


class _StagePresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(
        self,
        *,
        result_label: str,
        toggle_label: str,
        tabs: tuple[tuple[str, str], ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(result_label=result_label, parent=parent)
        self._tab_specs = tabs
        self._artifacts: dict[str, ImageArtifact | MaskArtifact] = {}
        self.toggle = QToolButton()
        self.toggle.setText(toggle_label)
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.canvases: list[ImageCanvas] = []
        for label, _key in tabs:
            canvas = ImageCanvas()
            self.canvases.append(canvas)
            self.tabs.addTab(canvas, label)
        self.tabs.hide()
        self.toggle.toggled.connect(self._toggle)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())
        self.layout().addWidget(self.toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._artifacts = {
            item.key: item
            for item in result.all_artifacts
            if isinstance(item, (ImageArtifact, MaskArtifact)) and isinstance(item.data, ImageAsset)
        }
        for canvas, (_label, key) in zip(self.canvases, self._tab_specs, strict=True):
            artifact = self._artifacts.get(key)
            if artifact is not None and isinstance(artifact.data, ImageAsset):
                canvas.set_image(artifact.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._artifacts = {}
        for canvas in self.canvases:
            canvas.clear_image()
        self.toggle.setChecked(False)
        super().clear_result()

    def _toggle(self, visible: bool) -> None:
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)
        self.tabs.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if not self.toggle.isChecked():
            if self._image_artifact is not None:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        key = self._tab_specs[self.tabs.currentIndex()][1]
        artifact = self._artifacts.get(key)
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)


class LoGEdgePresenter(_StagePresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(
            result_label="LoG Edge Map",
            toggle_label="LoG Stages",
            tabs=(("Smoothed Input", "log_smoothed"), ("Signed Response", "log_response_display")),
            parent=parent,
        )


class DoGEdgePresenter(_StagePresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(
            result_label="DoG Edge Map",
            toggle_label="DoG Stages",
            tabs=(
                ("Small-Sigma Blur", "dog_small_blur"),
                ("Large-Sigma Blur", "dog_large_blur"),
                ("Signed Response", "dog_response_display"),
            ),
            parent=parent,
        )
