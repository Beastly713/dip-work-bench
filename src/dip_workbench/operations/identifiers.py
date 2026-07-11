"""Permanent academic module and operation identifiers."""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from dip_workbench.core import InputValidationError


class ModuleId(StrEnum):
    M01 = "M01"
    M02 = "M02"
    M03 = "M03"
    M04 = "M04"
    M05 = "M05"
    M06 = "M06"
    M07 = "M07"
    M08 = "M08"
    M09 = "M09"
    M10 = "M10"
    M11 = "M11"


MODULE_NAMES: Mapping[ModuleId, str] = MappingProxyType(
    {
        ModuleId.M01: "Image Fundamentals and Representation",
        ModuleId.M02: "Arithmetic and Logical Operations",
        ModuleId.M03: "Intensity Transformations",
        ModuleId.M04: "Histogram Processing",
        ModuleId.M05: "Spatial Filtering and Convolution",
        ModuleId.M06: "Sharpening and Edge Enhancement",
        ModuleId.M07: "Frequency-Domain Processing",
        ModuleId.M08: "Noise Simulation and Restoration",
        ModuleId.M09: "Image Segmentation",
        ModuleId.M10: "Feature Extraction and Shape Analysis",
        ModuleId.M11: "Compression and Quality Analysis",
    }
)


@dataclass(frozen=True, slots=True)
class OperationId:
    value: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.value, str)
            or re.fullmatch(r"M(?:0[1-9]|1[01])-(?:0[1-9]|[1-9][0-9])", self.value) is None
        ):
            raise InputValidationError("Operation ID must use the format M01-01 through M11-99.")

    @property
    def module_id(self) -> ModuleId:
        return ModuleId(self.value[:3])

    @property
    def sequence(self) -> int:
        return int(self.value[4:])

    def __str__(self) -> str:
        return self.value


def parse_operation_id(value: str | OperationId) -> OperationId:
    if isinstance(value, OperationId):
        return value
    if not isinstance(value, str):
        raise InputValidationError("Operation ID must be a string.")
    return OperationId(value)
