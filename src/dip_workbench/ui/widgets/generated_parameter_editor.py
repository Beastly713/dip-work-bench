"""Schema-driven standard operation parameter editor."""
# mypy: disable-error-code="assignment,attr-defined,arg-type,call-overload,unused-ignore"

from collections.abc import Mapping

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.operations import ParameterSpec, ParameterType
from dip_workbench.ui.panels.operation_parameter_panel import OperationParameterEditor
from dip_workbench.ui.widgets.parameter_controls import KernelEditor


class GeneratedParameterEditor(OperationParameterEditor):
    def __init__(self, schema: tuple[ParameterSpec, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.schema = schema
        self.controls: dict[str, QWidget] = {}
        self.rows: dict[str, QWidget] = {}
        self.error_labels: dict[str, QLabel] = {}
        self._values = {spec.key: spec.default for spec in schema}
        self._updating = False
        layout = QVBoxLayout(self)
        self.primary_layout = QVBoxLayout()
        layout.addLayout(self.primary_layout)
        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setText("Advanced Settings")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.advanced_container = QWidget()
        self.advanced_layout = QVBoxLayout(self.advanced_container)
        self.advanced_container.hide()
        self.advanced_toggle.toggled.connect(self._toggle_advanced)
        advanced = any(spec.advanced for spec in schema)
        self.advanced_toggle.setVisible(advanced)
        layout.addWidget(self.advanced_toggle)
        layout.addWidget(self.advanced_container)
        for spec in schema:
            self._add_parameter(
                spec, self.advanced_layout if spec.advanced else self.primary_layout
            )
        layout.addStretch()
        self.set_values(self._values)

    def _add_parameter(self, spec: ParameterSpec, target: QVBoxLayout) -> None:
        row = QWidget()
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(0, 3, 0, 3)
        label = QLabel(spec.label)
        if spec.help_text:
            label.setToolTip(spec.help_text)
        control = self._create_control(spec)
        error = QLabel()
        error.setWordWrap(True)
        error.setStyleSheet("color: #b91c1c;")
        row_layout.addWidget(label)
        row_layout.addWidget(control)
        row_layout.addWidget(error)
        target.addWidget(row)
        self.controls[spec.key] = control
        self.rows[spec.key] = row
        self.error_labels[spec.key] = error

    def _create_control(self, spec: ParameterSpec) -> QWidget:
        kind = spec.parameter_type
        if kind is ParameterType.INTEGER:
            widget = QSpinBox()
            widget.setRange(
                int(spec.minimum if spec.minimum is not None else -1_000_000),
                int(spec.maximum if spec.maximum is not None else 1_000_000),
            )
            widget.setSingleStep(int(spec.step or 1))
            widget.valueChanged.connect(self._changed)
            return widget
        if kind is ParameterType.FLOAT:
            widget = QDoubleSpinBox()
            widget.setDecimals(6)
            widget.setRange(
                float(spec.minimum if spec.minimum is not None else -1e9),
                float(spec.maximum if spec.maximum is not None else 1e9),
            )
            widget.setSingleStep(float(spec.step or 0.1))
            widget.valueChanged.connect(self._changed)
            return widget
        if kind is ParameterType.BOOLEAN:
            widget = QCheckBox()
            widget.toggled.connect(self._changed)
            return widget
        if kind is ParameterType.ENUM:
            widget = QComboBox()
            for choice in spec.choices:
                widget.addItem(choice.label, choice.value)
            widget.currentIndexChanged.connect(self._changed)
            return widget
        if kind is ParameterType.RADIO:
            container = QWidget()
            layout = QVBoxLayout(container)
            group = QButtonGroup(container)
            container.button_group = group  # type: ignore[attr-defined]
            for choice in spec.choices:
                button = QRadioButton(choice.label)
                button.setProperty("choice_value", choice.value)
                group.addButton(button)
                layout.addWidget(button)
            group.buttonClicked.connect(self._changed)
            return container
        if kind in {ParameterType.INTEGER_RANGE, ParameterType.FLOAT_RANGE}:
            container = QWidget()
            layout = QHBoxLayout(container)
            boxes = []
            for _ in range(2):
                if kind is ParameterType.INTEGER_RANGE:
                    box = QSpinBox()
                    box.setRange(
                        int(spec.minimum if spec.minimum is not None else -1_000_000),
                        int(spec.maximum if spec.maximum is not None else 1_000_000),
                    )
                    box.setSingleStep(int(spec.step or 1))
                else:
                    box = QDoubleSpinBox()
                    box.setRange(
                        float(spec.minimum if spec.minimum is not None else -1e9),
                        float(spec.maximum if spec.maximum is not None else 1e9),
                    )
                    box.setSingleStep(float(spec.step or 0.1))
                    box.setDecimals(6)
                box.valueChanged.connect(self._changed)
                boxes.append(box)
                layout.addWidget(box)
            container.range_boxes = boxes  # type: ignore[attr-defined]
            return container
        if kind is ParameterType.MULTI_SELECT:
            widget = QListWidget()
            for choice in spec.choices:
                item = QListWidgetItem(choice.label)
                item.setData(Qt.ItemDataRole.UserRole, choice.value)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)
                widget.addItem(item)
            widget.itemChanged.connect(self._changed)
            return widget
        if kind is ParameterType.KERNEL:
            widget = KernelEditor(spec.default)
            widget.value_changed.connect(self._changed)
            return widget
        if kind in {ParameterType.FILE, ParameterType.IMAGE}:
            container = QWidget()
            layout = QHBoxLayout(container)
            editor = QLineEdit()
            browse = QPushButton("Browse")
            container.path_editor = editor  # type: ignore[attr-defined]
            editor.editingFinished.connect(self._changed)
            browse.clicked.connect(lambda: self._browse(editor))
            layout.addWidget(editor)
            layout.addWidget(browse)
            return container
        editor = QLineEdit()
        editor.editingFinished.connect(self._changed)
        return editor

    def _browse(self, editor: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select File", editor.text())
        if path:
            editor.setText(path)
            self._changed()

    def _changed(self, *args: object) -> None:
        if self._updating:
            return
        self._values = {spec.key: self._read(spec, self.controls[spec.key]) for spec in self.schema}
        self._apply_conditions()
        self.values_changed.emit(dict(self._values))

    def _read(self, spec: ParameterSpec, control: QWidget) -> object:
        kind = spec.parameter_type
        if isinstance(control, QSpinBox):
            return control.value()
        if isinstance(control, QDoubleSpinBox):
            return control.value()
        if isinstance(control, QCheckBox):
            return control.isChecked()
        if isinstance(control, QComboBox):
            return control.currentData()
        if kind is ParameterType.RADIO:
            button = control.button_group.checkedButton()  # type: ignore[attr-defined]
            return button.property("choice_value") if button else None
        if kind in {ParameterType.INTEGER_RANGE, ParameterType.FLOAT_RANGE}:
            return tuple(box.value() for box in control.range_boxes)  # type: ignore[attr-defined]
        if isinstance(control, QListWidget):
            return tuple(
                control.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(control.count())
                if control.item(i).checkState() is Qt.CheckState.Checked
            )
        if isinstance(control, KernelEditor):
            return control.value()
        if kind in {ParameterType.FILE, ParameterType.IMAGE}:
            return control.path_editor.text()  # type: ignore[attr-defined]
        assert isinstance(control, QLineEdit)
        text = control.text()
        if kind is ParameterType.TEXT_LIST:
            return tuple(item.strip() for item in text.split(",") if item.strip())
        if kind is ParameterType.NUMERIC_LIST:
            values: list[object] = []
            for item in text.split(","):
                try:
                    number = float(item.strip())
                    values.append(int(number) if number.is_integer() else number)
                except ValueError:
                    values.append(item.strip())
            return tuple(values)
        return text

    def set_values(self, values: Mapping[str, object]) -> None:
        self._updating = True
        self._values.update(values)
        for spec in self.schema:
            self._write(spec, self.controls[spec.key], self._values[spec.key])
        self._updating = False
        self._apply_conditions()

    def _write(self, spec: ParameterSpec, control: QWidget, value: object) -> None:
        if isinstance(control, QSpinBox):
            control.setValue(int(value))
            return
        if isinstance(control, QDoubleSpinBox):
            control.setValue(float(value))
            return
        if isinstance(control, QCheckBox):
            control.setChecked(bool(value))
            return
        if isinstance(control, QComboBox):
            control.setCurrentIndex(max(0, control.findData(value)))
            return
        if spec.parameter_type is ParameterType.RADIO:
            for button in control.button_group.buttons():  # type: ignore[attr-defined]
                button.setChecked(button.property("choice_value") == value)
        elif spec.parameter_type in {
            ParameterType.INTEGER_RANGE,
            ParameterType.FLOAT_RANGE,
        } and isinstance(value, (tuple, list)):
            for box, item in zip(control.range_boxes, value, strict=False):
                box.setValue(item)  # type: ignore[attr-defined]
        elif isinstance(control, QListWidget):
            selected = set(value) if isinstance(value, (tuple, list, set, frozenset)) else set()
            for i in range(control.count()):
                control.item(i).setCheckState(
                    Qt.CheckState.Checked
                    if control.item(i).data(Qt.ItemDataRole.UserRole) in selected
                    else Qt.CheckState.Unchecked
                )
        elif isinstance(control, KernelEditor):
            control.set_value(value)
        elif spec.parameter_type in {ParameterType.FILE, ParameterType.IMAGE}:
            control.path_editor.setText(str(value))  # type: ignore[attr-defined]
        elif isinstance(control, QLineEdit):
            control.setText(
                ", ".join(map(str, value)) if isinstance(value, (tuple, list)) else str(value)
            )

    def _apply_conditions(self) -> None:
        for spec in self.schema:
            self.rows[spec.key].setVisible(spec.is_visible(self._values))
            self.controls[spec.key].setEnabled(spec.is_enabled(self._values))

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        for key, label in self.error_labels.items():
            label.setText(errors.get(key, ""))
        advanced_error = any(spec.advanced and spec.key in errors for spec in self.schema)
        if advanced_error:
            self.advanced_toggle.setChecked(True)

    def _toggle_advanced(self, visible: bool) -> None:
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.advanced_container.setVisible(visible)
