"""Primary document workspace foundation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.ui.widgets import ImageCanvas


class OperationWorkspace(QWidget):
    open_image_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self._states = QStackedWidget()
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.addStretch()
        heading = QLabel("No image loaded")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        message = QLabel("Open a primary image to begin working.")
        self.open_button = QPushButton("Open Image")
        self.open_button.clicked.connect(self.open_image_requested)
        empty_layout.addWidget(heading)
        empty_layout.addWidget(message)
        empty_layout.addWidget(self.open_button)
        empty_layout.addStretch()

        image_state = QWidget()
        image_layout = QVBoxLayout(image_state)
        self.image_name_label = QLabel()
        self.image_name_label.setStyleSheet("font-size: 17px; font-weight: 600;")
        self.image_info_label = QLabel()
        self.image_canvas = ImageCanvas()
        image_layout.addWidget(self.image_name_label)
        image_layout.addWidget(self.image_info_label)
        image_layout.addWidget(self.image_canvas, 1)
        self._states.addWidget(empty)
        self._states.addWidget(image_state)
        layout.addWidget(self._states)

    def set_image(self, asset: ImageAsset) -> None:
        self.image_name_label.setText(asset.name)
        self.image_info_label.setText(
            f"{asset.width} × {asset.height} • {asset.colour_model.value}"  # noqa: RUF001
        )
        self.image_canvas.set_image(asset)
        self._states.setCurrentIndex(1)

    def clear_image(self) -> None:
        self.image_canvas.clear_image()
        self._states.setCurrentIndex(0)
