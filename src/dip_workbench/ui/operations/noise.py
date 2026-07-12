"""Noise operation presenter and parameter editor."""

from __future__ import annotations

from collections.abc import Mapping
from typing import SupportsInt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QToolButton, QVBoxLayout

from dip_workbench.core import ImageAsset
from dip_workbench.operations import HistogramArtifact, OperationResult, ParameterSpec
from dip_workbench.ui.operations.common import BeforeAfterImageWithMetricsPresenter
from dip_workbench.ui.panels import OperationParameterEditor
from dip_workbench.ui.widgets import (
    DisplayedExportTarget,
    GeneratedParameterEditor,
    HistogramWidget,
)


class NoiseParameterEditor(OperationParameterEditor):
    def __init__(self, schema: tuple[ParameterSpec, ...], parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(parent)
        self.editor = GeneratedParameterEditor(schema)
        self.editor.values_changed.connect(self._changed)
        self.regenerate_button = QPushButton("Regenerate")
        self.regenerate_button.clicked.connect(self._regenerate)
        self._values = {spec.key: spec.default for spec in schema}
        layout = QVBoxLayout(self)
        layout.addWidget(self.editor)
        layout.addWidget(self.regenerate_button)

    def set_values(self, values: Mapping[str, object]) -> None:
        self._values.update(values)
        self.editor.set_values(self._values)

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        self.editor.set_validation_errors(errors)

    def _changed(self, values: object) -> None:
        if isinstance(values, Mapping):
            self._values.update(values)
            self.values_changed.emit(dict(self._values))

    def _regenerate(self) -> None:
        raw_seed = self._values.get("seed", 42)
        seed = int(raw_seed) if isinstance(raw_seed, SupportsInt) else 42
        self._values["seed"] = (seed * 1103515245 + 12345) % 2147483648
        self.editor.set_values(self._values)
        self.values_changed.emit(dict(self._values))


class AddNoisePresenter(BeforeAfterImageWithMetricsPresenter):
    def __init__(self, parent=None) -> None:  # type: ignore[no-untyped-def]
        super().__init__(result_label="Noisy Result", parent=parent)
        self._noise_artifact: HistogramArtifact | None = None
        self.noise_toggle = QToolButton()
        self.noise_toggle.setText("Noise Distribution")
        self.noise_toggle.setCheckable(True)
        self.noise_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.noise_graph = HistogramWidget()
        self.noise_graph.hide()
        self.noise_toggle.toggled.connect(self._toggle)
        self.layout().addWidget(self.noise_toggle)  # type: ignore[union-attr]
        self.layout().addWidget(self.noise_graph)  # type: ignore[union-attr]

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        super().present(input_asset, result)
        self._noise_artifact = next(
            (artifact for artifact in result.artifacts if isinstance(artifact, HistogramArtifact)),
            None,
        )
        if self._noise_artifact is not None:
            self.noise_graph.set_histogram_data(self._noise_artifact.data)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self._noise_artifact = None
        self.noise_graph.clear()
        self.noise_toggle.setChecked(False)
        super().clear_result()

    def _toggle(self, visible: bool) -> None:
        self.noise_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.noise_graph.setVisible(visible)
        self._refresh_export_target()

    def _refresh_export_target(self) -> None:
        if self.noise_toggle.isChecked() and self._noise_artifact is not None:
            self._set_displayed_export_target(
                DisplayedExportTarget(self._noise_artifact, self.noise_graph)
            )
        elif self._image_artifact is not None:
            self._set_displayed_export_target(DisplayedExportTarget(self._image_artifact))
