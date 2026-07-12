"""PyQtGraph-backed graph, histogram and curve widgets."""

from __future__ import annotations

import pyqtgraph as pg  # type: ignore[import-untyped]
from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.operations import (
    GraphData,
    GraphStyle,
    VisualizationValidationError,
    coerce_graph_data,
    coerce_histogram_data,
)


class GraphWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._data: GraphData | None = None
        self.plot_items: list[object] = []
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.plot = pg.PlotWidget()
        self.message = QLabel("No graph data")
        self.message.setWordWrap(True)
        self.stack.addWidget(self.message)
        self.stack.addWidget(self.plot)
        layout.addWidget(self.stack)

    def set_graph_data(self, data: GraphData | object) -> None:
        try:
            graph = coerce_graph_data(data)
        except VisualizationValidationError as error:
            self._data = None
            self.message.setText(f"Unsupported graph data: {error}")
            self.stack.setCurrentWidget(self.message)
            return
        self._data = graph
        self._draw_graph(graph)
        self.stack.setCurrentWidget(self.plot)

    def graph_data(self) -> GraphData | None:
        return self._data

    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage:
        width = max(minimum_width, self.plot.width(), 1)
        height = max(minimum_height, self.plot.height(), 1)
        old_size = self.plot.size()
        try:
            self.plot.resize(width, height)
            image = QImage(width, height, QImage.Format.Format_ARGB32)
            image.fill(0xFFFFFFFF)
            painter = QPainter(image)
            self.plot.render(painter)
            painter.end()
            return image
        finally:
            self.plot.resize(old_size)

    def clear(self) -> None:
        self._data = None
        self.plot.clear()
        self.plot_items = []
        self.message.setText("No graph data")
        self.stack.setCurrentWidget(self.message)

    def _draw_graph(self, graph: GraphData) -> None:
        self.plot.clear()
        self.plot_items = []
        self.plot.setTitle(graph.title)
        self.plot.setLabel("bottom", graph.x_label)
        self.plot.setLabel("left", graph.y_label)
        legend = self.plot.addLegend() if len(graph.series) > 1 else None
        bar_width = 0.8 / max(len(graph.series), 1)
        for index, series in enumerate(graph.series):
            pen = pg.mkPen(pg.intColor(index), width=2)
            if graph.style is GraphStyle.BAR:
                offset = (index - (len(graph.series) - 1) / 2.0) * bar_width
                item = pg.BarGraphItem(
                    x=[x + offset for x in series.x],
                    height=list(series.y),
                    width=bar_width,
                    brush=pg.intColor(index),
                )
                self.plot.addItem(item)
                if legend is not None:
                    legend.addItem(item, series.label)
            else:
                item = self.plot.plot(series.x, series.y, pen=pen, name=series.label)
            self.plot_items.append(item)


class HistogramWidget(GraphWidget):
    def set_histogram_data(self, data: object) -> None:
        self.set_graph_data(coerce_histogram_data(data))


class TransformationCurveWidget(GraphWidget):
    def set_curve_data(self, data: object) -> None:
        graph = coerce_graph_data(data, title="Input-Output Mapping")
        if not graph.x_label:
            graph = GraphData(
                graph.series,
                title=graph.title,
                x_label="Input intensity",
                y_label="Output intensity",
                style=graph.style,
            )
        self.set_graph_data(graph)
