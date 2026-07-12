"""Focused reusable controls used by generated parameter forms."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget


class KernelEditor(QWidget):
    value_changed = Signal()

    def __init__(self, value: object, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        layout.addWidget(self.table)
        self.set_value(value)
        self.table.itemChanged.connect(self.value_changed)

    def set_value(self, value: object) -> None:
        rows = value if isinstance(value, (tuple, list)) else ()
        self.table.blockSignals(True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(
            len(rows[0]) if rows and isinstance(rows[0], (tuple, list)) else 0
        )
        for row_index, row in enumerate(rows):
            if not isinstance(row, (tuple, list)):
                continue
            for column_index, item in enumerate(row):
                self.table.setItem(row_index, column_index, QTableWidgetItem(str(item)))
        self.table.blockSignals(False)

    def value(self) -> tuple[tuple[object, ...], ...]:
        rows: list[tuple[object, ...]] = []
        for row in range(self.table.rowCount()):
            values: list[object] = []
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                text = item.text().strip() if item is not None else ""
                try:
                    numeric = float(text)
                    values.append(int(numeric) if numeric.is_integer() else numeric)
                except ValueError:
                    values.append(text)
            rows.append(tuple(values))
        return tuple(rows)
