"""Declarative operation parameter contracts."""

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from dip_workbench.core import InputValidationError, ParameterValidationError


class ParameterType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ENUM = "enum"
    RADIO = "radio"
    INTEGER_RANGE = "integer_range"
    KERNEL = "kernel"


@dataclass(frozen=True, slots=True)
class ParameterChoice:
    value: object
    label: str

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise InputValidationError("Choice label is required.")


class ConditionOperator(StrEnum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    IN = "in"
    NOT_IN = "not_in"
    TRUTHY = "truthy"
    FALSY = "falsy"


@dataclass(frozen=True, slots=True)
class ParameterCondition:
    parameter_key: str
    operator: ConditionOperator
    expected_value: object = True

    def __post_init__(self) -> None:
        if not _key(self.parameter_key) or not isinstance(self.operator, ConditionOperator):
            raise InputValidationError("Parameter condition is invalid.")

    def evaluate(self, values: Mapping[str, object]) -> bool:
        if self.parameter_key not in values:
            return False
        value = values[self.parameter_key]
        if self.operator is ConditionOperator.EQUALS:
            return value == self.expected_value
        if self.operator is ConditionOperator.NOT_EQUALS:
            return value != self.expected_value
        if self.operator is ConditionOperator.TRUTHY:
            return bool(value)
        if self.operator is ConditionOperator.FALSY:
            return not bool(value)
        try:
            included = value in self.expected_value  # type: ignore[operator]
        except TypeError:
            return False
        return included if self.operator is ConditionOperator.IN else not included


ParameterValidator = Callable[[object, Mapping[str, object]], str | None]


def _key(value: object) -> bool:
    return (
        isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*", value) is not None
    )


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    key: str
    label: str
    parameter_type: ParameterType
    default: object
    minimum: int | float | None = None
    maximum: int | float | None = None
    step: int | float | None = None
    choices: tuple[ParameterChoice, ...] = ()
    help_text: str = ""
    advanced: bool = False
    visible_when: ParameterCondition | None = None
    enabled_when: ParameterCondition | None = None
    validator: ParameterValidator | None = None

    def __post_init__(self) -> None:
        if (
            not _key(self.key)
            or not isinstance(self.label, str)
            or not self.label.strip()
            or not isinstance(self.parameter_type, ParameterType)
        ):
            raise InputValidationError("Parameter identity is invalid.")
        if self.step is not None and (isinstance(self.step, bool) or self.step <= 0):
            raise InputValidationError("Parameter step must be positive.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise InputValidationError("Parameter bounds are invalid.")
        values = [choice.value for choice in self.choices]
        if any(values.count(value) > 1 for value in values):
            raise InputValidationError("Parameter choices must be unique.")
        try:
            self._validate_builtin(self.default)
        except ParameterValidationError as error:
            raise InputValidationError(str(error)) from error

    def is_visible(self, values: Mapping[str, object]) -> bool:
        return self.visible_when is None or self.visible_when.evaluate(values)

    def is_enabled(self, values: Mapping[str, object]) -> bool:
        return self.enabled_when is None or self.enabled_when.evaluate(values)

    def validate(self, value: object, values: Mapping[str, object]) -> None:
        self._validate_builtin(value)
        if self.validator is not None:
            message = self.validator(value, values)
            if message:
                raise ParameterValidationError(message)

    def _validate_builtin(self, value: object) -> None:
        kind = self.parameter_type
        numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
        if kind is ParameterType.INTEGER and (
            not isinstance(value, int) or isinstance(value, bool)
        ):
            raise ParameterValidationError(f"{self.label} must be an integer.")
        if kind is ParameterType.FLOAT and not numeric:
            raise ParameterValidationError(f"{self.label} must be numeric.")
        if kind is ParameterType.BOOLEAN and not isinstance(value, bool):
            raise ParameterValidationError(f"{self.label} must be boolean.")
        choice_values = [choice.value for choice in self.choices]
        if kind in {ParameterType.ENUM, ParameterType.RADIO} and value not in choice_values:
            raise ParameterValidationError(f"{self.label} has an invalid choice.")
        if kind is ParameterType.INTEGER_RANGE:
            if not isinstance(value, (tuple, list)) or len(value) != 2:
                raise ParameterValidationError(f"{self.label} must contain two values.")
            valid = all(isinstance(v, int) and not isinstance(v, bool) for v in value)
            if not valid or value[0] > value[1]:
                raise ParameterValidationError(f"{self.label} range is invalid.")
        if kind is ParameterType.KERNEL:
            if (
                not isinstance(value, (tuple, list))
                or not value
                or any(not isinstance(row, (tuple, list)) or not row for row in value)
            ):
                raise ParameterValidationError(f"{self.label} kernel is invalid.")
            widths = {len(row) for row in value}
            flat = [item for row in value for item in row]
            if len(widths) != 1 or any(
                not isinstance(v, (int, float)) or isinstance(v, bool) for v in flat
            ):
                raise ParameterValidationError(f"{self.label} kernel is invalid.")
        candidates: list[int | float] = []
        if numeric:
            candidates = [value]  # type: ignore[list-item]
        elif kind is ParameterType.INTEGER_RANGE and isinstance(value, (tuple, list)):
            candidates = list(value)
        if self.minimum is not None and any(v < self.minimum for v in candidates):
            raise ParameterValidationError(f"{self.label} is below minimum.")
        if self.maximum is not None and any(v > self.maximum for v in candidates):
            raise ParameterValidationError(f"{self.label} exceeds maximum.")


def validate_parameter_values(
    schema: tuple[ParameterSpec, ...], supplied_values: Mapping[str, object]
) -> Mapping[str, object]:
    keys = [spec.key for spec in schema]
    if len(keys) != len(set(keys)):
        raise ParameterValidationError("Parameter schema contains duplicate keys.")
    unknown = set(supplied_values) - set(keys)
    if unknown:
        raise ParameterValidationError(f"Unknown parameters: {', '.join(sorted(unknown))}.")
    resolved = {spec.key: spec.default for spec in schema}
    resolved.update(supplied_values)
    for spec in schema:
        spec.validate(resolved[spec.key], resolved)
    return MappingProxyType(resolved)
