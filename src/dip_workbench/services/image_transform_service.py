"""Stateless image-editing utility transforms."""

import math
from enum import StrEnum
from pathlib import Path
from typing import ClassVar

import cv2
import numpy as np

from dip_workbench.core import (
    ColourModel,
    ImageAsset,
    InputValidationError,
    OperationExecutionError,
)
from dip_workbench.core.geometry import RectangularRegion


class InterpolationMode(StrEnum):
    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"
    AREA = "area"


class RotationCanvasMode(StrEnum):
    EXPANDED = "expanded"
    CROPPED = "cropped"


class FlipDirection(StrEnum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    BOTH = "both"


class ImageTransformService:
    _INTERPOLATION: ClassVar[dict[InterpolationMode, int]] = {
        InterpolationMode.NEAREST: cv2.INTER_NEAREST,
        InterpolationMode.LINEAR: cv2.INTER_LINEAR,
        InterpolationMode.CUBIC: cv2.INTER_CUBIC,
        InterpolationMode.AREA: cv2.INTER_AREA,
    }

    def crop(self, asset: ImageAsset, region: RectangularRegion) -> ImageAsset:
        self._validate(asset)
        if not isinstance(region, RectangularRegion) or not region.fits_within(
            asset.width, asset.height
        ):
            raise InputValidationError("Crop region must fit within the current image.")
        return self._derived(
            asset,
            asset.data[region.y : region.y2, region.x : region.x2],
            "U-05",
            "Crop",
            "cropped",
            {"region": region},
        )

    def resize(
        self, asset: ImageAsset, *, width: int, height: int, interpolation: InterpolationMode
    ) -> ImageAsset:
        self._validate(asset)
        self._dimensions(width, height)
        self._check_interpolation(asset, interpolation)
        try:
            data = cv2.resize(
                asset.data, (width, height), interpolation=self._INTERPOLATION[interpolation]
            )
        except cv2.error as error:
            raise OperationExecutionError("Image resize failed.") from error
        return self._derived(
            asset,
            data,
            "U-06",
            "Resize",
            "resized",
            {"width": width, "height": height, "interpolation": interpolation.value},
        )

    def rotate(
        self,
        asset: ImageAsset,
        *,
        angle_degrees: float,
        canvas_mode: RotationCanvasMode,
        interpolation: InterpolationMode,
    ) -> ImageAsset:
        self._validate(asset)
        if (
            isinstance(angle_degrees, bool)
            or not isinstance(angle_degrees, (int, float))
            or not math.isfinite(angle_degrees)
        ):
            raise InputValidationError("Rotation angle must be finite.")
        if not isinstance(canvas_mode, RotationCanvasMode):
            raise InputValidationError("Rotation canvas mode is invalid.")
        self._check_interpolation(asset, interpolation, rotation=True)
        normalized = angle_degrees % 360
        if canvas_mode is RotationCanvasMode.EXPANDED and normalized in {0, 90, 180, 270}:
            data = np.rot90(asset.data, {0: 0, 90: 1, 180: 2, 270: 3}[round(normalized)])
        else:
            center = (asset.width / 2.0, asset.height / 2.0)
            matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
            out_w, out_h = asset.width, asset.height
            if canvas_mode is RotationCanvasMode.EXPANDED:
                cosine, sine = abs(matrix[0, 0]), abs(matrix[0, 1])
                out_w = math.ceil(asset.height * sine + asset.width * cosine)
                out_h = math.ceil(asset.height * cosine + asset.width * sine)
                matrix[0, 2] += out_w / 2 - center[0]
                matrix[1, 2] += out_h / 2 - center[1]
            try:
                data = cv2.warpAffine(
                    asset.data,
                    matrix,
                    (out_w, out_h),
                    flags=self._INTERPOLATION[interpolation],
                    borderMode=cv2.BORDER_CONSTANT,
                    borderValue=0,
                )
            except cv2.error as error:
                raise OperationExecutionError("Image rotation failed.") from error
        return self._derived(
            asset,
            data,
            "U-07",
            "Rotate",
            "rotated",
            {
                "angle_degrees": angle_degrees,
                "canvas_mode": canvas_mode.value,
                "interpolation": interpolation.value,
            },
        )

    def flip(self, asset: ImageAsset, *, direction: FlipDirection) -> ImageAsset:
        self._validate(asset)
        if not isinstance(direction, FlipDirection):
            raise InputValidationError("Flip direction is invalid.")
        data = {
            FlipDirection.HORIZONTAL: asset.data[:, ::-1],
            FlipDirection.VERTICAL: asset.data[::-1, :],
            FlipDirection.BOTH: asset.data[::-1, ::-1],
        }[direction]
        return self._derived(
            asset, data, "U-08", "Flip/Mirror", "flipped", {"direction": direction.value}
        )

    @staticmethod
    def _validate(asset: object) -> None:
        if not isinstance(asset, ImageAsset) or asset.colour_model not in {
            ColourModel.RGB,
            ColourModel.GRAY,
            ColourModel.BINARY,
        }:
            raise InputValidationError("Transforms require an RGB, grayscale, or binary asset.")

    @staticmethod
    def _dimensions(width: object, height: object) -> None:
        if any(isinstance(v, bool) or not isinstance(v, int) or v <= 0 for v in (width, height)):
            raise InputValidationError("Transform dimensions must be positive integers.")

    def _check_interpolation(
        self, asset: ImageAsset, mode: InterpolationMode, *, rotation: bool = False
    ) -> None:
        if not isinstance(mode, InterpolationMode) or (rotation and mode is InterpolationMode.AREA):
            raise InputValidationError("Interpolation mode is invalid for this transform.")
        if asset.colour_model is ColourModel.BINARY and mode is not InterpolationMode.NEAREST:
            raise InputValidationError("Binary transforms require nearest-neighbour interpolation.")

    @staticmethod
    def _derived(
        asset: ImageAsset,
        data: np.ndarray,
        operation_id: str,
        operation_name: str,
        suffix: str,
        parameters: dict[str, object],
    ) -> ImageAsset:
        path = Path(asset.name)
        stem = path.stem if path.suffix else asset.name
        if not stem.endswith(f"-{suffix}"):
            stem += f"-{suffix}"
        metadata = dict(asset.metadata)
        metadata.update(
            {
                "derived_from_asset_id": asset.id,
                "utility_operation_id": operation_id,
                "utility_operation_name": operation_name,
                "utility_parameters": parameters,
            }
        )
        return ImageAsset(
            name=f"{stem}{path.suffix}",
            data=np.ascontiguousarray(data),
            colour_model=asset.colour_model,
            source_path=asset.source_path,
            metadata=metadata,
        )
