"""PySide-free visualization data contracts and adapters."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

from dip_workbench.core import InputValidationError


class VisualizationValidationError(InputValidationError):
    """Raised when visualization payloads cannot be adapted safely."""


class GraphStyle(StrEnum):
    LINE = "line"
    STEP = "step"
    BAR = "bar"
    SCATTER = "scatter"


@dataclass(frozen=True, slots=True)
class GraphSeries:
    label: str
    x: tuple[float, ...]
    y: tuple[float, ...]

    def __post_init__(self) -> None:
        label = str(self.label)
        if self.label is not None and not label.strip():
            raise VisualizationValidationError("Graph series labels must be non-empty.")
        x = _numeric_tuple(self.x, "Graph x coordinates")
        y = _numeric_tuple(self.y, "Graph y coordinates")
        if not x or len(x) != len(y):
            raise VisualizationValidationError("Graph series requires equal non-zero x/y lengths.")
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)


@dataclass(frozen=True, slots=True)
class GraphData:
    series: tuple[GraphSeries, ...]
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    style: GraphStyle = GraphStyle.LINE

    def __post_init__(self) -> None:
        series = tuple(self.series)
        if not series:
            raise VisualizationValidationError("Graph data requires at least one series.")
        try:
            style = self.style if isinstance(self.style, GraphStyle) else GraphStyle(self.style)
        except ValueError as error:
            raise VisualizationValidationError("Graph style is unsupported.") from error
        object.__setattr__(self, "series", series)
        object.__setattr__(self, "title", str(self.title))
        object.__setattr__(self, "x_label", str(self.x_label))
        object.__setattr__(self, "y_label", str(self.y_label))
        object.__setattr__(self, "style", style)


@dataclass(frozen=True, slots=True)
class TableData:
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]

    def __post_init__(self) -> None:
        columns = tuple(str(column) for column in self.columns)
        if not columns or any(not column.strip() for column in columns):
            raise VisualizationValidationError("Table columns must be non-empty.")
        rows = tuple(tuple(row) for row in self.rows)
        if any(len(row) != len(columns) for row in rows):
            raise VisualizationValidationError("Every table row must match the column count.")
        object.__setattr__(self, "columns", columns)
        object.__setattr__(self, "rows", rows)


@dataclass(frozen=True, slots=True)
class MatrixData:
    values: tuple[tuple[object, ...], ...]
    row_labels: tuple[str, ...] = ()
    column_labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(tuple(row) for row in self.values)
        if not values or not values[0]:
            raise VisualizationValidationError("Matrix data must be non-empty.")
        width = len(values[0])
        if any(len(row) != width for row in values):
            raise VisualizationValidationError("Matrix data must be rectangular.")
        row_labels = tuple(str(label) for label in self.row_labels)
        column_labels = tuple(str(label) for label in self.column_labels)
        if row_labels and len(row_labels) != len(values):
            raise VisualizationValidationError("Matrix row labels must match the row count.")
        if column_labels and len(column_labels) != width:
            raise VisualizationValidationError("Matrix column labels must match the column count.")
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "row_labels", row_labels)
        object.__setattr__(self, "column_labels", column_labels)


@dataclass(frozen=True, slots=True)
class TreeNode:
    label: str
    value: object | None = None
    children: tuple[TreeNode, ...] = ()

    def __post_init__(self) -> None:
        label = str(self.label)
        if not label.strip():
            raise VisualizationValidationError("Tree labels must be non-empty.")
        children = tuple(
            child if isinstance(child, TreeNode) else coerce_tree_data(child)
            for child in self.children
        )
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "children", children)


def _numeric_tuple(values: object, label: str) -> tuple[float, ...]:
    try:
        array = np.asarray(values)
    except (TypeError, ValueError) as error:
        raise VisualizationValidationError(f"{label} must be numeric.") from error
    if array.ndim != 1:
        raise VisualizationValidationError(f"{label} must be one-dimensional.")
    output: list[float] = []
    for value in array.tolist():
        if isinstance(value, bool) or not isinstance(value, (int, float, np.number)):
            raise VisualizationValidationError(f"{label} must contain only numeric values.")
        number = float(value)
        if not math.isfinite(number):
            raise VisualizationValidationError(f"{label} must contain only finite values.")
        output.append(number)
    return tuple(output)


def coerce_graph_data(
    payload: object, *, title: str = "", style: GraphStyle | str = GraphStyle.LINE
) -> GraphData:
    if isinstance(payload, GraphData):
        return payload
    if isinstance(payload, Mapping):
        if "input" in payload and "output" in payload:
            return GraphData(
                (
                    GraphSeries(
                        "Mapping",
                        _numeric_tuple(payload["input"], "Input"),
                        _numeric_tuple(payload["output"], "Output"),
                    ),
                ),
                title=title,
                x_label="Input intensity",
                y_label="Output intensity",
                style=GraphStyle(style),
            )
        if "x" in payload and "y" in payload:
            return GraphData(
                (GraphSeries(str(payload.get("label", "Series")), payload["x"], payload["y"]),),
                title=title,
                style=GraphStyle(style),
            )
        if "series" in payload:
            return GraphData(
                tuple(payload["series"]),
                title=str(payload.get("title", title)),
                x_label=str(payload.get("x_label", "")),
                y_label=str(payload.get("y_label", "")),
                style=payload.get("style", style),
            )
    raise VisualizationValidationError("Graph payload is unsupported.")


def coerce_histogram_data(payload: object) -> GraphData:
    if isinstance(payload, GraphData):
        return payload
    if isinstance(payload, Mapping):
        series = []
        for label, counts in payload.items():
            y = _numeric_tuple(counts, "Histogram counts")
            series.append(GraphSeries(str(label), tuple(float(i) for i in range(len(y))), y))
        return GraphData(
            tuple(series), x_label="Intensity", y_label="Frequency", style=GraphStyle.BAR
        )
    y = _numeric_tuple(payload, "Histogram counts")
    return GraphData(
        (GraphSeries("Frequency", tuple(float(i) for i in range(len(y))), y),),
        x_label="Intensity",
        y_label="Frequency",
        style=GraphStyle.BAR,
    )


def coerce_table_data(payload: object) -> TableData:
    if isinstance(payload, TableData):
        return payload
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        rows = list(payload)
        if rows and all(isinstance(row, Mapping) for row in rows):
            columns: list[str] = []
            for row in rows:
                for key in row:
                    text = str(key)
                    if text not in columns:
                        columns.append(text)
            mapping_rows = [row for row in rows if isinstance(row, Mapping)]
            return TableData(
                tuple(columns),
                tuple(tuple(row.get(column, "") for column in columns) for row in mapping_rows),
            )
    raise VisualizationValidationError("Table payload is unsupported.")


def coerce_matrix_data(payload: object) -> MatrixData:
    if isinstance(payload, MatrixData):
        return payload
    if isinstance(payload, np.ndarray):
        if payload.ndim != 2:
            raise VisualizationValidationError("Matrix arrays must be two-dimensional.")
        return MatrixData(tuple(tuple(value for value in row) for row in payload.tolist()))
    if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
        return MatrixData(tuple(tuple(row) for row in payload if isinstance(row, Sequence)))
    raise VisualizationValidationError("Matrix payload is unsupported.")


def coerce_tree_data(payload: object, *, _seen: set[int] | None = None) -> TreeNode:
    if isinstance(payload, TreeNode):
        return payload
    if not isinstance(payload, Mapping):
        raise VisualizationValidationError("Tree payload is unsupported.")
    seen = set() if _seen is None else _seen
    identity = id(payload)
    if identity in seen:
        raise VisualizationValidationError("Cyclic tree payloads are unsupported.")
    seen.add(identity)
    try:
        label = payload["label"]
    except KeyError as error:
        raise VisualizationValidationError("Tree payload requires a label.") from error
    child_payloads = payload.get("children", ())
    if not isinstance(child_payloads, Sequence) or isinstance(
        child_payloads, (str, bytes, bytearray)
    ):
        raise VisualizationValidationError("Tree children must be a sequence.")
    children = tuple(coerce_tree_data(child, _seen=seen) for child in child_payloads)
    seen.remove(identity)
    return TreeNode(str(label), payload.get("value"), children)


__all__ = [
    "GraphData",
    "GraphSeries",
    "GraphStyle",
    "MatrixData",
    "TableData",
    "TreeNode",
    "VisualizationValidationError",
    "coerce_graph_data",
    "coerce_histogram_data",
    "coerce_matrix_data",
    "coerce_table_data",
    "coerce_tree_data",
]
