"""Immutable operation execution requests, contexts, and outcomes."""

import math
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

import numpy as np

from dip_workbench.core import DIPWorkbenchError, InputValidationError
from dip_workbench.execution.cancellation import CancellationToken
from dip_workbench.operations import OperationDefinition, OperationId, OperationResult


class ExecutionMode(StrEnum):
    PREVIEW = "preview"
    APPLY = "apply"


ProgressCallback = Callable[[float, str], None]


def _freeze(value: object) -> object:
    if isinstance(value, np.ndarray):
        result = np.array(value, copy=True, order="C")
        result.setflags(write=False)
        return result
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(v) for v in value)
    return value


def _mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return _freeze(value)  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class OperationContext:
    inputs: Mapping[str, object]
    parameters: Mapping[str, object]
    interaction_data: Mapping[str, object]
    document_metadata: Mapping[str, object]
    cancellation_token: CancellationToken
    progress_callback: ProgressCallback

    def __post_init__(self) -> None:
        if not isinstance(self.cancellation_token, CancellationToken) or not callable(
            self.progress_callback
        ):
            raise InputValidationError("Operation context cancellation and progress are invalid.")
        for name in ("inputs", "parameters", "interaction_data", "document_metadata"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise InputValidationError("Operation context fields must be mappings.")
            object.__setattr__(self, name, _mapping(value))

    def report_progress(self, percent: float, message: str = "") -> None:
        if (
            isinstance(percent, bool)
            or not isinstance(percent, (int, float))
            or not math.isfinite(percent)
            or not 0 <= percent <= 100
            or not isinstance(message, str)
        ):
            raise InputValidationError("Progress must be finite from 0 to 100 with a text message.")
        self.progress_callback(float(percent), message)


@runtime_checkable
class OperationExecutor(Protocol):
    def execute(self, context: OperationContext) -> OperationResult: ...


@dataclass(frozen=True, slots=True)
class OperationRequest:
    request_id: str
    definition: OperationDefinition
    mode: ExecutionMode
    generation: int
    inputs: Mapping[str, object]
    parameters: Mapping[str, object]
    interaction_data: Mapping[str, object]
    document_metadata: Mapping[str, object]
    cancellation_token: CancellationToken

    def __post_init__(self) -> None:
        try:
            parsed = uuid.UUID(self.request_id)
        except (ValueError, AttributeError) as error:
            raise InputValidationError("Request ID must be a UUID.") from error
        if (
            str(parsed) != self.request_id
            or not isinstance(self.definition, OperationDefinition)
            or not isinstance(self.mode, ExecutionMode)
        ):
            raise InputValidationError("Operation request identity is invalid.")
        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
            or self.generation <= 0
        ):
            raise InputValidationError("Request generation must be positive.")
        for name in ("inputs", "parameters", "interaction_data", "document_metadata"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise InputValidationError("Request fields must be mappings.")
            object.__setattr__(self, name, MappingProxyType(dict(value)))

    @property
    def operation_id(self) -> OperationId:
        return self.definition.id


@dataclass(frozen=True, slots=True)
class ExecutionSuccess:
    request: OperationRequest
    result: OperationResult
    processing_time_ms: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.processing_time_ms, bool)
            or not math.isfinite(self.processing_time_ms)
            or self.processing_time_ms < 0
        ):
            raise InputValidationError("Processing time must be finite and non-negative.")


@dataclass(frozen=True, slots=True)
class ExecutionFailure:
    request: OperationRequest
    error: DIPWorkbenchError


@dataclass(frozen=True, slots=True)
class ExecutionCancelled:
    request: OperationRequest


@dataclass(frozen=True, slots=True)
class ProgressUpdate:
    request: OperationRequest
    percent: float
    message: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.percent, bool)
            or not math.isfinite(self.percent)
            or not 0 <= self.percent <= 100
            or not isinstance(self.message, str)
        ):
            raise InputValidationError("Progress update is invalid.")
