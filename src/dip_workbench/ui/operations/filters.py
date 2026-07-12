"""Filter operation presenters and editors."""

from __future__ import annotations

from collections.abc import Mapping
from typing import SupportsInt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTabWidget, QToolButton

from dip_workbench.core import ImageAsset
from dip_workbench.operations import MatrixArtifact, OperationResult
from dip_workbench.operations.m05.custom_convolution import identity_kernel, weighted_average_kernel
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.panels import OperationParameterEditor
from dip_workbench.ui.widgets import DisplayedExportTarget, GeneratedParameterEditor, MatrixViewer


class ConvolutionParameterEditor(OperationParameterEditor):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        from dip_workbench.operations.m05.custom_convolution import CUSTOM_CONVOLUTION_DEFINITION

        super().__init__(parent)
        self.editor = GeneratedParameterEditor(CUSTOM_CONVOLUTION_DEFINITION.parameter_schema)
        self.editor.values_changed.connect(self._changed)
        from PySide6.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        self._values = {
            spec.key: spec.default for spec in CUSTOM_CONVOLUTION_DEFINITION.parameter_schema
        }

    def set_values(self, values: Mapping[str, object]) -> None:
        self._values.update(values)
        self._sync_kernel()
        self.editor.set_values(self._values)

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        self.editor.set_validation_errors(errors)

    def _changed(self, values: object) -> None:
        if isinstance(values, Mapping):
            self._values.update(values)
        self._sync_kernel()
        self.values_changed.emit(dict(self._values))

    def _sync_kernel(self) -> None:
        raw_size = self._values.get("kernel_size", 3)
        size = int(raw_size) if isinstance(raw_size, SupportsInt) else 3
        preset = self._values.get("preset")
        if preset == "identity":
            self._values["kernel"] = identity_kernel(size)
            self.editor.controls["kernel"].setEnabled(False)
        elif preset == "weighted_average":
            self._values["kernel"] = weighted_average_kernel(size)
            self.editor.controls["kernel"].setEnabled(False)
        else:
            self.editor.controls["kernel"].setEnabled(True)


class CustomConvolutionPresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Convolution Result", parent=parent)
        self._matrices: dict[str, MatrixArtifact] = {}
        self.kernel_toggle = QToolButton()
        self.kernel_toggle.setText("Kernel Details")
        self.kernel_toggle.setCheckable(True)
        self.kernel_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.tabs = QTabWidget()
        self.resolved = MatrixViewer()
        self.flipped = MatrixViewer()
        self.tabs.addTab(self.resolved, "Resolved Kernel")
        self.tabs.addTab(self.flipped, "Flipped Kernel Used")
        self.tabs.hide()
        self.kernel_toggle.toggled.connect(self._toggle)
        self.tabs.currentChanged.connect(lambda _index: self._refresh_export_target())
        self.layout().addWidget(self.kernel_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.tabs)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._matrices = {
            artifact.key: artifact
            for artifact in result.artifacts
            if isinstance(artifact, MatrixArtifact)
        }
        if "resolved_kernel" in self._matrices:
            self.resolved.set_matrix_data(self._matrices["resolved_kernel"].data)
        if "flipped_kernel" in self._matrices:
            self.flipped.set_matrix_data(self._matrices["flipped_kernel"].data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._matrices = {}
        self.resolved.set_matrix_data([[0]])
        self.flipped.set_matrix_data([[0]])
        self.kernel_toggle.setChecked(False)
        super().clear_result()

    def _toggle(self, visible: bool) -> None:
        self.kernel_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.tabs.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if not self.kernel_toggle.isChecked():
            if self._image_artifact is not None:
                self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
            return
        key = ("resolved_kernel", "flipped_kernel")[self.tabs.currentIndex()]
        artifact = self._matrices.get(key)
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)
