"""Generic operation input summary and source selection."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.controllers import InputSource, OperationController
from dip_workbench.core import ImageAsset
from dip_workbench.operations import InputRole


class OperationInputStrip(QWidget):
    source_changed = Signal(object)
    open_image_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        heading = QLabel("Inputs")
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
        self.additional_box = QGroupBox("Additional inputs")
        self.additional_layout = QVBoxLayout(self.additional_box)
        layout.addWidget(self.additional_box)

    def refresh(self, controller: OperationController) -> None:
        definition = controller.active_definition
        if definition is None:
            self.summary.setText("No operation selected.")
            return
        primary = next(
            (x for x in definition.input_spec if x.role is InputRole.PRIMARY_IMAGE), None
        )
        image = (
            controller.document_controller.original_image
            if controller.input_source is InputSource.ORIGINAL
            else controller.document_controller.current_image
        )
        self.summary.setText(
            f"{image.name} — {image.width} x {image.height} — {image.colour_model.value}"
            if isinstance(image, ImageAsset)
            else "No primary image loaded."
        )
        self.open_button.setVisible(image is None)
        self.original_button.setVisible(primary is not None)
        self.current_button.setVisible(primary is not None)
        self.original_button.setEnabled(primary is not None and primary.allow_original)
        self.current_button.setEnabled(primary is not None and primary.allow_current)
        self.original_button.setChecked(controller.input_source is InputSource.ORIGINAL)
        self.current_button.setChecked(controller.input_source is InputSource.CURRENT)
        while self.additional_layout.count():
            item = self.additional_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        additional = [x for x in definition.input_spec if x.role is not InputRole.PRIMARY_IMAGE]
        for spec in additional:
            value = controller.additional_inputs.get(spec.key)
            count = len(value) if isinstance(value, (tuple, list)) else int(value is not None)
            error = controller.input_errors.get(spec.key)
            label = QLabel(
                f"{spec.label} — {f'{count} items' if count else 'Not provided'} ({'Required' if spec.required else 'Optional'})"
                + (f"\n{error}" if error else "")
            )
            label.setWordWrap(True)
            if error:
                label.setStyleSheet("color:#b91c1c")
            self.additional_layout.addWidget(label)
        self.additional_box.setVisible(bool(additional))
