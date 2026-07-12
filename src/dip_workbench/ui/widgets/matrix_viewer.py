"""Matrix table and heatmap viewer."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg  # type: ignore[import-untyped]
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedWidget, QTabWidget, QVBoxLayout, QWidget

from dip_workbench.operations import MatrixData, TableData, coerce_matrix_data
from dip_workbench.ui.widgets.data_table import DataTableWidget


class MatrixViewer(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: MatrixData | None = None
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.table = DataTableWidget()
        self.heat_stack = QStackedWidget()
        self.heat_message = QLabel("No numeric heatmap available")
        self.heat_message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.heat_plot = pg.PlotWidget()
        self.heat_item = pg.ImageItem()
        self.heat_plot.addItem(self.heat_item)
        self.heat_stack.addWidget(self.heat_message)
        self.heat_stack.addWidget(self.heat_plot)
        self.tabs.addTab(self.table, "Table")
        self.tabs.addTab(self.heat_stack, "Heatmap")
        layout.addWidget(self.tabs)

    def set_matrix_data(self, data: object) -> None:
        try:
            matrix = coerce_matrix_data(data)
        except Exception as error:
            self._data = None
            self.table.clear()
            self.heat_message.setText(f"Unsupported matrix data: {error}")
            self.heat_stack.setCurrentWidget(self.heat_message)
            return
        self._data = matrix
        columns = matrix.column_labels or tuple(f"C{i + 1}" for i in range(len(matrix.values[0])))
        rows = matrix.values
        if matrix.row_labels:
            columns = ("Row", *columns)
            rows = tuple(
                (matrix.row_labels[index], *row) for index, row in enumerate(matrix.values)
            )
        self.table.set_table_data(TableData(columns, rows))
        try:
            values = np.asarray(matrix.values, dtype=float)
        except (TypeError, ValueError):
            self.heat_message.setText("Heatmap requires numeric matrix values.")
            self.heat_stack.setCurrentWidget(self.heat_message)
        else:
            self.heat_item.setImage(values.T, autoLevels=True)
            self.heat_stack.setCurrentWidget(self.heat_plot)

    def matrix_data(self) -> MatrixData | None:
        return self._data

    def clear(self) -> None:
        self._data = None
        self.table.clear()
        self.heat_item.clear()
        self.heat_stack.setCurrentWidget(self.heat_message)
