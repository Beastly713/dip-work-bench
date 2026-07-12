"""GUI tests for PyQtGraph-backed graph widgets."""

import numpy as np

from dip_workbench.operations import GraphData, GraphSeries, GraphStyle
from dip_workbench.ui.widgets import GraphWidget, HistogramWidget, TransformationCurveWidget


def test_graph_styles_and_render(qtbot) -> None:  # type: ignore[no-untyped-def]
    for style in GraphStyle:
        widget = GraphWidget()
        qtbot.addWidget(widget)
        widget.resize(220, 160)
        widget.set_graph_data(GraphData((GraphSeries("s", (-1, 0, 1), (1, 0, 1)),), style=style))
        assert widget.graph_data() is not None
        image = widget.render_image(minimum_width=600, minimum_height=400)
        assert not image.isNull()
        assert image.width() >= 600 and image.height() >= 400
        non_background = 0
        for x in range(300, image.width(), 20):
            for y in range(0, image.height(), 20):
                if image.pixelColor(x, y).name() != "#ffffff":
                    non_background += 1
        assert non_background > 0


def test_step_graph_uses_step_coordinates(qtbot) -> None:  # type: ignore[no-untyped-def]
    widget = GraphWidget()
    qtbot.addWidget(widget)
    widget.set_graph_data(
        GraphData((GraphSeries("step", (0, 1, 2), (3, 4, 5)),), style=GraphStyle.STEP)
    )
    item = widget.plot_items[0]
    assert len(item.xData) == 5
    assert list(item.yData) == [3.0, 3.0, 4.0, 4.0, 5.0]


def test_histogram_and_negative_curve(qtbot) -> None:  # type: ignore[no-untyped-def]
    histogram = HistogramWidget()
    qtbot.addWidget(histogram)
    histogram.set_histogram_data({"gray": [0, 2, 0]})
    assert histogram.graph_data().y_label == "Frequency"  # type: ignore[union-attr]

    curve = TransformationCurveWidget()
    qtbot.addWidget(curve)
    values = np.arange(256, dtype=np.uint8)
    curve.set_curve_data({"input": values, "output": 255 - values})
    series = curve.graph_data().series[0]  # type: ignore[union-attr]
    assert (series.x[0], series.y[0]) == (0.0, 255.0)
    assert (series.x[127], series.y[127]) == (127.0, 128.0)
    assert (series.x[255], series.y[255]) == (255.0, 0.0)
