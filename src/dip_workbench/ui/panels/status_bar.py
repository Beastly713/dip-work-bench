"""Persistent workbench status bar."""

from PySide6.QtWidgets import QLabel, QStatusBar, QWidget


class WorkbenchStatusBar(QStatusBar):
    """Display three independent shell-level status regions."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(26)
        self.left_label = QLabel("No image loaded")
        self.centre_label = QLabel("")
        self.right_label = QLabel("Ready")
        self.addWidget(self.left_label)
        self.addWidget(self.centre_label, 1)
        self.addPermanentWidget(self.right_label)

    def set_left_status(self, text: str) -> None:
        self.left_label.setText(text)

    def set_centre_status(self, text: str) -> None:
        self.centre_label.setText(text)

    def set_right_status(self, text: str) -> None:
        self.right_label.setText(text)
