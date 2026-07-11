"""Empty operation-workspace page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class OperationWorkspace(QWidget):
    """Reserve the operation workspace without faking operation behavior."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(36, 32, 36, 32)
        heading = QLabel("Operation Workspace")
        heading.setStyleSheet("font-size: 24px; font-weight: 600;")
        panel = QFrame()
        panel.setStyleSheet("background: #1f2937; border-radius: 6px;")
        panel_layout = QVBoxLayout(panel)
        message = QLabel("Select an operation to begin.")
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        message.setStyleSheet("color: #d1d5db; font-size: 16px;")
        panel_layout.addWidget(message)
        layout.addWidget(heading)
        layout.addWidget(panel, 1)
