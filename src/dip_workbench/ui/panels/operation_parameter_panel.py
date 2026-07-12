"""Generic host for operation-specific parameter editors and actions."""

from collections.abc import Mapping

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from dip_workbench.controllers import OperationController, OperationWorkspaceState
from dip_workbench.operations import ApplyPolicy


class OperationParameterEditor(QWidget):
    values_changed = Signal(object)

    def set_values(self, values: Mapping[str, object]) -> None:
        """Receive the complete parameter mapping."""

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        """Receive validation messages keyed by parameter."""


class OperationParameterPanel(QWidget):
    preview_requested = Signal()
    apply_requested = Signal()
    reset_requested = Signal()
    apply_candidate_changed = Signal(object)
    parameter_values_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel("Parameters")
        heading.setStyleSheet("font-size:17px;font-weight:600")
        layout.addWidget(heading)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.host = QWidget()
        self.host_layout = QVBoxLayout(self.host)
        self.scroll_area.setWidget(self.host)
        layout.addWidget(self.scroll_area, 1)
        self.validation_summary = QLabel()
        self.validation_summary.setWordWrap(True)
        self.validation_summary.setStyleSheet("color:#b91c1c")
        layout.addWidget(self.validation_summary)
        self.candidate_selector = QComboBox()
        self.candidate_selector.currentIndexChanged.connect(self._candidate_changed)
        layout.addWidget(self.candidate_selector)
        self.preview_button = QPushButton("Preview")
        self.apply_button = QPushButton("Apply to Current")
        self.reset_button = QPushButton("Reset Parameters")
        self.preview_button.clicked.connect(self.preview_requested)
        self.apply_button.clicked.connect(self.apply_requested)
        self.reset_button.clicked.connect(self.reset_requested)
        layout.addWidget(self.preview_button)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.reset_button)
        self._editor: OperationParameterEditor | None = None

    def configure(self, controller: OperationController) -> None:
        definition = controller.active_definition
        if definition is None:
            return
        if self._editor is not None:
            self._editor.setParent(None)
            self._editor = None
        while self.host_layout.count():
            item = self.host_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        if definition.custom_parameter_factory is not None:
            candidate = definition.custom_parameter_factory()
            if isinstance(candidate, OperationParameterEditor):
                self._editor = candidate
                self._editor.values_changed.connect(self.parameter_values_changed)
                self.host_layout.addWidget(self._editor)
        if self._editor is None and definition.parameter_schema:
            from dip_workbench.ui.widgets.generated_parameter_editor import (
                GeneratedParameterEditor,
            )

            self._editor = GeneratedParameterEditor(definition.parameter_schema)
            self._editor.values_changed.connect(self.parameter_values_changed)
            self.host_layout.addWidget(self._editor)
        if self._editor is None:
            message = QLabel("No parameters required.")
            message.setWordWrap(True)
            self.host_layout.addWidget(message)
        self.refresh(controller)

    def refresh(self, controller: OperationController) -> None:
        definition = controller.active_definition
        if definition is None:
            return
        processing = controller.workspace_state is OperationWorkspaceState.PROCESSING
        self.preview_button.setText(controller.preview_action_label)
        self.preview_button.setEnabled(controller.can_preview and not processing)
        self.apply_button.setVisible(definition.apply_policy is not ApplyPolicy.NONE)
        self.apply_button.setEnabled(controller.can_apply and not processing)
        self.reset_button.setEnabled(not processing)
        self.validation_summary.setText("\n".join(controller.parameter_errors.values()))
        explicit = definition.apply_policy is ApplyPolicy.EXPLICIT_CANDIDATES
        self.candidate_selector.setVisible(explicit)
        self.candidate_selector.blockSignals(True)
        self.candidate_selector.clear()
        if explicit and controller.active_result:
            self.candidate_selector.addItem("Select result…", None)
            for candidate in controller.active_result.apply_candidates:
                self.candidate_selector.addItem(candidate.label, candidate.artifact_key)
            index = self.candidate_selector.findData(controller.selected_apply_candidate)
            self.candidate_selector.setCurrentIndex(max(0, index))
        self.candidate_selector.blockSignals(False)
        if self._editor is not None:
            self._editor.set_values(controller.parameter_values)
            self._editor.set_validation_errors(controller.parameter_errors)

    def _candidate_changed(self, index: int) -> None:
        if index >= 0:
            self.apply_candidate_changed.emit(self.candidate_selector.itemData(index))
