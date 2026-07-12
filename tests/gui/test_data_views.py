"""GUI tests for table, metrics, and matrix views."""

from dip_workbench.ui.widgets import DataTableWidget, MatrixViewer, MetricsPanel


def test_data_table_filter_and_copy(qtbot) -> None:  # type: ignore[no-untyped-def]
    widget = DataTableWidget()
    qtbot.addWidget(widget)
    widget.set_table_data(({"name": "Alpha", "score": 1}, {"score": 2, "extra": "Beta"}))
    assert widget.table_data().columns == ("name", "score", "extra")
    widget.search.setText("beta")
    assert widget.proxy.rowCount() == 1
    widget.set_table_data(object())
    assert not widget.message.isHidden()
    assert "Unsupported table data" in widget.message.text()


def test_metrics_and_matrix_views(qtbot) -> None:  # type: ignore[no-untyped-def]
    metrics = MetricsPanel()
    qtbot.addWidget(metrics)
    metrics.set_metrics(
        {"zero": 0, "negative": -1}, units={"negative": "dB"}, processing_time_ms=1.5
    )
    assert "zero" in metrics.metrics()
    assert "Processing time" in metrics.metrics()

    matrix = MatrixViewer()
    qtbot.addWidget(matrix)
    matrix.set_matrix_data([[1, -1], [0, 2]])
    assert matrix.matrix_data() is not None
    matrix.set_matrix_data([["a", "b"]])
    assert matrix.matrix_data() is not None
    matrix.set_matrix_data([[1, 2], 3])
    assert matrix.matrix_data() is None
    assert "Unsupported matrix data" in matrix.heat_message.text()
