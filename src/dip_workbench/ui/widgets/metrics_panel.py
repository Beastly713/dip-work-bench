"""Responsive metric display panel."""

from __future__ import annotations

from collections.abc import Mapping

from PySide6.QtWidgets import QGridLayout, QLabel, QWidget


class MetricsPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QGridLayout(self)
        self._data: Mapping[str, object] = {}

    def set_metrics(
        self,
        metrics: Mapping[str, object],
        *,
        units: Mapping[str, object] | None = None,
        descriptions: Mapping[str, object] | None = None,
        processing_time_ms: float | None = None,
    ) -> None:
        self.clear()
        data = dict(metrics)
        if processing_time_ms is not None:
            data["Processing time"] = processing_time_ms
            units = {**dict(units or {}), "Processing time": "ms"}
        self._data = data
        for row, (key, value) in enumerate(data.items()):
            unit = "" if units is None else str(units.get(key, ""))
            description = "" if descriptions is None else str(descriptions.get(key, ""))
            label = QLabel(str(key))
            label.setToolTip(description)
            value_label = QLabel(
                f"{value:g} {unit}".strip()
                if isinstance(value, float)
                else f"{value} {unit}".strip()
            )
            self._layout.addWidget(label, row, 0)
            self._layout.addWidget(value_label, row, 1)

    def metrics(self) -> Mapping[str, object]:
        return self._data

    def clear(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item is None:
                continue
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._data = {}
