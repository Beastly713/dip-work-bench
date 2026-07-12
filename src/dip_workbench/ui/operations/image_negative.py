"""Custom parameter and result interfaces for M03-01."""

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ImageAsset
from dip_workbench.operations import CurveArtifact, ImageArtifact, OperationResult
from dip_workbench.ui.panels import OperationParameterEditor
from dip_workbench.ui.widgets import (
    BeforeAfterComparisonWidget,
    DisplayedExportTarget,
    OperationResultPresenter,
    TransformationCurveWidget,
)


class ImageNegativeParameterEditor(OperationParameterEditor):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.colour_handling_combo = QComboBox()
        for label, value in (
            ("Luminance only", "luminance"),
            ("Each RGB channel", "channels"),
            ("Grayscale output", "grayscale"),
        ):
            self.colour_handling_combo.addItem(label, value)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #b91c1c;")
        layout.addRow("Colour Handling", self.colour_handling_combo)
        layout.addRow(self.error_label)
        self.colour_handling_combo.currentIndexChanged.connect(self._emit_values)

    def _emit_values(self) -> None:
        self.values_changed.emit({"colour_handling": self.colour_handling_combo.currentData()})

    def set_values(self, values: Mapping[str, object]) -> None:
        index = self.colour_handling_combo.findData(values.get("colour_handling"))
        self.colour_handling_combo.blockSignals(True)
        self.colour_handling_combo.setCurrentIndex(max(index, 0))
        self.colour_handling_combo.blockSignals(False)

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        self.error_label.setText(errors.get("colour_handling", ""))


class ImageNegativeResultPresenter(OperationResultPresenter):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.comparison = BeforeAfterComparisonWidget()
        layout.addWidget(self.comparison, 1)
        self.mapping_toggle = QToolButton()
        self.mapping_toggle.setText("Input–Output Mapping")  # noqa: RUF001
        self.mapping_toggle.setCheckable(True)
        self.mapping_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.mapping_curve = TransformationCurveWidget()
        self.mapping_curve.hide()
        self.mapping_toggle.toggled.connect(self._toggle_mapping)
        layout.addWidget(self.mapping_toggle)
        layout.addWidget(self.mapping_curve)
        self._image_artifact: ImageArtifact | None = None
        self._curve_artifact: CurveArtifact | None = None

    def _toggle_mapping(self, visible: bool) -> None:
        self.mapping_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.mapping_curve.setVisible(visible)
        self._refresh_export_target()

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        output = result.primary_artifact.data
        if not isinstance(output, ImageAsset):
            self.clear_result()
            return
        self._image_artifact = (
            result.primary_artifact if isinstance(result.primary_artifact, ImageArtifact) else None
        )
        self._curve_artifact = next(
            (artifact for artifact in result.artifacts if isinstance(artifact, CurveArtifact)),
            None,
        )
        self.comparison.set_images(
            input_asset,
            output,
            input_label="Input",
            result_label="Negative Result",
        )
        if self._curve_artifact is not None:
            self.mapping_curve.set_curve_data(self._curve_artifact.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self.comparison.clear()
        self.mapping_curve.clear()
        self.mapping_toggle.setChecked(False)
        self._image_artifact = None
        self._curve_artifact = None
        super().clear_result()

    def supports_before_after_comparison(self) -> bool:
        return self._image_artifact is not None

    def activate_before_after_comparison(self) -> bool:
        if self._image_artifact is None:
            return False
        self.comparison.focus_comparison_controls()
        return True

    def _refresh_export_target(self) -> None:
        if self.mapping_toggle.isChecked() and self._curve_artifact is not None:
            self._set_displayed_export_target(
                DisplayedExportTarget(self._curve_artifact, self.mapping_curve)
            )
        elif self._image_artifact is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
        else:
            self._set_displayed_export_target(None)
