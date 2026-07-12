"""Generate a concise Lena experiment report for all academic operations.

The runner intentionally uses the repository's registered operation executors rather than GUI
automation. It writes a clean, repeatable report tree under report_outputs/.
"""

from __future__ import annotations

import csv
import json
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import (
    CurveArtifact,
    HistogramArtifact,
    ImageArtifact,
    MaskArtifact,
    MatrixArtifact,
    OverlayArtifact,
    TableArtifact,
    coerce_graph_data,
    coerce_histogram_data,
    coerce_matrix_data,
    coerce_table_data,
    operation_registry,
)
from dip_workbench.operations.overlays import CircleOverlay, LineOverlay, PointOverlay
from dip_workbench.operations.results import OperationResult
from dip_workbench.services import ImageIOService

ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "lena.png"
OUTPUT_ROOT = ROOT / "report_outputs"


@dataclass(frozen=True)
class RunSpec:
    suffix: str
    parameters: Mapping[str, object]
    notes: str


@dataclass(frozen=True)
class OperationPlan:
    runs: tuple[RunSpec, ...]
    files: Mapping[str, str]
    notes: str


def main() -> None:
    if not INPUT_PATH.is_file():
        raise SystemExit("lena.png must exist at the repository root.")

    image_io = ImageIOService()
    image = image_io.load(INPUT_PATH)
    input_summary = {
        "width": image.width,
        "height": image.height,
        "dtype": str(image.data.dtype),
        "channels": 1 if image.data.ndim == 2 else int(image.data.shape[2]),
        "colour_model": image.colour_model.value,
    }

    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir()

    plans = build_manifest()
    report_rows: list[dict[str, object]] = []
    for definition in operation_registry.all():
        op_id = str(definition.id)
        if op_id not in plans:
            raise RuntimeError(f"No report plan exists for {op_id}.")
        report_rows.append(
            run_operation(
                image_io=image_io,
                image=image,
                input_summary=input_summary,
                op_id=op_id,
                plan=plans[op_id],
            )
        )

    write_report(input_summary, report_rows)
    print(f"Generated {len(report_rows)} operation directories in {OUTPUT_ROOT.relative_to(ROOT)}")


def build_manifest() -> dict[str, OperationPlan]:
    return {
        "M01-01": plan(
            {"grayscale_image": "result.png"},
            {"method": "luminance"},
            "Luminance grayscale conversion gives a professor-friendly single-channel baseline.",
        ),
        "M01-02": OperationPlan(
            (
                RunSpec(
                    "manual",
                    {"mode": "manual", "threshold": 128, "polarity": "bright_foreground"},
                    "Manual threshold at the mid-gray value.",
                ),
                RunSpec(
                    "otsu",
                    {"mode": "otsu", "threshold": 128, "polarity": "bright_foreground"},
                    "Otsu automatically estimates the threshold.",
                ),
            ),
            {"manual:binary_image": "result_manual.png", "otsu:binary_image": "result_otsu.png"},
            "Manual and Otsu thresholding are the two meaningful binary variants.",
        ),
        "M01-03": plan(
            {
                "red_channel": "red_channel.png",
                "green_channel": "green_channel.png",
                "blue_channel": "blue_channel.png",
            },
            {"channel": "all", "display": "intensity"},
            "All RGB channels are shown as intensity images.",
        ),
        "M02-02": plan(
            {"adjusted_image": "result.png"},
            {"brightness": 25, "contrast": 1.15},
            "A moderate brightness and contrast increase keeps Lena recognizable.",
        ),
        "M03-01": plan(
            {"negative_image": "result.png"},
            {"colour_handling": "luminance"},
            "Default luminance negative emphasizes tonal inversion.",
        ),
        "M03-03": OperationPlan(
            (
                RunSpec("gamma_0_6", {"gamma": 0.6}, "Gamma below 1 brightens midtones."),
                RunSpec("gamma_1_8", {"gamma": 1.8}, "Gamma above 1 darkens midtones."),
            ),
            {
                "gamma_0_6:gamma_corrected_image": "result_gamma_0_6.png",
                "gamma_0_6:gamma_curve": "gamma_curve_0_6.png",
                "gamma_0_6:gamma_curve:csv": "gamma_curve_0_6.csv",
                "gamma_1_8:gamma_corrected_image": "result_gamma_1_8.png",
                "gamma_1_8:gamma_curve": "gamma_curve_1_8.png",
                "gamma_1_8:gamma_curve:csv": "gamma_curve_1_8.csv",
            },
            "Two gamma values demonstrate opposite brightness effects without clutter.",
        ),
        "M04-01": plan(
            {
                "rgb_histogram": "rgb_histogram.png",
                "rgb_histogram:csv": "rgb_histogram.csv",
                "grayscale_histogram": "grayscale_histogram.png",
                "grayscale_histogram:csv": "grayscale_histogram.csv",
            },
            {"mode": "ordinary", "bins": 256},
            "Ordinary 256-bin histograms show the tonal distribution directly.",
        ),
        "M04-02": plan(
            {
                "equalized_image": "result.png",
                "histogram_comparison": "histogram_comparison.png",
                "histogram_comparison:csv": "histogram_comparison.csv",
                "input_cdf": "input_cdf.png",
                "input_cdf:csv": "input_cdf.csv",
                "equalization_mapping": "equalization_mapping.png",
                "equalization_mapping:csv": "equalization_mapping.csv",
            },
            {},
            "Equalization is run once using the implemented histogram mapping.",
        ),
        "M05-01": plan(
            {"filtered_image": "result.png"},
            {
                "filter_method": "gaussian",
                "kernel_size": 5,
                "gaussian_sigma": 1.0,
                "border": "reflect",
                "constant_value": 0,
            },
            "A 5x5 Gaussian blur gives a smooth, meaningful denoising example.",
        ),
        "M05-05": plan(
            {
                "convolution_result": "result.png",
                "resolved_kernel:csv": "resolved_kernel.csv",
                "flipped_kernel:csv": "flipped_kernel.csv",
            },
            {
                "preset": "custom",
                "kernel_size": 3,
                "kernel": ((-2.0, -1.0, 0.0), (-1.0, 1.0, 1.0), (0.0, 1.0, 2.0)),
                "normalize_kernel": False,
                "colour_handling": "per_channel",
                "border": "reflect",
                "constant_value": 0,
                "display_mapping": "normalized",
            },
            "The specified directional custom kernel is saved with its resolved/flipped forms.",
        ),
        "M06-01": plan(
            {
                "gradient_x_display": "gradient_x.png",
                "gradient_y_display": "gradient_y.png",
                "gradient_magnitude": "gradient_magnitude.png",
            },
            {"method": "prewitt"},
            "Prewitt gradients expose horizontal, vertical and combined edge strength.",
        ),
        "M06-02": plan(
            {
                "sobel_x_display": "sobel_x.png",
                "sobel_y_display": "sobel_y.png",
                "sobel_result": "sobel_magnitude.png",
            },
            {"kernel_size": 3, "scale": 1.0, "threshold_enabled": False, "threshold": 100},
            "Unthresholded Sobel output preserves continuous edge magnitude.",
        ),
        "M06-03": plan(
            {"laplacian_response": "result.png", "laplacian_kernel:csv": "laplacian_kernel.csv"},
            {"neighbourhood": "eight", "display": "signed_heatmap", "scale": 1.0},
            "The eight-neighbour signed heatmap shows positive and negative second derivatives.",
        ),
        "M06-04": plan(
            {
                "sharpened_image": "result.png",
                "laplacian_display": "laplacian_response.png",
                "laplacian_kernel:csv": "laplacian_kernel.csv",
            },
            {
                "neighbourhood": "four",
                "strength": 1.0,
                "colour_handling": "preserve_luminance_colour",
            },
            "Laplacian sharpening enhances detail while preserving colour appearance.",
        ),
        "M06-05": plan(
            {
                "unsharp_image": "result.png",
                "blurred_image": "blurred_image.png",
                "detail_display": "detail_mask.png",
            },
            {"kernel_size": 5, "sigma": 1.0, "amount": 0.7},
            "Unsharp masking adds a controlled detail mask back to the source.",
        ),
        "M06-06": plan(
            {
                "high_boost_image": "result.png",
                "blurred_image": "blurred_image.png",
                "detail_display": "detail_mask.png",
            },
            {"kernel_size": 5, "sigma": 1.0, "boost": 1.8},
            "High-boost filtering uses a stronger detail emphasis than unsharp masking.",
        ),
        "M07-01": plan(
            {"fourier_magnitude": "magnitude_spectrum.png"},
            {"center_spectrum": True, "logarithmic_scale": True, "show_phase": False},
            "A centered logarithmic magnitude spectrum makes frequency energy visible.",
        ),
        "M07-03": plan(
            {
                "low_pass_result": "result.png",
                "low_pass_input_spectrum": "input_spectrum.png",
                "low_pass_mask": "frequency_mask.png",
                "low_pass_filtered_spectrum": "filtered_spectrum.png",
            },
            {"cutoff_percent": 15.0},
            "The low-pass filter keeps central low-frequency content.",
        ),
        "M07-04": plan(
            {
                "high_pass_result": "result.png",
                "high_pass_input_spectrum": "input_spectrum.png",
                "high_pass_mask": "frequency_mask.png",
                "high_pass_filtered_spectrum": "filtered_spectrum.png",
            },
            {"cutoff_percent": 10.0},
            "The high-pass filter suppresses smooth low-frequency content.",
        ),
        "M08-01": OperationPlan(
            (
                RunSpec(
                    "gaussian",
                    {
                        "noise_type": "gaussian",
                        "processing": "luminance",
                        "seed": 42,
                        "gaussian_mean": 0.0,
                        "gaussian_std": 20.0,
                        "salt_probability": 0.05,
                        "pepper_probability": 0.05,
                        "speckle_std": 0.1,
                    },
                    "Gaussian noise with fixed seed.",
                ),
                RunSpec(
                    "salt_and_pepper",
                    {
                        "noise_type": "salt_and_pepper",
                        "processing": "luminance",
                        "seed": 42,
                        "gaussian_mean": 0.0,
                        "gaussian_std": 20.0,
                        "salt_probability": 0.03,
                        "pepper_probability": 0.03,
                        "speckle_std": 0.1,
                    },
                    "Balanced salt-and-pepper impulse noise.",
                ),
                RunSpec(
                    "speckle",
                    {
                        "noise_type": "speckle",
                        "processing": "luminance",
                        "seed": 42,
                        "gaussian_mean": 0.0,
                        "gaussian_std": 20.0,
                        "salt_probability": 0.05,
                        "pepper_probability": 0.05,
                        "speckle_std": 0.10,
                    },
                    "Multiplicative speckle noise.",
                ),
            ),
            {
                "gaussian:noisy_image": "result_gaussian.png",
                "gaussian:noise_distribution": "noise_distribution_gaussian.png",
                "gaussian:noise_distribution:csv": "noise_distribution_gaussian.csv",
                "salt_and_pepper:noisy_image": "result_salt_and_pepper.png",
                "speckle:noisy_image": "result_speckle.png",
            },
            "Three representative noise families are run with a fixed seed.",
        ),
        "M09-02": plan(
            {"range_mask": "mask.png", "range_overlay": "overlay.png"},
            {"intensity_range": (80, 180), "include_boundaries": True},
            "The chosen intensity band selects midtones and visualizes them as an overlay.",
        ),
        "M09-03": plan(
            {
                "colour_mask": "mask.png",
                "extracted_region": "extracted_region.png",
                "colour_overlay": "overlay.png",
            },
            {"red_range": (150, 255), "green_range": (70, 210), "blue_range": (50, 190)},
            "The bounded RGB range selects warm skin/face tones from Lena.",
        ),
        "M09-05": plan(
            {
                "adaptive_mask": "adaptive_mask.png",
                "global_otsu_mask": "global_otsu_comparison.png",
            },
            {
                "block_size": 11,
                "offset": 2,
                "polarity": "bright_foreground",
                "include_global_otsu_comparison": True,
            },
            "Adaptive thresholding is paired with a global Otsu reference.",
        ),
        "M10-01": plan(
            {"canny_edges": "result.png", "canny_smoothed": "smoothed_input.png"},
            {
                "blur_kernel": 5,
                "sigma": 1.0,
                "low_threshold": 50,
                "high_threshold": 150,
                "aperture_size": 3,
                "l2_gradient": True,
            },
            "Canny edges are generated with a standard smoothed two-threshold setup.",
        ),
        "M10-02": plan(
            {
                "log_edges": "result.png",
                "log_smoothed": "smoothed_input.png",
                "log_response_display": "signed_response.png",
            },
            {
                "gaussian_kernel": 5,
                "sigma": 1.0,
                "neighbourhood": "eight",
                "zero_crossing_contrast": 10.0,
            },
            "LoG uses Gaussian smoothing followed by zero-crossing detection.",
        ),
        "M10-03": plan(
            {
                "dog_edges": "result.png",
                "dog_small_blur": "small_sigma_blur.png",
                "dog_large_blur": "large_sigma_blur.png",
                "dog_response_display": "signed_response.png",
            },
            {"sigma_small": 1.0, "sigma_large": 2.0, "edge_threshold": 5.0},
            "DoG compares two blurred scales to reveal edges.",
        ),
        "M10-04": plan(
            {
                "detected_lines": "overlay.png",
                "line_edge_map": "line_edge_map.png",
                "line_detections:csv": "line_detections.csv",
            },
            {
                "canny_low": 50,
                "canny_high": 150,
                "rho_resolution": 1.0,
                "theta_resolution_degrees": 1.0,
                "vote_threshold": 50,
                "minimum_line_length": 30,
                "maximum_line_gap": 10,
                "maximum_lines": 30,
            },
            "A bounded Hough line setup detects the strongest line segments.",
        ),
        "M10-05": plan(
            {
                "detected_circles": "overlay.png",
                "circle_preprocessed": "circle_preprocessed.png",
                "circle_detections:csv": "circle_detections.csv",
            },
            {
                "median_kernel": 5,
                "dp": 1.2,
                "minimum_distance": 20,
                "canny_high_threshold": 100.0,
                "accumulator_threshold": 30.0,
                "minimum_radius": 5,
                "maximum_radius": 80,
                "maximum_circles": 10,
            },
            "A bounded Hough circle setup looks for the most salient circular structures.",
        ),
        "M10-06": plan(
            {
                "detected_corners": "overlay.png",
                "harris_response_display": "harris_response.png",
                "corner_detections:csv": "corner_detections.csv",
            },
            {
                "block_size": 2,
                "aperture_size": 3,
                "harris_k": 0.04,
                "quality_level": 0.01,
                "minimum_distance": 10,
                "maximum_corners": 100,
                "subpixel_refinement": False,
            },
            "Harris corners are limited to the strongest 100 detections.",
        ),
    }


def plan(files: Mapping[str, str], parameters: Mapping[str, object], notes: str) -> OperationPlan:
    return OperationPlan((RunSpec("main", parameters, notes),), files, notes)


def run_operation(
    *,
    image_io: ImageIOService,
    image: ImageAsset,
    input_summary: Mapping[str, object],
    op_id: str,
    plan: OperationPlan,
) -> dict[str, object]:
    definition = operation_registry.get(op_id)
    op_dir = OUTPUT_ROOT / op_id
    op_dir.mkdir()
    results: dict[str, OperationResult] = {}
    attempt_log: list[dict[str, object]] = []

    for run in bounded_runs(op_id, plan.runs):
        result = execute(definition.executor_factory(), image, run.parameters)
        results[run.suffix] = result
        attempt_log.append(
            {
                "suffix": run.suffix,
                "parameters": to_jsonable(run.parameters),
                "notes": run.notes,
                "metrics": to_jsonable(result.metrics),
                "status": "success",
            }
        )
        if op_id in {"M10-04", "M10-05"} and should_stop_tuning(op_id, result):
            break

    artifacts = save_expected_artifacts(image_io, image, op_dir, plan.files, results)
    artifacts.extend(write_derived_plates(op_dir, op_id, artifacts))

    final_result = next(reversed(results.values()))
    selected_parameters = (
        attempt_log[0]["parameters"]
        if len(attempt_log) == 1
        else {item["suffix"]: item["parameters"] for item in attempt_log}
    )
    metadata = {
        "operation_id": op_id,
        "operation_name": definition.display_name,
        "input_image": "lena.png",
        "input_path": "lena.png",
        "input_summary": dict(input_summary),
        "selected_experiment": {
            "parameters": selected_parameters,
            "notes": plan.notes,
        },
        "artifacts": artifacts,
        "metrics": to_jsonable(final_result.metrics),
        "attempt_log": attempt_log,
        "status": "success",
    }
    (op_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    write_analysis(op_dir, definition.display_name, op_id, input_summary, metadata)

    return {
        "operation_id": op_id,
        "operation_name": definition.display_name,
        "purpose": definition.short_description,
        "parameters": metadata["selected_experiment"]["parameters"],
        "observation": observation(metadata),
        "artifacts": artifacts,
        "attempts": len(attempt_log),
    }


def execute(
    executor: object, image: ImageAsset, parameters: Mapping[str, object]
) -> OperationResult:
    context = OperationContext(
        {"image": image},
        parameters,
        {},
        {},
        CancellationToken(),
        lambda *_args: None,
    )
    result = executor.execute(context)  # type: ignore[attr-defined]
    if not isinstance(result, OperationResult):
        raise RuntimeError("Operation executor did not return OperationResult.")
    return result


def bounded_runs(op_id: str, runs: tuple[RunSpec, ...]) -> tuple[RunSpec, ...]:
    if op_id == "M10-04":
        base = dict(runs[0].parameters)
        return (
            runs[0],
            RunSpec("tuned_2", {**base, "vote_threshold": 35}, "Lowered vote threshold if needed."),
            RunSpec(
                "tuned_3",
                {**base, "vote_threshold": 25, "minimum_line_length": 20},
                "Lowered vote threshold and line length if needed.",
            ),
        )
    if op_id == "M10-05":
        base = dict(runs[0].parameters)
        return (
            runs[0],
            RunSpec(
                "tuned_2",
                {**base, "accumulator_threshold": 22.0},
                "Lowered accumulator threshold if needed.",
            ),
            RunSpec(
                "tuned_3",
                {**base, "accumulator_threshold": 18.0, "maximum_circles": 10},
                "Lowered accumulator threshold further if needed.",
            ),
        )
    return runs


def should_stop_tuning(op_id: str, result: OperationResult) -> bool:
    if op_id == "M10-04":
        return result.metrics.get("Detected Lines", 0) > 0
    if op_id == "M10-05":
        return result.metrics.get("Detected Circles", 0) > 0
    return True


def save_expected_artifacts(
    image_io: ImageIOService,
    image: ImageAsset,
    op_dir: Path,
    files: Mapping[str, str],
    results: Mapping[str, OperationResult],
) -> list[dict[str, str]]:
    saved: list[dict[str, str]] = []
    for selector, filename in files.items():
        run_suffix, artifact_key, export_kind = parse_selector(selector, results)
        artifact = results[run_suffix].get_artifact(artifact_key)
        path = op_dir / filename
        if isinstance(artifact, (ImageArtifact, MaskArtifact)):
            if export_kind == "csv":
                raise RuntimeError(f"{selector} is an image artifact, not CSV.")
            save_image_asset(image_io, artifact.data, path)
            artifact_type = "mask" if isinstance(artifact, MaskArtifact) else "image"
        elif isinstance(artifact, (HistogramArtifact, CurveArtifact)):
            graph = (
                coerce_histogram_data(artifact.data)
                if isinstance(artifact, HistogramArtifact)
                else coerce_graph_data(artifact.data)
            )
            if export_kind == "csv":
                write_graph_csv(path, graph)
                artifact_type = "csv"
            else:
                write_graph_png(path, graph)
                artifact_type = "graph" if isinstance(artifact, HistogramArtifact) else "curve"
        elif isinstance(artifact, MatrixArtifact):
            write_matrix_csv(path, coerce_matrix_data(artifact.data))
            artifact_type = "csv"
        elif isinstance(artifact, TableArtifact):
            write_table_csv(path, coerce_table_data(artifact.data))
            artifact_type = "csv"
        elif isinstance(artifact, OverlayArtifact):
            if export_kind == "csv":
                raise RuntimeError(f"{selector} is an overlay artifact, not CSV.")
            write_overlay_png(path, image, artifact.data.items)  # type: ignore[attr-defined]
            artifact_type = "overlay"
        else:
            raise RuntimeError(f"Unsupported artifact type for {selector}.")
        saved.append(
            {
                "key": artifact.key,
                "type": artifact_type,
                "filename": filename,
                "description": artifact.label,
            }
        )
    return saved


def parse_selector(
    selector: str, results: Mapping[str, OperationResult]
) -> tuple[str, str, str | None]:
    parts = selector.split(":")
    export_kind = "csv" if parts[-1] == "csv" else None
    if export_kind:
        parts = parts[:-1]
    if len(parts) == 2:
        return parts[0], parts[1], export_kind
    return ("main" if "main" in results else next(iter(results))), parts[0], export_kind


def save_image_asset(image_io: ImageIOService, data: object, path: Path) -> None:
    if not isinstance(data, ImageAsset):
        raise RuntimeError(f"{path.name} does not contain an ImageAsset.")
    image_io.save(data, path)


def write_graph_csv(path: Path, graph: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("series", "x", "y"))
        for series in graph.series:
            writer.writerows((series.label, x, y) for x, y in zip(series.x, series.y, strict=True))


def write_matrix_csv(path: Path, matrix: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        if matrix.column_labels:
            writer.writerow(
                ("", *matrix.column_labels) if matrix.row_labels else matrix.column_labels
            )
        for index, row in enumerate(matrix.values):
            writer.writerow((matrix.row_labels[index], *row) if matrix.row_labels else row)


def write_table_csv(path: Path, table: Any) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(table.columns)
        writer.writerows(table.rows)


def write_graph_png(path: Path, graph: Any) -> None:
    canvas = np.full((480, 760, 3), 255, dtype=np.uint8)
    plot = (70, 40, 720, 410)
    cv2.rectangle(canvas, (plot[0], plot[1]), (plot[2], plot[3]), (40, 40, 40), 1)
    all_x = [x for series in graph.series for x in series.x]
    all_y = [y for series in graph.series for y in series.y]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    if x_min == x_max:
        x_max += 1
    if y_min == y_max:
        y_max += 1
    colours = ((220, 60, 60), (60, 170, 60), (60, 90, 220), (180, 120, 40))

    def point(x: float, y: float) -> tuple[int, int]:
        px = int(plot[0] + (x - x_min) * (plot[2] - plot[0]) / (x_max - x_min))
        py = int(plot[3] - (y - y_min) * (plot[3] - plot[1]) / (y_max - y_min))
        return px, py

    for index, series in enumerate(graph.series):
        colour = colours[index % len(colours)]
        pts = [point(x, y) for x, y in zip(series.x, series.y, strict=True)]
        if getattr(graph, "style", "") == "bar" and len(pts) <= 300:
            baseline = point(x_min, 0 if y_min <= 0 <= y_max else y_min)[1]
            for px, py in pts:
                cv2.line(canvas, (px, baseline), (px, py), colour, 1)
        else:
            cv2.polylines(canvas, [np.array(pts, dtype=np.int32)], False, colour, 2)
        cv2.putText(
            canvas,
            series.label[:28],
            (90 + index * 160, 450),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            colour,
            1,
            cv2.LINE_AA,
        )
    if graph.title:
        cv2.putText(canvas, graph.title[:80], (70, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    cv2.imwrite(str(path), canvas)


def write_overlay_png(path: Path, image: ImageAsset, items: Sequence[object]) -> None:
    base = image.data
    if image.colour_model is not ColourModel.RGB:
        rgb = cv2.cvtColor(base, cv2.COLOR_GRAY2RGB)
    else:
        rgb = np.array(base, copy=True)
    for item in items:
        if isinstance(item, LineOverlay):
            cv2.line(
                rgb,
                (round(item.x1), round(item.y1)),
                (round(item.x2), round(item.y2)),
                (255, 0, 0),
                2,
                cv2.LINE_AA,
            )
        elif isinstance(item, CircleOverlay):
            cv2.circle(
                rgb,
                (round(item.center_x), round(item.center_y)),
                round(item.radius),
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
        elif isinstance(item, PointOverlay):
            cv2.circle(rgb, (round(item.x), round(item.y)), round(item.radius), (255, 0, 0), -1)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def write_derived_plates(
    op_dir: Path, op_id: str, artifacts: list[dict[str, str]]
) -> list[dict[str, str]]:
    filenames = {item["filename"] for item in artifacts}
    derived: list[dict[str, str]] = []
    if op_id == "M01-02":
        if make_plate(op_dir, ("result_manual.png", "result_otsu.png"), "comparison.png"):
            derived.append(plate_artifact("comparison.png", "Manual/Otsu comparison plate"))
    elif op_id == "M01-03":
        if make_plate(
            op_dir, ("red_channel.png", "green_channel.png", "blue_channel.png"), "triptych.png"
        ):
            derived.append(plate_artifact("triptych.png", "RGB channel triptych"))
    elif op_id in {"M03-03", "M08-01"}:
        candidates = sorted(
            name for name in filenames if name.startswith("result_") and name.endswith(".png")
        )
        if make_plate(op_dir, tuple(candidates), "comparison.png"):
            derived.append(plate_artifact("comparison.png", "Variant comparison plate"))
    elif op_id in {"M06-01", "M06-02"}:
        candidates = (
            (
                "gradient_x.png",
                "gradient_y.png",
                "gradient_magnitude.png",
            )
            if op_id == "M06-01"
            else ("sobel_x.png", "sobel_y.png", "sobel_magnitude.png")
        )
        if make_plate(op_dir, candidates, "triptych.png"):
            derived.append(plate_artifact("triptych.png", "Directional response triptych"))
    return derived


def plate_artifact(filename: str, description: str) -> dict[str, str]:
    return {
        "key": filename.removesuffix(".png"),
        "type": "image",
        "filename": filename,
        "description": description,
    }


def make_plate(op_dir: Path, filenames: tuple[str, ...], output_name: str) -> bool:
    images = []
    labels = []
    for filename in filenames:
        path = op_dir / filename
        if not path.is_file():
            continue
        data = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if data is None:
            continue
        images.append(cv2.resize(data, (256, 256), interpolation=cv2.INTER_AREA))
        labels.append(filename.removesuffix(".png"))
    if not images:
        return False
    label_h = 34
    panels = []
    for image, label in zip(images, labels, strict=True):
        panel = np.full((image.shape[0] + label_h, image.shape[1], 3), 255, dtype=np.uint8)
        panel[label_h:, :] = image
        cv2.putText(panel, label[:28], (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 0, 0), 1)
        panels.append(panel)
    cv2.imwrite(str(op_dir / output_name), np.hstack(panels))
    return True


def write_analysis(
    op_dir: Path,
    operation_name: str,
    op_id: str,
    input_summary: Mapping[str, object],
    metadata: Mapping[str, object],
) -> None:
    params = metadata["selected_experiment"]["parameters"]
    artifacts = metadata["artifacts"]
    metrics = metadata["metrics"]
    lines = [
        f"# {op_id} — {operation_name}",
        "",
        "## Purpose",
        purpose_sentence(operation_name),
        "",
        "## Input",
        "- File: `lena.png`",
        f"- Size: `{input_summary['width']} x {input_summary['height']}`",
        f"- Colour model: `{input_summary['colour_model']}`",
        "",
        "## Parameters Used",
    ]
    for key, value in dict(params).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Generated Artifacts"])
    for artifact in artifacts:  # type: ignore[assignment]
        lines.append(f"- `{artifact['filename']}` — {artifact['description']}")
    lines.extend(["", "## Key Metrics"])
    metric_items = list(dict(metrics).items())[:5]
    if metric_items:
        for key, value in metric_items:
            lines.append(f"- {key}: {format_metric(value)}")
    else:
        lines.append("- No numeric metrics reported by this operation.")
    lines.extend(["", "## Observation", observation(metadata), ""])
    (op_dir / "analysis.md").write_text("\n".join(lines), encoding="utf-8")


def write_report(input_summary: Mapping[str, object], rows: list[dict[str, object]]) -> None:
    lines = [
        "# DIP Workbench Lena Experiment Report",
        "",
        "## Input Image Summary",
        "- File: `lena.png`",
        f"- Size: `{input_summary['width']} x {input_summary['height']}`",
        f"- Colour model: `{input_summary['colour_model']}`",
        f"- Data type: `{input_summary['dtype']}`",
        "",
        "## Methodology",
        "Each academic operation was executed through the registered DIP Workbench executor path using a single curated parameter setup, with only the manifest-approved compact variants.",
        "",
    ]
    for row in rows:
        op_id = row["operation_id"]
        lines.extend(
            [
                f"## {op_id} — {row['operation_name']}",
                "",
                f"Purpose: {row['purpose']}",
                "",
                "Parameters: "
                + ", ".join(f"`{k}={v}`" for k, v in dict(row["parameters"]).items()),
                "",
                f"Observation: {row['observation']}",
                "",
                "Files: "
                + ", ".join(
                    f"[{item['filename']}]({op_id}/{item['filename']})"
                    for item in row["artifacts"]  # type: ignore[index]
                ),
                "",
            ]
        )
    (OUTPUT_ROOT / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def purpose_sentence(operation_name: str) -> str:
    return f"Demonstrate {operation_name.lower()} on the standard Lena input."


def observation(metadata: Mapping[str, object]) -> str:
    metrics = dict(metadata.get("metrics", {}))
    if metrics:
        key, value = next(iter(metrics.items()))
        return f"The selected setup produced clear visual output; the leading reported metric is {key} = {format_metric(value)}."
    artifacts = metadata.get("artifacts", [])
    count = len(artifacts) if isinstance(artifacts, Sequence) else 0
    return (
        f"The selected setup produced {count} concise artifact(s) suitable for visual comparison."
    )


def format_metric(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def to_jsonable(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, tuple):
        return [to_jsonable(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


if __name__ == "__main__":
    main()
