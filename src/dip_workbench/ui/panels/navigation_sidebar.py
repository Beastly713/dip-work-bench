"""Structural navigation sidebar."""

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QPushButton, QVBoxLayout, QWidget


class NavigationSidebar(QWidget):
    """Provide home navigation until operation navigation is populated."""

    MINIMUM_WIDTH = 220

    def __init__(self, show_home: Callable[[], None], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setStyleSheet("background: #f1f5f9;")
        layout = QVBoxLayout(self)
        self.home_button = QPushButton("Home")
        self.home_button.clicked.connect(show_home)
        heading = QLabel("Operations")
        heading.setStyleSheet("font-weight: 600; margin-top: 16px;")
        placeholder = QLabel("Operation navigation is not populated yet.")
        placeholder.setWordWrap(True)
        placeholder.setStyleSheet("color: #64748b;")
        layout.addWidget(self.home_button)
        layout.addWidget(heading)
        layout.addWidget(placeholder)
        layout.addStretch()
