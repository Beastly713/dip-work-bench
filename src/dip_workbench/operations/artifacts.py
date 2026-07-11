"""Typed heterogeneous operation result artifacts."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from types import MappingProxyType
from typing import ClassVar

import numpy as np

from dip_workbench.core import ColourModel, FloatingImage, ImageAsset, InputValidationError

__all__ = [
    "ArtifactType",
    "BitstreamArtifact",
    "ContourSetArtifact",
    "CurveArtifact",
    "DatasetComponentsArtifact",
    "HistogramArtifact",
    "ImageArtifact",
    "KeypointSetArtifact",
    "LabelMapArtifact",
    "MaskArtifact",
    "MatchSetArtifact",
    "MatrixArtifact",
    "MetricGroupArtifact",
    "OverlayArtifact",
    "ResultArtifact",
    "TableArtifact",
    "TextArtifact",
    "TreeArtifact",
]


class ArtifactType(StrEnum):
    IMAGE = "image"
    MASK = "mask"
    LABEL_MAP = "label_map"
    OVERLAY = "overlay"
    HISTOGRAM = "histogram"
    CURVE = "curve"
    MATRIX = "matrix"
    TABLE = "table"
    METRIC_GROUP = "metric_group"
    TEXT = "text"
    TREE = "tree"
    BITSTREAM = "bitstream"
    CONTOUR_SET = "contour_set"
    KEYPOINT_SET = "keypoint_set"
    MATCH_SET = "match_set"
    DATASET_COMPONENTS = "dataset_components"


def _freeze(value: object) -> object:
    if isinstance(value, np.ndarray):
        copied = np.array(value, copy=True, order="C")
        copied.setflags(write=False)
        return copied
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(v) for v in value)
    return value


@dataclass(frozen=True, slots=True)
class ResultArtifact:
    key: str
    label: str
    data: object
    exportable: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)
    ARTIFACT_TYPE: ClassVar[ArtifactType]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.key, str)
            or re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", self.key) is None
            or not isinstance(self.label, str)
            or not self.label.strip()
        ):
            raise InputValidationError("Artifact key and label are invalid.")
        object.__setattr__(self, "data", _freeze(self.data))
        object.__setattr__(self, "metadata", _freeze(self.metadata))

    @property
    def artifact_type(self) -> ArtifactType:
        return self.ARTIFACT_TYPE


class ImageArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.IMAGE


class MaskArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.MASK


class LabelMapArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.LABEL_MAP


class OverlayArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.OVERLAY


class HistogramArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.HISTOGRAM


class CurveArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.CURVE


class MatrixArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.MATRIX


class TableArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.TABLE


class MetricGroupArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.METRIC_GROUP


class TextArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.TEXT


class TreeArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.TREE


class BitstreamArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.BITSTREAM


class ContourSetArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.CONTOUR_SET


class KeypointSetArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.KEYPOINT_SET


class MatchSetArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.MATCH_SET


class DatasetComponentsArtifact(ResultArtifact):
    ARTIFACT_TYPE = ArtifactType.DATASET_COMPONENTS


def _specialized_validation(self: ResultArtifact) -> None:
    if isinstance(self, ImageArtifact) and not isinstance(self.data, (ImageAsset, FloatingImage)):
        raise InputValidationError("Image artifact requires image data.")
    if isinstance(self, MaskArtifact) and (
        not isinstance(self.data, ImageAsset) or self.data.colour_model is not ColourModel.BINARY
    ):
        raise InputValidationError("Mask artifact requires a binary image.")
    if isinstance(self, LabelMapArtifact) and (
        not isinstance(self.data, ImageAsset) or self.data.colour_model is not ColourModel.LABEL
    ):
        raise InputValidationError("Label artifact requires a label map.")
    if isinstance(self, TextArtifact) and not isinstance(self.data, str):
        raise InputValidationError("Text artifact requires text.")
    if isinstance(self, BitstreamArtifact) and not isinstance(self.data, (bytes, str)):
        raise InputValidationError("Bitstream artifact requires bytes or text.")


_base_post = ResultArtifact.__post_init__


def _post(self: ResultArtifact) -> None:
    _base_post(self)
    _specialized_validation(self)


ResultArtifact.__post_init__ = _post  # type: ignore[method-assign]
