"""Reduced-resolution preview input foundation."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

import cv2
import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError


@dataclass(frozen=True, slots=True)
class PreviewResolutionPolicy:
    enabled: bool = True
    maximum_dimension: int = 1024

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_dimension, bool)
            or not isinstance(self.maximum_dimension, int)
            or self.maximum_dimension <= 0
        ):
            raise InputValidationError("Preview maximum dimension must be positive.")


class PreviewInputReducer:
    def __init__(self, policy: PreviewResolutionPolicy) -> None:
        if not isinstance(policy, PreviewResolutionPolicy):
            raise InputValidationError("Preview policy is invalid.")
        self.policy = policy

    def reduce_inputs(self, inputs: Mapping[str, object]) -> Mapping[str, object]:
        if not isinstance(inputs, Mapping):
            raise InputValidationError("Preview inputs must be a mapping.")
        return MappingProxyType({key: self._reduce(value) for key, value in inputs.items()})

    def _reduce(self, value: object) -> object:
        if isinstance(value, ImageAsset):
            return self._reduce_asset(value)
        if isinstance(value, Mapping):
            return MappingProxyType({key: self._reduce(item) for key, item in value.items()})
        if isinstance(value, (tuple, list)):
            return tuple(self._reduce(item) for item in value)
        return value

    def _reduce_asset(self, asset: ImageAsset) -> ImageAsset:
        limit = self.policy.maximum_dimension
        longest = max(asset.width, asset.height)
        if not self.policy.enabled or longest <= limit:
            return asset
        scale = limit / longest
        width = max(1, round(asset.width * scale))
        height = max(1, round(asset.height * scale))
        interpolation = (
            cv2.INTER_AREA
            if asset.colour_model in {ColourModel.RGB, ColourModel.GRAY}
            else cv2.INTER_NEAREST
        )
        data = cv2.resize(asset.data, (width, height), interpolation=interpolation)
        if asset.colour_model is ColourModel.LABEL:
            data = data.astype(np.int32, copy=False)
        metadata = dict(asset.metadata)
        metadata.update(
            {
                "preview_original_asset_id": asset.id,
                "preview_original_dimensions": (asset.width, asset.height),
                "preview_dimensions": (width, height),
                "preview_scale_x": width / asset.width,
                "preview_scale_y": height / asset.height,
            }
        )
        return ImageAsset(
            name=asset.name,
            data=np.ascontiguousarray(data),
            colour_model=asset.colour_model,
            source_path=asset.source_path,
            metadata=metadata,
        )
