"""Academic operation identity header."""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dip_workbench.operations import OperationDefinition


class OperationHeader(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.operation_id_label = QLabel()
        self.name_label = QLabel("No operation selected")
        self.purpose_label = QLabel()
        self.operation_id_label.setStyleSheet("color:#2563eb;font-weight:600")
        self.name_label.setStyleSheet("font-size:22px;font-weight:600")
        self.purpose_label.setWordWrap(True)
        layout.addWidget(self.operation_id_label)
        layout.addWidget(self.name_label)
        layout.addWidget(self.purpose_label)

    def set_operation(self, definition: OperationDefinition) -> None:
        self.operation_id_label.setText(str(definition.id))
        self.name_label.setText(definition.display_name)
        self.purpose_label.setText(definition.short_description)

    def clear_operation(self) -> None:
        self.operation_id_label.clear()
        self.name_label.setText("No operation selected")
        self.purpose_label.clear()
