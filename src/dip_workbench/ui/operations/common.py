"""Small reusable presenters for current before/after operations."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import CurveArtifact, ImageArtifact, MaskArtifact, OperationResult
from dip_workbench.ui.widgets import (
    BeforeAfterComparisonWidget,
    DisplayedExportTarget,
    MetricsPanel,
    OperationResultPresenter,
    TransformationCurveWidget,
)


class BeforeAfterImagePresenter(OperationResultPresenter):
    def __init__(
        self,
        *,
        input_label: str = "Input",
        result_label: str = "Result",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._input_label = input_label
        self._result_label = result_label
        self._image_artifact: ImageArtifact | MaskArtifact | None = None
        layout = QVBoxLayout(self)
        self.comparison = BeforeAfterComparisonWidget()
        layout.addWidget(self.comparison, 1)

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        output = result.primary_artifact.data
        if not isinstance(output, ImageAsset) or not isinstance(
            result.primary_artifact, (ImageArtifact, MaskArtifact)
        ):
            self.clear_result()
            return
        self._image_artifact = result.primary_artifact
        self.comparison.set_images(
            input_asset,
            output,
            input_label=self._input_label,
            result_label=self._result_label,
        )
        self._set_displayed_export_target(DisplayedExportTarget(result.primary_artifact))

    def clear_result(self) -> None:
        self.comparison.clear()
        self._image_artifact = None
        super().clear_result()

    def supports_before_after_comparison(self) -> bool:
        return self._image_artifact is not None

    def activate_before_after_comparison(self) -> bool:
        if self._image_artifact is None:
            return False
        self.comparison.focus_comparison_controls()
        return True


class BeforeAfterImageWithMetricsPresenter(BeforeAfterImagePresenter):
    def __init__(self, *, result_label: str = "Result", parent: QWidget | None = None) -> None:
        super().__init__(result_label=result_label, parent=parent)
        self.metrics_panel = MetricsPanel()
        self.layout().addWidget(self.metrics_panel)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self.metrics_panel.set_metrics(result.metrics, processing_time_ms=result.processing_time_ms)

    def clear_result(self) -> None:
        self.metrics_panel.clear()
        super().clear_result()


class BeforeAfterImageWithCurvePresenter(BeforeAfterImagePresenter):
    def __init__(
        self,
        *,
        result_label: str = "Result",
        curve_label: str = "Transformation Curve",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(result_label=result_label, parent=parent)
        self._curve_artifact: CurveArtifact | None = None
        self.curve_toggle = QToolButton()
        self.curve_toggle.setText(curve_label)
        self.curve_toggle.setCheckable(True)
        self.curve_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.curve_widget = TransformationCurveWidget()
        self.curve_widget.hide()
        self.curve_toggle.toggled.connect(self._toggle_curve)
        self.layout().addWidget(self.curve_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.curve_widget)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._curve_artifact = next(
            (artifact for artifact in result.artifacts if isinstance(artifact, CurveArtifact)),
            None,
        )
        if self._curve_artifact is not None:
            self.curve_widget.set_curve_data(self._curve_artifact.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._curve_artifact = None
        self.curve_widget.clear()
        self.curve_toggle.setChecked(False)
        super().clear_result()

    def _toggle_curve(self, visible: bool) -> None:
        self.curve_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.curve_widget.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if self.curve_toggle.isChecked() and self._curve_artifact is not None:
            self._set_displayed_export_target(
                DisplayedExportTarget(self._curve_artifact, self.curve_widget)
            )
        elif self._image_artifact is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
        else:
            self._set_displayed_export_target(None)
