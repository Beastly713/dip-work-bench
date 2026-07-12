"""Generic artifact export service."""

from __future__ import annotations

import csv
import os
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Protocol

from PySide6.QtGui import QImage

from dip_workbench.core import ColourModel, ExportError, ImageAsset
from dip_workbench.operations import (
    BitstreamArtifact,
    CurveArtifact,
    HistogramArtifact,
    ImageArtifact,
    LabelMapArtifact,
    MaskArtifact,
    MatrixArtifact,
    MetricGroupArtifact,
    ResultArtifact,
    TableArtifact,
    TextArtifact,
    TreeArtifact,
    TreeNode,
    coerce_graph_data,
    coerce_matrix_data,
    coerce_table_data,
    coerce_tree_data,
)
from dip_workbench.services.image_io_service import ImageIOService


class GraphRenderSource(Protocol):
    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage: ...


class ExportService:
    """Own extension validation, serialization and file writing for artifacts."""

    IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")
    GRAPH_EXTENSIONS = (".png", ".csv")

    def __init__(self, image_io: ImageIOService) -> None:
        self._image_io = image_io

    def supported_extensions(
        self, artifact: ResultArtifact, *, has_render_source: bool = False
    ) -> tuple[str, ...]:
        if not artifact.exportable:
            return ()
        if isinstance(artifact, (ImageArtifact, MaskArtifact)):
            data = artifact.data
            if not isinstance(data, ImageAsset):
                return ()
            if data.colour_model is ColourModel.BINARY:
                return (".png", ".bmp", ".tif", ".tiff")
            if data.colour_model is ColourModel.LABEL:
                return ()
            return self.IMAGE_EXTENSIONS
        if isinstance(artifact, LabelMapArtifact):
            return ()
        if isinstance(artifact, (HistogramArtifact, CurveArtifact)):
            return self.GRAPH_EXTENSIONS if has_render_source else (".csv",)
        if isinstance(artifact, (TableArtifact, MatrixArtifact)):
            return (".csv",)
        if isinstance(
            artifact, (MetricGroupArtifact, TextArtifact, BitstreamArtifact, TreeArtifact)
        ):
            return (".txt",)
        return ()

    def default_extension(
        self, artifact: ResultArtifact, *, has_render_source: bool = False
    ) -> str:
        extensions = self.supported_extensions(artifact, has_render_source=has_render_source)
        if not extensions:
            raise ExportError(f"{artifact.label} cannot be exported.")
        if isinstance(artifact, (HistogramArtifact, CurveArtifact)) and has_render_source:
            return ".png"
        return extensions[0]

    def export(
        self,
        artifact: ResultArtifact,
        destination: str | Path,
        *,
        render_source: GraphRenderSource | None = None,
        preferred_extension: str | None = None,
    ) -> Path:
        if not artifact.exportable:
            raise ExportError(f"{artifact.label} is not exportable.")
        target = Path(destination)
        if target.exists() and target.is_dir():
            raise ExportError("Output destination is a directory.")
        has_render_source = render_source is not None
        suffix = (preferred_extension or target.suffix).lower()
        if not suffix:
            suffix = self.default_extension(artifact, has_render_source=has_render_source)
            target = target.with_suffix(suffix)
        if not target.parent.is_dir():
            raise ExportError("Output parent directory does not exist.")
        if suffix not in self.supported_extensions(artifact, has_render_source=has_render_source):
            raise ExportError(f"Unsupported export extension for {artifact.label}: {suffix}.")
        if isinstance(artifact, LabelMapArtifact):
            raise ExportError("Raw label maps require an explicit display mapping before export.")

        def writer(path: Path) -> None:
            self._write_artifact(artifact, path, render_source=render_source)

        self._safe_write(target, writer)
        return target

    def _write_artifact(
        self,
        artifact: ResultArtifact,
        destination: Path,
        *,
        render_source: GraphRenderSource | None,
    ) -> None:
        if isinstance(artifact, (ImageArtifact, MaskArtifact)):
            if not isinstance(artifact.data, ImageAsset):
                raise ExportError("Image artifact does not contain an image.")
            self._image_io.save(artifact.data, destination)
            return
        if isinstance(artifact, (HistogramArtifact, CurveArtifact)):
            if destination.suffix.lower() == ".png":
                if render_source is None:
                    raise ExportError("Graph PNG export requires a current render source.")
                image = render_source.render_image()
                if image.isNull() or not image.save(str(destination)):
                    raise ExportError("Graph image could not be written.")
                return
            self._write_graph_csv(artifact, destination)
            return
        if isinstance(artifact, TableArtifact):
            table = coerce_table_data(artifact.data)
            self._write_csv(destination, (table.columns, *table.rows))
            return
        if isinstance(artifact, MatrixArtifact):
            matrix = coerce_matrix_data(artifact.data)
            rows: list[tuple[object, ...]] = []
            if matrix.column_labels:
                rows.append(
                    ("", *matrix.column_labels) if matrix.row_labels else matrix.column_labels
                )
            for index, row in enumerate(matrix.values):
                rows.append((matrix.row_labels[index], *row) if matrix.row_labels else row)
            self._write_csv(destination, rows)
            return
        if isinstance(artifact, MetricGroupArtifact):
            self._write_text(destination, self._metrics_text(artifact.data, artifact.metadata))
            return
        if isinstance(artifact, TextArtifact):
            self._write_text(destination, str(artifact.data))
            return
        if isinstance(artifact, BitstreamArtifact):
            data = (
                artifact.data.decode("utf-8")
                if isinstance(artifact.data, bytes)
                else str(artifact.data)
            )
            self._write_text(destination, data)
            return
        if isinstance(artifact, TreeArtifact):
            self._write_text(destination, self._tree_text(coerce_tree_data(artifact.data)))
            return
        raise ExportError(f"{artifact.label} cannot be exported.")

    def _write_graph_csv(self, artifact: ResultArtifact, destination: Path) -> None:
        graph = coerce_graph_data(artifact.data)
        rows: list[tuple[object, object, object]] = [("series", "x", "y")]
        for series in graph.series:
            rows.extend((series.label, x, y) for x, y in zip(series.x, series.y, strict=True))
        self._write_csv(destination, rows)

    def _safe_write(self, destination: Path, writer) -> None:  # type: ignore[no-untyped-def]
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                delete=False,
                dir=destination.parent,
                prefix=f".{destination.name}.",
                suffix=destination.suffix,
            ) as handle:
                temp_path = Path(handle.name)
            writer(temp_path)
            os.replace(temp_path, destination)
        except ExportError:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise
        except OSError as error:
            if temp_path is not None and temp_path.exists():
                temp_path.unlink(missing_ok=True)
            raise ExportError("Artifact could not be written.") from error

    def _write_csv(self, destination: Path, rows: Iterable[Iterable[object]]) -> None:
        try:
            with destination.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerows(rows)
        except OSError as error:
            raise ExportError("CSV export could not be written.") from error

    def _write_text(self, destination: Path, text: str) -> None:
        try:
            destination.write_text(text, encoding="utf-8")
        except OSError as error:
            raise ExportError("Text export could not be written.") from error

    def _metrics_text(self, data: object, metadata: Mapping[str, object]) -> str:
        if not isinstance(data, Mapping):
            raise ExportError("Metric artifact data must be a mapping.")
        units = metadata.get("units") if isinstance(metadata.get("units"), Mapping) else {}
        lines = []
        for key, value in data.items():
            unit = units.get(key, "") if isinstance(units, Mapping) else ""
            suffix = f" {unit}" if unit else ""
            lines.append(f"{key}: {value}{suffix}")
        return "\n".join(lines)

    def _tree_text(self, node: TreeNode, *, depth: int = 0) -> str:
        label = f"{'  ' * depth}{node.label}"
        if node.value is not None:
            label = f"{label}: {node.value}"
        children = [self._tree_text(child, depth=depth + 1) for child in node.children]
        return "\n".join([label, *children])
