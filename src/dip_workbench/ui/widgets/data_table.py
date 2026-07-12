"""Model/view data table widget."""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QLineEdit, QTableView, QVBoxLayout, QWidget

from dip_workbench.operations import TableData, coerce_table_data


def format_cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


MODEL_INDEX = QModelIndex()


class TableDataModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._data = TableData(("Value",), ())

    def set_table_data(self, data: TableData) -> None:
        self.beginResetModel()
        self._data = data
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | QPersistentModelIndex = MODEL_INDEX) -> int:
        return 0 if parent.isValid() else len(self._data.rows)

    def columnCount(self, parent: QModelIndex | QPersistentModelIndex = MODEL_INDEX) -> int:
        return 0 if parent.isValid() else len(self._data.columns)

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if not index.isValid():
            return None
        value = self._data.rows[index.row()][index.column()]
        if role in {Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole}:
            return format_cell(value)
        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation is Qt.Orientation.Horizontal:
            return self._data.columns[section]
        return str(section + 1)

    @property
    def table_data(self) -> TableData:
        return self._data


class ContainsFilterProxy(QSortFilterProxyModel):
    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._needle = ""

    def set_filter_text(self, text: str) -> None:
        self._needle = text.casefold()
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: QModelIndex | QPersistentModelIndex
    ) -> bool:
        if not self._needle:
            return True
        model = self.sourceModel()
        for column in range(model.columnCount(source_parent)):
            value = model.index(source_row, column, source_parent).data()
            if self._needle in str(value).casefold():
                return True
        return False


class DataTableWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search")
        self.model = TableDataModel(self)
        self.proxy = ContainsFilterProxy(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        layout.addWidget(self.search)
        layout.addWidget(self.table, 1)
        self.search.textChanged.connect(self.proxy.set_filter_text)

    def set_table_data(self, data: object) -> None:
        self.model.set_table_data(coerce_table_data(data))
        self.table.resizeColumnsToContents()

    def table_data(self) -> TableData:
        return self.model.table_data

    def clear(self) -> None:
        self.model.set_table_data(TableData(("Value",), ()))

    def copy_selection(self) -> str:
        indexes = sorted(
            self.table.selectedIndexes(), key=lambda index: (index.row(), index.column())
        )
        rows: dict[int, dict[int, str]] = {}
        for proxy_index in indexes:
            rows.setdefault(proxy_index.row(), {})[proxy_index.column()] = str(
                proxy_index.data() or ""
            )
        text = "\n".join(
            "\t".join(cells[column] for column in sorted(cells))
            for _, cells in sorted(rows.items())
        )
        QGuiApplication.clipboard().setText(text)
        return text
