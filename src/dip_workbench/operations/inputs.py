"""Declarative operation input contracts for one selected image."""

import re
from dataclasses import dataclass

from dip_workbench.core import ColourModel, InputValidationError


@dataclass(frozen=True, slots=True)
class InputSpec:
    key: str
    label: str
    accepted_colour_models: frozenset[ColourModel] = frozenset()
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
        if not isinstance(self.label, str) or not self.label.strip():
            raise InputValidationError("Input label is required.")
        if any(not isinstance(model, ColourModel) for model in self.accepted_colour_models):
            raise InputValidationError("Accepted colour model is invalid.")
        if not (self.allow_original or self.allow_current):
            raise InputValidationError("Input must allow Original or Current Result.")
