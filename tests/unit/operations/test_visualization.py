"""Tests for visualization contracts and adapters."""

import numpy as np
import pytest

from dip_workbench.operations import (
    GraphData,
    GraphSeries,
    MatrixData,
    TableData,
    VisualizationValidationError,
    coerce_graph_data,
    coerce_histogram_data,
    coerce_matrix_data,
    coerce_table_data,
)


def test_valid_graph_and_validation_errors() -> None:
    graph = GraphData((GraphSeries("line", (0, 1), (2, 3)),))
    assert graph.series[0].x == (0.0, 1.0)
    with pytest.raises(VisualizationValidationError):
        GraphData(())
    with pytest.raises(VisualizationValidationError):
        GraphSeries("bad", (1,), (1, 2))
    with pytest.raises(VisualizationValidationError):
        GraphSeries("bad", (float("nan"),), (1,))
    with pytest.raises(VisualizationValidationError):
        GraphSeries("bad", (True,), (1,))


def test_table_and_matrix_contracts() -> None:
    assert TableData(("a",), ((1,),)).rows == ((1,),)
    with pytest.raises(VisualizationValidationError):
        TableData(("a",), ((1, 2),))
    assert MatrixData(((1, 2), (3, 4)), row_labels=("r1", "r2")).values[1] == (3, 4)
    with pytest.raises(VisualizationValidationError):
        MatrixData(())
    with pytest.raises(VisualizationValidationError):
        MatrixData(((1,), (1, 2)))
    with pytest.raises(VisualizationValidationError):
        MatrixData(((1,),), column_labels=("a", "b"))


def test_compatibility_adapters() -> None:
    mapping = {"input": np.arange(3, dtype=np.uint8), "output": np.array([255, 254, 253])}
    assert coerce_graph_data(mapping).series[0].y == (255.0, 254.0, 253.0)
    assert coerce_graph_data({"x": [1, 2], "y": [3, 4]}).series[0].x == (1.0, 2.0)
    assert coerce_histogram_data([0, 4]).series[0].x == (0.0, 1.0)
    assert len(coerce_histogram_data({"r": [1], "g": [2]}).series) == 2
    table = coerce_table_data(({"b": 1, "a": 2}, {"c": 3}))
    assert table.columns == ("b", "a", "c")
    assert table.rows[1] == ("", "", 3)
    assert coerce_matrix_data(np.eye(2)).values == ((1.0, 0.0), (0.0, 1.0))
    with pytest.raises(VisualizationValidationError):
        coerce_matrix_data([[1, 2], 3])
