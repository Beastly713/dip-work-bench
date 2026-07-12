"""State-driven generic operation result area."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.controllers import OperationController, OperationWorkspaceState


class ResultWorkspaceHost(QWidget):
    cancel_requested = Signal()
    open_image_requested = Signal()
    correct_inputs_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self._pages = {}
        self._messages = {}
        self._result_widget: QWidget | None = None
        states = (
            (OperationWorkspaceState.NO_OPERATION, "No operation selected."),
            (OperationWorkspaceState.MISSING_INPUT, "Load or correct the required inputs."),
            (
                OperationWorkspaceState.READY,
                "Inputs are ready.\nSelect Preview or Run to process the operation.",
            ),
            (OperationWorkspaceState.PROCESSING, "Processing…"),
            (OperationWorkspaceState.RESULT, "Result"),
            (OperationWorkspaceState.FAILURE, "The operation could not be completed."),
        )
        for state, text in states:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            page_layout.addStretch()
            message = QLabel(text)
            message.setWordWrap(True)
            message.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_layout.addWidget(message)
            self._pages[state] = page
            self._messages[state] = message
            if state is OperationWorkspaceState.MISSING_INPUT:
                self.open_button = QPushButton("Open Image")
                self.open_button.clicked.connect(self.open_image_requested)
                page_layout.addWidget(self.open_button)
            elif state is OperationWorkspaceState.PROCESSING:
                self.progress_bar = QProgressBar()
                self.progress_message = QLabel()
                cancel = QPushButton("Cancel")
                cancel.clicked.connect(self.cancel_requested)
                page_layout.addWidget(self.progress_bar)
                page_layout.addWidget(self.progress_message)
                page_layout.addWidget(cancel)
            elif state is OperationWorkspaceState.RESULT:
                self.result_summary = QLabel()
                self.result_summary.setWordWrap(True)
                self.result_widget_host = QVBoxLayout()
                page_layout.addWidget(self.result_summary)
                page_layout.addLayout(self.result_widget_host)
            elif state is OperationWorkspaceState.FAILURE:
                correct = QPushButton("Correct Inputs")
                correct.clicked.connect(self.correct_inputs_requested)
                page_layout.addWidget(correct)
            page_layout.addStretch()
            self.stack.addWidget(page)
        layout.addWidget(self.stack)

    def refresh(self, controller: OperationController) -> None:
        state = controller.workspace_state
        self.stack.setCurrentWidget(self._pages[state])
        if state is OperationWorkspaceState.MISSING_INPUT:
            self._messages[state].setText(
                "\n".join(
                    [*controller.input_errors.values(), *controller.parameter_errors.values()]
                )
            )
            self.open_button.setVisible(controller.document_controller.current_image is None)
        elif state is OperationWorkspaceState.PROCESSING:
            definition = controller.active_definition
            self._messages[state].setText(
                f"Processing {definition.display_name if definition else 'operation'}…"
            )
            self.progress_bar.setValue(round(controller.progress_percent))
            self.progress_message.setText(controller.progress_message)
        elif state is OperationWorkspaceState.RESULT and controller.active_result:
            result = controller.active_result
            lines = [
                f"Primary: {result.primary_artifact.label} ({result.primary_artifact.artifact_type.value})",
                *(f"{x.label} ({x.artifact_type.value})" for x in result.artifacts),
                *(f"{k}: {v}" for k, v in result.metrics.items()),
                *(f"Warning: {x}" for x in result.warnings),
            ]
            if result.processing_time_ms is not None:
                lines.append(f"Processing time: {result.processing_time_ms:.1f} ms")
            self.result_summary.setText("\n".join(lines))
        elif state is OperationWorkspaceState.FAILURE:
            self._messages[state].setText(controller.failure_message or "The operation failed.")

    def set_result_widget(self, widget: QWidget | None) -> None:
        if self._result_widget is not None:
            self.result_widget_host.removeWidget(self._result_widget)
            self._result_widget.setParent(None)
        self._result_widget = widget
        self.result_summary.setVisible(widget is None)
        if widget is not None:
            self.result_widget_host.addWidget(widget)
