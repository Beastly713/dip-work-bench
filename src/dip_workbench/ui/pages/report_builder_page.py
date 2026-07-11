"""Empty report-builder page."""

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class ReportBuilderPage(QWidget):
    """Present the report builder's C02 empty state."""

    def __init__(self, show_home: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        heading = QLabel("Report Builder")
        heading.setStyleSheet("font-size: 24px; font-weight: 600;")
        message = QLabel("No report entries exist. Add-to-report support will be available later.")
        self.home_button = QPushButton("Return Home")
        self.home_button.clicked.connect(show_home)
        layout.addWidget(heading)
        layout.addWidget(message)
        layout.addWidget(self.home_button)
        layout.addStretch()
