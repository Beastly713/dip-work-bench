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
    load_image_requested = Signal(str)
    clear_input_requested = Signal(str)

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
        self.additional_summaries: dict[str, QLabel] = {}
        self.load_buttons: dict[str, QPushButton] = {}
        self.clear_buttons: dict[str, QPushButton] = {}

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
        self.additional_summaries.clear()
        self.load_buttons.clear()
        self.clear_buttons.clear()
        additional = [x for x in definition.input_spec if x.role is not InputRole.PRIMARY_IMAGE]
        for spec in additional:
            value = controller.additional_inputs.get(spec.key)
            error = controller.input_errors.get(spec.key)
            row = QWidget()
            row_layout = QHBoxLayout(row)
            label = QLabel(self._summary(spec.label, spec.role, value, spec.minimum_count))
            label.setWordWrap(True)
            if error:
                label.setText(f"{label.text()}\n{error}")
                label.setStyleSheet("color:#b91c1c")
            row_layout.addWidget(label, 1)
            self.additional_summaries[spec.key] = label
            if spec.role in {
                InputRole.SECONDARY_IMAGE,
                InputRole.REFERENCE_IMAGE,
                InputRole.SECOND_FRAME,
                InputRole.BINARY_MASK,
            }:
                load = QPushButton("Change" if value is not None else "Load")
                load.clicked.connect(
                    lambda checked=False, key=spec.key: self.load_image_requested.emit(key)
                )
                clear = QPushButton("Clear")
                clear.setVisible(value is not None)
                clear.clicked.connect(
                    lambda checked=False, key=spec.key: self.clear_input_requested.emit(key)
                )
                self.load_buttons[spec.key] = load
                self.clear_buttons[spec.key] = clear
                row_layout.addWidget(load)
                row_layout.addWidget(clear)
            self.additional_layout.addWidget(row)
        self.additional_box.setVisible(bool(additional))

    @staticmethod
    def _summary(label: str, role: InputRole, value: object, minimum_count: int) -> str:
        requirement = f"required, minimum {minimum_count}" if minimum_count else "optional"
        if isinstance(value, ImageAsset):
            return f"{label} — {value.name} — {value.width} x {value.height} — {value.colour_model.value} ({requirement})"
        if role is InputRole.DATASET and isinstance(value, (tuple, list)):
            images = [item for item in value if isinstance(item, ImageAsset)]
            dimensions = {(item.width, item.height) for item in images}
            size = (
                f"{next(iter(dimensions))[0]} x {next(iter(dimensions))[1]}"
                if len(dimensions) == 1
                else "Mixed dimensions"
            )
            return f"{label} — {len(value)} images — {size} (minimum {minimum_count})"
        count = len(value) if isinstance(value, (tuple, list, set, frozenset)) else 0
        if role is InputRole.SEED_POINTS:
            return f"{label} — {count} selected"
        if role in {InputRole.REGION_SELECTION, InputRole.BLOCK_SELECTION} and value is not None:
            fields = tuple(getattr(value, key, None) for key in ("x", "y", "width", "height"))
            if all(item is not None for item in fields):
                return f"{label} — x={fields[0]}, y={fields[1]}, {fields[2]} x {fields[3]}"
        if role is InputRole.MARKERS and isinstance(value, dict):
            return f"{label} — " + ", ".join(f"{key}: {len(items)}" for key, items in value.items())
        if role is InputRole.CONTOUR_SELECTION and value is not None:
            return f"{label} — Selected"
        return f"{label} — Not provided ({requirement})"
