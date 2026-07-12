"""Home-page summary card for one permanent academic module."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from dip_workbench.operations import MODULE_NAMES, ModuleId, OperationDefinition


class ModuleCard(QWidget):
    clicked = Signal(object)

    def __init__(
        self,
        module_id: ModuleId,
        operations: tuple[OperationDefinition, ...],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.module_id = module_id
        self.setObjectName("moduleCard")
        self.setStyleSheet(
            "QWidget#moduleCard { background: #f8fafc; border: 1px solid #cbd5e1; "
            "border-radius: 5px; } QWidget#moduleCard:hover { border-color: #2563eb; }"
        )
        layout = QVBoxLayout(self)
        number = QLabel(module_id.value[1:])
        number.setStyleSheet("color: #2563eb; font-size: 18px; font-weight: 700;")
        name = QLabel(MODULE_NAMES[module_id])
        name.setWordWrap(True)
        name.setStyleSheet("font-weight: 600;")
        count = QLabel(
            f"{len(operations)} registered {'tool' if len(operations) == 1 else 'tools'}"
        )
        count.setStyleSheet("color: #64748b;")
        tools = QLabel("\n".join(item.display_name for item in operations[:3]))
        tools.setWordWrap(True)
        layout.addWidget(number)
        layout.addWidget(name)
        layout.addWidget(count)
        layout.addWidget(tools)
        layout.addStretch()

    def mouseReleaseEvent(self, event: object) -> None:
        self.clicked.emit(self.module_id)
