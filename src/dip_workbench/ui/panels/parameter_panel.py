"""Structural parameter panel."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ParameterPanel(QWidget):
    """Reserve space for future operation parameters."""

    MINIMUM_WIDTH = 280

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setStyleSheet("background: #f8fafc;")
        layout = QVBoxLayout(self)
        heading = QLabel("Parameters")
        heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        message = QLabel("Select an operation to view its parameters.")
        message.setWordWrap(True)
        message.setStyleSheet("color: #64748b;")
        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addStretch()
