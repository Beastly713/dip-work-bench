"""M08-01 Add Noise."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import HistogramArtifact, ImageArtifact
from dip_workbench.operations.definitions import (
    ApplyPolicy,
    OperationDefinition,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.parameters import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
)
from dip_workbench.operations.registry import operation_registry
from dip_workbench.operations.results import OperationResult
from dip_workbench.operations.visualization import GraphData, GraphSeries, GraphStyle

if TYPE_CHECKING:
    from dip_workbench.execution import OperationContext

NOISE_TYPES = tuple(
    ParameterChoice(v, label)
    for v, label in (
        ("gaussian", "Gaussian"),
        ("salt", "Salt"),
        ("pepper", "Pepper"),
        ("salt_and_pepper", "Salt and pepper"),
        ("speckle", "Speckle"),
    )
)
PROCESSING = (
    ParameterChoice("luminance", "Luminance"),
    ParameterChoice("per_channel", "Per channel"),
)


def _probability_validator(_value: object, values: Mapping[str, object]) -> str | None:
    mapping = dict(values)
    salt = mapping.get("salt_probability", 0.0)
    pepper = mapping.get("pepper_probability", 0.0)
    salt_value = (
        float(salt) if isinstance(salt, (int, float)) and not isinstance(salt, bool) else 0.0
    )
    pepper_value = (
        float(pepper) if isinstance(pepper, (int, float)) and not isinstance(pepper, bool) else 0.0
    )
    if mapping.get("noise_type") == "salt_and_pepper" and salt_value + pepper_value > 1.0:
        return "Salt and pepper probabilities must sum to at most 1.0."
    return None


def _clip(data: np.ndarray) -> np.ndarray:
    return np.ascontiguousarray(np.clip(np.rint(data), 0, 255).astype(np.uint8))


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputValidationError(f"{label} must be numeric.")
    return float(value)


def _apply_noise(
    values: np.ndarray,
    params: Mapping[str, object],
    rng: np.random.Generator,
    *,
    whole_pixel: bool,
) -> np.ndarray:
    noise_type = params["noise_type"]
    working = values.astype(np.float64)
    if noise_type == "gaussian":
        noise = rng.normal(
            _number(params["gaussian_mean"], "Gaussian mean"),
            _number(params["gaussian_std"], "Gaussian standard deviation"),
            working.shape,
        )
        return _clip(np.add(working, noise))
    if noise_type == "speckle":
        noise = rng.normal(0.0, _number(params["speckle_std"], "Speckle std"), working.shape)
        return _clip(np.add(working, np.multiply(working, noise)))
    mask_shape = working.shape[:2] if whole_pixel and working.ndim == 3 else working.shape
    if noise_type == "salt":
        salt = rng.random(mask_shape) < _number(params["salt_probability"], "Salt probability")
        output = values.copy()
        output[salt] = 255
        return np.ascontiguousarray(output, dtype=np.uint8)
    if noise_type == "pepper":
        pepper = rng.random(mask_shape) < _number(
            params["pepper_probability"], "Pepper probability"
        )
        output = values.copy()
        output[pepper] = 0
        return np.ascontiguousarray(output, dtype=np.uint8)
    if noise_type == "salt_and_pepper":
        draws = rng.random(mask_shape)
        salt_prob = _number(params["salt_probability"], "Salt probability")
        pepper_prob = _number(params["pepper_probability"], "Pepper probability")
        salt = draws < salt_prob
        pepper = (draws >= salt_prob) & (draws < salt_prob + pepper_prob)
        output = values.copy()
        output[salt] = 255
        output[pepper] = 0
        return np.ascontiguousarray(output, dtype=np.uint8)
    raise InputValidationError("Noise type is invalid.")


class AddNoiseExecutor:
    def execute(self, context: OperationContext) -> OperationResult:
        context.cancellation_token.raise_if_cancelled()
        image = context.inputs.get("image")
        if not isinstance(image, ImageAsset) or image.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
        }:
            raise InputValidationError("Add Noise requires RGB or grayscale input.")
        params = dict(context.parameters)
        seed = params.get("seed")
        if not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2147483647:
            raise InputValidationError("Seed is invalid.")
        if _probability_validator(None, params):
            raise InputValidationError(
                _probability_validator(None, params) or "Noise probabilities are invalid."
            )
        rng = np.random.default_rng(seed)
        processing = params.get("processing")
        if image.colour_model is ColourModel.GRAY:
            source_intensity = image.data
            output = _apply_noise(image.data, params, rng, whole_pixel=False)
            delta = output.astype(np.int16) - source_intensity.astype(np.int16)
            model = ColourModel.GRAY
        elif processing == "per_channel":
            source_intensity = image.data
            output = _apply_noise(image.data, params, rng, whole_pixel=True)
            delta = output.astype(np.int16) - source_intensity.astype(np.int16)
            model = ColourModel.RGB
        elif processing == "luminance":
            ycc = cv2.cvtColor(image.data, cv2.COLOR_RGB2YCrCb)
            y = ycc[..., 0]
            noisy_y = _apply_noise(y, params, rng, whole_pixel=False)
            ycc[..., 0] = noisy_y
            output = cv2.cvtColor(ycc, cv2.COLOR_YCrCb2RGB)
            delta = noisy_y.astype(np.int16) - y.astype(np.int16)
            model = ColourModel.RGB
        else:
            raise InputValidationError("Noise processing mode is invalid.")
        context.cancellation_token.raise_if_cancelled()
        flat_delta = delta.reshape(-1)
        counts, edges = np.histogram(flat_delta, bins=41, range=(-255, 255))
        centres = (edges[:-1] + edges[1:]) / 2.0
        changed = float(np.count_nonzero(flat_delta)) * 100.0 / flat_delta.size
        graph = GraphData(
            (
                GraphSeries(
                    "Applied Delta", tuple(centres.tolist()), tuple(counts.astype(float).tolist())
                ),
            ),
            title="Applied Noise Distribution",
            x_label="Applied delta",
            y_label="Frequency",
            style=GraphStyle.BAR,
        )
        asset = ImageAsset(
            name=f"{Path(image.name).stem}-noisy",
            data=np.ascontiguousarray(output, dtype=np.uint8),
            colour_model=model,
            source_path=image.source_path,
            metadata={
                "operation_id": "M08-01",
                "input_asset_id": image.id,
                **{k: v for k, v in params.items() if k != "kernel"},
            },
        )
        return OperationResult(
            ImageArtifact("noisy_image", "Noisy Image", asset),
            (HistogramArtifact("noise_distribution", "Applied Noise Distribution", graph),),
            metrics={
                "Seed": seed,
                "Mean Applied Delta": float(np.mean(flat_delta)),
                "Standard Deviation of Applied Delta": float(np.std(flat_delta)),
                "Changed Pixels Percentage": changed,
            },
            metadata={"input_asset": image},
        )


def create_noise_parameter_editor() -> object:
    from dip_workbench.ui.operations.noise import NoiseParameterEditor

    return NoiseParameterEditor(ADD_NOISE_DEFINITION.parameter_schema)


def create_add_noise_presenter() -> object:
    from dip_workbench.ui.operations.noise import AddNoisePresenter

    return AddNoisePresenter()


ADD_NOISE_DEFINITION = OperationDefinition(
    OperationId("M08-01"),
    ModuleId.M08,
    "Add Noise",
    "Add reproducible synthetic noise.",
    (
        InputSpec(
            "image",
            "Primary Image",
            accepted_colour_models=frozenset({ColourModel.RGB, ColourModel.GRAY}),
        ),
    ),
    (
        ParameterSpec(
            "noise_type", "Noise Type", ParameterType.ENUM, "gaussian", choices=NOISE_TYPES
        ),
        ParameterSpec(
            "processing", "Processing", ParameterType.ENUM, "luminance", choices=PROCESSING
        ),
        ParameterSpec("seed", "Seed", ParameterType.INTEGER, 42, minimum=0, maximum=2147483647),
        ParameterSpec(
            "gaussian_mean",
            "Gaussian Mean",
            ParameterType.FLOAT,
            0.0,
            minimum=-50.0,
            maximum=50.0,
            visible_when=ParameterCondition("noise_type", ConditionOperator.EQUALS, "gaussian"),
        ),
        ParameterSpec(
            "gaussian_std",
            "Gaussian Std",
            ParameterType.FLOAT,
            20.0,
            minimum=1.0,
            maximum=100.0,
            visible_when=ParameterCondition("noise_type", ConditionOperator.EQUALS, "gaussian"),
        ),
        ParameterSpec(
            "salt_probability",
            "Salt Probability",
            ParameterType.FLOAT,
            0.05,
            minimum=0.0,
            maximum=0.5,
            visible_when=ParameterCondition(
                "noise_type", ConditionOperator.IN, ("salt", "salt_and_pepper")
            ),
            validator=_probability_validator,
        ),
        ParameterSpec(
            "pepper_probability",
            "Pepper Probability",
            ParameterType.FLOAT,
            0.05,
            minimum=0.0,
            maximum=0.5,
            visible_when=ParameterCondition(
                "noise_type", ConditionOperator.IN, ("pepper", "salt_and_pepper")
            ),
            validator=_probability_validator,
        ),
        ParameterSpec(
            "speckle_std",
            "Speckle Std",
            ParameterType.FLOAT,
            0.10,
            minimum=0.01,
            maximum=1.0,
            visible_when=ParameterCondition("noise_type", ConditionOperator.EQUALS, "speckle"),
        ),
    ),
    PreviewPolicy.IMMEDIATE,
    ApplyPolicy.PRIMARY_ARTIFACT,
    PresenterId.T3_ANALYSIS_AND_GRAPH,
    AddNoiseExecutor,
    create_add_noise_presenter,
    custom_parameter_factory=create_noise_parameter_editor,
)

operation_registry.register(ADD_NOISE_DEFINITION)
