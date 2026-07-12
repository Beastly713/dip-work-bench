"""Single-image operation input summary and source selection."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.controllers import InputSource, OperationController
from dip_workbench.core import ImageAsset


class OperationInputStrip(QWidget):
    source_changed = Signal(object)
    open_image_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel("Input")
        heading.setStyleSheet("font-size:16px;font-weight:600")
        layout.addWidget(heading)
        self.summary = QLabel()
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)
        row = QHBoxLayout()
        self.original_button = QRadioButton(InputSource.ORIGINAL.value)
        self.current_button = QRadioButton(InputSource.CURRENT.value)
        self.source_group = QButtonGroup(self)
        self.source_group.addButton(self.original_button)
        self.source_group.addButton(self.current_button)
        self.original_button.clicked.connect(lambda: self.source_changed.emit(InputSource.ORIGINAL))
        self.current_button.clicked.connect(lambda: self.source_changed.emit(InputSource.CURRENT))
        row.addWidget(self.original_button)
        row.addWidget(self.current_button)
        row.addStretch()
        layout.addLayout(row)
        self.open_button = QPushButton("Open Image")
        self.open_button.clicked.connect(self.open_image_requested)
        layout.addWidget(self.open_button)

    def refresh(self, controller: OperationController) -> None:
        definition = controller.active_definition
        if definition is None:
            self.summary.setText("No operation selected.")
            return
        spec = definition.input_spec[0]
        image = (
            controller.document_controller.original_image
            if controller.input_source is InputSource.ORIGINAL
            else controller.document_controller.current_image
        )
        text = (
            f"{image.name} — {image.width} x {image.height} — {image.colour_model.value}"
            if isinstance(image, ImageAsset)
            else "No image loaded."
        )
        if spec.key in controller.input_errors:
            text = f"{text}\n{controller.input_errors[spec.key]}"
        self.summary.setText(text)
        self.open_button.setVisible(image is None)
        self.original_button.setEnabled(spec.allow_original)
        self.current_button.setEnabled(spec.allow_current)
        self.original_button.setChecked(controller.input_source is InputSource.ORIGINAL)
        self.current_button.setChecked(controller.input_source is InputSource.CURRENT)
