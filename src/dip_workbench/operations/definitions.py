"""Immutable academic operation definitions."""

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from dip_workbench.core import InputValidationError
from dip_workbench.operations.identifiers import ModuleId, OperationId
from dip_workbench.operations.inputs import InputSpec
from dip_workbench.operations.parameters import ParameterSpec


class PreviewPolicy(StrEnum):
    NONE = "none"
    IMMEDIATE = "immediate"
    DEBOUNCED = "debounced"
    EXPLICIT = "explicit"


class ApplyPolicy(StrEnum):
    NONE = "none"
    PRIMARY_ARTIFACT = "primary_artifact"
    EXPLICIT_CANDIDATES = "explicit_candidates"


class PresenterId(StrEnum):
    T1_SINGLE_IMAGE_TRANSFORMATION = "T1"
    T2_DUAL_IMAGE_TRANSFORMATION = "T2"
    T3_ANALYSIS_AND_GRAPH = "T3"
    T4_OVERLAY_AND_FEATURE_DETECTION = "T4"
    T5_INTERACTIVE_CANVAS = "T5"
    T6_DATA_AND_COMPRESSION = "T6"
    T7_DATASET_ANALYSIS = "T7"


Factory = Callable[[], object]


@dataclass(frozen=True, slots=True)
class OperationDefinition:
    id: OperationId
    module_id: ModuleId
    display_name: str
    short_description: str
    input_spec: tuple[InputSpec, ...]
    parameter_schema: tuple[ParameterSpec, ...]
    preview_policy: PreviewPolicy
    apply_policy: ApplyPolicy
    presenter_id: PresenterId
    executor_factory: Factory
    presenter_factory: Factory
    search_aliases: tuple[str, ...] = ()
    sample_id: str | None = None
    help_content: str = ""
    custom_input_factory: Factory | None = None
    custom_parameter_factory: Factory | None = None
    custom_presenter_factory: Factory | None = None

    def __post_init__(self) -> None:
        if self.id.module_id is not self.module_id:
            raise InputValidationError("Operation ID does not match its module.")
        if not self.display_name.strip() or not self.short_description.strip():
            raise InputValidationError("Operation name and description are required.")
        if not callable(self.executor_factory) or not callable(self.presenter_factory):
            raise InputValidationError("Operation factories must be callable.")
        inputs = [item.key for item in self.input_spec]
        parameters = [item.key for item in self.parameter_schema]
        if len(inputs) != len(set(inputs)) or len(parameters) != len(set(parameters)):
            raise InputValidationError("Operation contract keys must be unique.")
        for input_item in self.input_spec:
            if input_item.same_dimensions_as is not None and (
                input_item.same_dimensions_as not in inputs
                or input_item.same_dimensions_as == input_item.key
            ):
                raise InputValidationError("Input dimension reference is invalid.")
        for parameter_item in self.parameter_schema:
            for condition in (parameter_item.visible_when, parameter_item.enabled_when):
                if condition is not None and condition.parameter_key not in parameters:
                    raise InputValidationError("Parameter condition reference is invalid.")
        aliases = [alias.strip().casefold() for alias in self.search_aliases]
        if any(not alias for alias in aliases) or len(aliases) != len(set(aliases)):
            raise InputValidationError("Search aliases must be unique and non-empty.")
        if self.sample_id is not None and not self.sample_id.strip():
            raise InputValidationError("Sample ID cannot be empty.")
