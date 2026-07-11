"""DIP Workbench home page."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget


class HomePage(QWidget):
    """Present the initial, deliberately inactive image-opening choices."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(16)

        title = QLabel("DIP Workbench")
        title.setObjectName("pageTitle")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #1f2937;")
        description = QLabel(
            "Demonstrate, compare, and document syllabus-based image-processing operations."
        )
        description.setStyleSheet("font-size: 15px; color: #4b5563;")

        buttons = QHBoxLayout()
        self.open_image_button = QPushButton("Open Image")
        self.sample_image_button = QPushButton("Use Sample Image")
        self.open_image_button.setEnabled(False)
        self.sample_image_button.setEnabled(False)
        buttons.addWidget(self.open_image_button)
        buttons.addWidget(self.sample_image_button)
        buttons.addStretch()

        drop_area = QFrame()
        drop_area.setObjectName("dropArea")
        drop_area.setMinimumHeight(260)
        drop_area.setStyleSheet(
            "QFrame#dropArea { background: #1f2937; border: 1px dashed #94a3b8; "
            "border-radius: 6px; }"
        )
        drop_layout = QVBoxLayout(drop_area)
        drop_label = QLabel("Drag and drop will be available in a later step")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet("color: #d1d5db; font-size: 15px;")
        drop_layout.addWidget(drop_label)

        empty_message = QLabel(
            "No image loaded. Open an image to begin when image support is added."
        )
        empty_message.setStyleSheet("color: #6b7280;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(buttons)
        layout.addWidget(drop_area, 1)
        layout.addWidget(empty_message)
