"""Tests for generic artifact export."""

import numpy as np
import pytest

from dip_workbench.core import ColourModel, ExportError, ImageAsset
from dip_workbench.operations import (
    CircleOverlay,
    CurveArtifact,
    GraphData,
    GraphSeries,
    HistogramArtifact,
    ImageArtifact,
    MatrixArtifact,
    MetricGroupArtifact,
    OverlayArtifact,
    OverlayData,
    TableArtifact,
    TextArtifact,
)
from dip_workbench.services import ExportService, ImageIOService


class RenderSource:
    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800):
        from PySide6.QtGui import QImage

        image = QImage(minimum_width, minimum_height, QImage.Format.Format_RGB32)
        image.fill(0xFFFFFFFF)
        return image


def asset(model: ColourModel = ColourModel.GRAY) -> ImageAsset:
    data = np.full((4, 4), 255, dtype=np.uint8)
    if model is ColourModel.RGB:
        data = np.full((4, 4, 3), 100, dtype=np.uint8)
    if model is ColourModel.BINARY:
        data = np.array([[0, 255], [255, 0]], dtype=np.uint8)
    return ImageAsset("image", data, model)


def test_image_exports_and_non_exportable_rejection(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    image_artifact = ImageArtifact("image", "Image", asset(ColourModel.RGB))
    for suffix in (".png", ".jpg", ".bmp", ".tiff"):
        destination = service.export(image_artifact, tmp_path / f"out{suffix}")
        assert destination.exists() and destination.stat().st_size > 0
    with pytest.raises(ExportError):
        service.export(
            ImageArtifact("hidden", "Hidden", asset(), exportable=False),
            tmp_path / "hidden.png",
        )
    destination = service.export(
        image_artifact, tmp_path / "preferred-image", preferred_extension=".png"
    )
    assert destination == tmp_path / "preferred-image.png"
    assert destination.exists()


def test_structured_exports(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    service.export(
        CurveArtifact("curve", "Curve", {"x": [0, 1], "y": [2, 3]}), tmp_path / "curve.csv"
    )
    assert (tmp_path / "curve.csv").read_text(encoding="utf-8").splitlines()[0] == "series,x,y"
    service.export(
        TableArtifact("table", "Table", [{"a": "x,y", "b": '"q"'}]), tmp_path / "table.csv"
    )
    assert '"x,y"' in (tmp_path / "table.csv").read_text(encoding="utf-8")
    service.export(MatrixArtifact("matrix", "Matrix", [[1, 2], [3, 4]]), tmp_path / "matrix")
    assert (tmp_path / "matrix.csv").exists()
    service.export(MetricGroupArtifact("metrics", "Metrics", {"snr": 0}), tmp_path / "metrics.txt")
    assert "snr: 0" in (tmp_path / "metrics.txt").read_text(encoding="utf-8")
    service.export(TextArtifact("text", "Text", "hello"), tmp_path / "text.txt")
    curve_destination = service.export(
        CurveArtifact("curve2", "Curve 2", {"x": [0, 1], "y": [1, 0]}),
        tmp_path / "curve-preferred",
        preferred_extension=".csv",
    )
    assert curve_destination == tmp_path / "curve-preferred.csv"


def test_export_validation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    artifact = ImageArtifact("image", "Image", asset())
    with pytest.raises(ExportError):
        service.export(artifact, tmp_path / "missing" / "out.png")
    with pytest.raises(ExportError):
        service.export(artifact, tmp_path)
    with pytest.raises(ExportError):
        service.export(artifact, tmp_path / "out.gif")
    with pytest.raises(ExportError):
        service.export(artifact, tmp_path / "typed.gif", preferred_extension=".png")


def test_histogram_csv_exports(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    for name, payload in (
        ("counts", [0, 2, 0]),
        ("channels", {"red": [1, 0], "green": [0, 1]}),
        ("graph", GraphData((GraphSeries("hist", (0, 1), (0, 5)),))),
    ):
        destination = service.export(
            HistogramArtifact(name, name.title(), payload), tmp_path / f"{name}.csv"
        )
        text = destination.read_text(encoding="utf-8")
        assert text.splitlines()[0] == "series,x,y"
        assert ",0.0," in text


def test_visible_histogram_subset_csv_and_png_export(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    graph = GraphData(
        (
            GraphSeries("Red", (0, 1), (1, 2)),
            GraphSeries("Blue", (0, 1), (3, 4)),
        )
    )
    artifact = HistogramArtifact("visible_histogram", "Visible Histogram", graph)
    csv_path = service.export(artifact, tmp_path / "visible.csv")
    text = csv_path.read_text(encoding="utf-8")
    assert "Red" in text and "Blue" in text and "Green" not in text
    png_path = service.export(artifact, tmp_path / "visible.png", render_source=RenderSource())
    assert png_path.exists() and png_path.stat().st_size > 0


def test_overlay_png_requires_render_source(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = ExportService(ImageIOService())
    artifact = OverlayArtifact("overlay", "Overlay", OverlayData((CircleOverlay(2, 2, 1),)))
    with pytest.raises(ExportError):
        service.export(artifact, tmp_path / "overlay.png")
    destination = service.export(artifact, tmp_path / "overlay.png", render_source=RenderSource())
    assert destination.exists() and destination.stat().st_size > 0
