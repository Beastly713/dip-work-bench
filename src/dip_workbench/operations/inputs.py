"""Declarative operation input contracts."""

import re
from dataclasses import dataclass
from enum import StrEnum

from dip_workbench.core import ColourModel, InputValidationError


class InputRole(StrEnum):
    PRIMARY_IMAGE = "primary_image"
    SECONDARY_IMAGE = "secondary_image"
    REFERENCE_IMAGE = "reference_image"
    SECOND_FRAME = "second_frame"
    DATASET = "dataset"
    BINARY_MASK = "binary_mask"
    SEED_POINTS = "seed_points"
    MARKERS = "markers"
    REGION_SELECTION = "region_selection"
    CONTOUR_SELECTION = "contour_selection"
    BLOCK_SELECTION = "block_selection"


@dataclass(frozen=True, slots=True)
class InputSpec:
    key: str
    label: str
    role: InputRole
    required: bool = True
    multiple: bool = False
    minimum_count: int = 1
    maximum_count: int | None = 1
    accepted_colour_models: frozenset[ColourModel] = frozenset()
    same_dimensions_as: str | None = None
    requires_interaction: bool = False
    automatic_conversion_allowed: bool = False
    allow_original: bool = True
    allow_current: bool = True
    help_text: str = ""

    def __post_init__(self) -> None:
        if (
            not isinstance(self.key, str)
            or re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", self.key) is None
        ):
            raise InputValidationError("Input key must be snake case.")
        if (
            not isinstance(self.label, str)
            or not self.label.strip()
            or not isinstance(self.role, InputRole)
        ):
            raise InputValidationError("Input label and role are required.")
        for value in (self.minimum_count, self.maximum_count):
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 0
            ):
                raise InputValidationError("Input counts must be non-negative integers.")
        if self.required and self.minimum_count < 1:
            raise InputValidationError("Required inputs need at least one value.")
        if self.maximum_count is not None and self.maximum_count < self.minimum_count:
            raise InputValidationError("Maximum count is too small.")
        if not self.multiple and self.maximum_count != 1:
            raise InputValidationError("Single inputs must have maximum count one.")
        if any(not isinstance(model, ColourModel) for model in self.accepted_colour_models):
            raise InputValidationError("Accepted colour model is invalid.")
        if (
            self.same_dimensions_as is not None
            and re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", self.same_dimensions_as) is None
        ):
            raise InputValidationError("Dimension reference must be an input key.")
        if self.role is InputRole.PRIMARY_IMAGE and not (self.allow_original or self.allow_current):
            raise InputValidationError("Primary input must allow Original or Current.")
