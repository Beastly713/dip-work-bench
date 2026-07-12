"""Structural parameter panel."""

from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.ui.panels.operation_parameter_panel import OperationParameterPanel
from dip_workbench.ui.panels.utility_transform_panel import UtilityTransformPanel


class ParameterPanel(QWidget):
    """Reserve space for future operation parameters."""

    MINIMUM_WIDTH = 280

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        placeholder = QWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        heading = QLabel("Parameters")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        message = QLabel("Select an operation to view its parameters.")
        message.setWordWrap(True)
        placeholder_layout.addWidget(heading)
        placeholder_layout.addWidget(message)
        placeholder_layout.addStretch()
        self.utility_panel = UtilityTransformPanel()
        self.operation_panel = OperationParameterPanel()
        self.stack.addWidget(placeholder)
        self.stack.addWidget(self.utility_panel)
        self.stack.addWidget(self.operation_panel)
        layout.addWidget(self.stack)

    def show_placeholder(self) -> None:
        self.stack.setCurrentIndex(0)

    def show_utility_panel(self) -> None:
        self.stack.setCurrentIndex(1)

    def show_operation_panel(self) -> None:
        self.stack.setCurrentIndex(2)
