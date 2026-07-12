"""Coordination for the generic academic-operation workspace."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType

from PySide6.QtCore import QObject, Signal

from dip_workbench.controllers.document_controller import DocumentController
from dip_workbench.core import ImageAsset, InputValidationError, ParameterValidationError
from dip_workbench.execution import (
    ExecutionCancelled,
    ExecutionFailure,
    ExecutionSuccess,
    OperationExecutionManager,
    OperationRequest,
    ProgressUpdate,
)
from dip_workbench.operations import (
    ApplyPolicy,
    OperationDefinition,
    OperationResult,
    PreviewPolicy,
)


class InputSource(StrEnum):
    ORIGINAL = "Original"
    CURRENT = "Current Result"


class OperationWorkspaceState(StrEnum):
    NO_OPERATION = "no_operation"
    MISSING_INPUT = "missing_input"
    READY = "ready"
    PROCESSING = "processing"
    RESULT = "result"
    FAILURE = "failure"


class OperationController(QObject):
    changed = Signal()
    image_applied = Signal(object)

    def __init__(
        self,
        document_controller: DocumentController,
        execution_manager: OperationExecutionManager,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.document_controller = document_controller
        self.execution_manager = execution_manager
        self._active_definition: OperationDefinition | None = None
        self._workspace_state = OperationWorkspaceState.NO_OPERATION
        self._input_source = InputSource.ORIGINAL
        self._parameter_values: dict[str, object] = {}
        self._input_errors: dict[str, str] = {}
        self._parameter_errors: dict[str, str] = {}
        self._active_result: OperationResult | None = None
        self._progress_percent = 0.0
        self._progress_message = ""
        self._failure_message = ""
        self._selected_apply_candidate: str | None = None
        self._preview_request: OperationRequest | None = None
        self._apply_request: OperationRequest | None = None
        self._preview_signature: tuple[object, ...] | None = None
        self._applied = False
        execution_manager.preview_succeeded.connect(self._preview_succeeded)
        execution_manager.apply_succeeded.connect(self._apply_succeeded)
        execution_manager.progress.connect(self._progress)
        execution_manager.failed.connect(self._failed)
        execution_manager.cancelled.connect(self._cancelled)

    @property
    def active_definition(self) -> OperationDefinition | None:
        return self._active_definition

    @property
    def workspace_state(self) -> OperationWorkspaceState:
        return self._workspace_state

    @property
    def input_source(self) -> InputSource:
        return self._input_source

    @property
    def parameter_values(self) -> Mapping[str, object]:
        return MappingProxyType(dict(self._parameter_values))

    @property
    def input_errors(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self._input_errors))

    @property
    def parameter_errors(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self._parameter_errors))

    @property
    def active_result(self) -> OperationResult | None:
        return self._active_result

    @property
    def progress_percent(self) -> float:
        return self._progress_percent

    @property
    def progress_message(self) -> str:
        return self._progress_message

    @property
    def failure_message(self) -> str:
        return self._failure_message

    @property
    def selected_apply_candidate(self) -> str | None:
        return self._selected_apply_candidate

    @property
    def can_preview(self) -> bool:
        return (
            self._active_definition is not None
            and not self._input_errors
            and not self._parameter_errors
            and self._workspace_state is not OperationWorkspaceState.PROCESSING
        )

    @property
    def can_apply(self) -> bool:
        definition = self._active_definition
        if definition is None or self._active_result is None or self._applied:
            return False
        if definition.apply_policy is ApplyPolicy.NONE:
            return False
        if definition.apply_policy is ApplyPolicy.PRIMARY_ARTIFACT:
            return isinstance(self._active_result.primary_artifact.data, ImageAsset)
        return self._candidate_artifact() is not None

    @property
    def preview_action_label(self) -> str:
        definition = self._active_definition
        if definition is not None and definition.preview_policy in {
            PreviewPolicy.IMMEDIATE,
            PreviewPolicy.DEBOUNCED,
        }:
            return "Preview"
        return "Run"

    def select_operation(self, definition: OperationDefinition) -> None:
        if not isinstance(definition, OperationDefinition):
            raise InputValidationError("A valid operation definition is required.")
        self._cancel_work()
        self.document_controller.clear_active_preview()
        self._active_definition = definition
        saved = self.document_controller.document_store.get_operation_state(str(definition.id))
        defaults = {spec.key: spec.default for spec in definition.parameter_schema}
        parameters = saved.get("parameters") if saved is not None else None
        self._parameter_values = dict(parameters) if isinstance(parameters, Mapping) else defaults
        if set(self._parameter_values) != set(defaults):
            self._parameter_values = defaults
        else:
            try:
                for parameter_spec in definition.parameter_schema:
                    parameter_spec.validate(
                        self._parameter_values[parameter_spec.key], self._parameter_values
                    )
            except ParameterValidationError:
                self._parameter_values = defaults
        saved_source = saved.get("input_source") if saved is not None else None
        preferred = self._default_source()
        try:
            source = InputSource(saved_source) if isinstance(saved_source, str) else preferred
        except ValueError:
            source = preferred
        self._input_source = source if self._source_allowed(source) else preferred
        candidate = saved.get("selected_apply_candidate") if saved is not None else None
        self._selected_apply_candidate = candidate if isinstance(candidate, str) else None
        self._clear_result()
        self._validate()
        self._persist()
        self.changed.emit()

    def clear_operation(self) -> None:
        self._cancel_work()
        self.document_controller.clear_active_preview()
        self._active_definition = None
        self._parameter_values.clear()
        self._input_errors.clear()
        self._parameter_errors.clear()
        self._clear_result()
        self._workspace_state = OperationWorkspaceState.NO_OPERATION
        self.changed.emit()

    def set_input_source(self, source: InputSource) -> None:
        if not isinstance(source, InputSource) or not self._source_allowed(source):
            raise InputValidationError("The selected image source is not allowed.")
        if source is self._input_source:
            return
        self._input_source = source
        self._invalidate_result()

    def resolved_inputs(self) -> Mapping[str, object]:
        resolved: dict[str, object] = {}
        definition = self._active_definition
        if definition is not None:
            spec = definition.input_spec[0]
            image = (
                self.document_controller.original_image
                if self._input_source is InputSource.ORIGINAL
                else self.document_controller.current_image
            )
            if image is not None:
                resolved[spec.key] = image
        return MappingProxyType(resolved)

    def set_parameter_values(self, values: Mapping[str, object]) -> None:
        if not isinstance(values, Mapping):
            raise ParameterValidationError("Parameter values must be a mapping.")
        definition = self._require_definition()
        known = {spec.key for spec in definition.parameter_schema}
        unknown = set(values) - known
        if unknown:
            raise ParameterValidationError(f"Unknown parameters: {', '.join(sorted(unknown))}.")
        self._parameter_values.update(values)
        self._invalidate_result()

    def set_parameter_value(self, key: str, value: object) -> None:
        self.set_parameter_values({key: value})

    def parameter_values_changed(self, values: Mapping[str, object]) -> None:
        self.set_parameter_values(values)
        self._automatic_preview()

    def reset_parameters(self) -> None:
        definition = self._require_definition()
        self._parameter_values = {spec.key: spec.default for spec in definition.parameter_schema}
        self._invalidate_result()
        self._automatic_preview()

    def preview_or_run(self) -> None:
        self._submit_preview(0)

    def _submit_preview(self, debounce_ms: int | None) -> None:
        definition = self._require_definition()
        self._validate()
        if not self.can_preview:
            self.changed.emit()
            return
        inputs = self.resolved_inputs()
        metadata = self._document_metadata()
        self._workspace_state = OperationWorkspaceState.PROCESSING
        self._failure_message = ""
        self._progress_percent = 0.0
        self._progress_message = "Starting operation…"
        self._applied = False
        self._preview_request = self.execution_manager.request_preview(
            definition,
            inputs=inputs,
            parameters=self._parameter_values,
            document_metadata=metadata,
            debounce_ms=debounce_ms,
        )
        self._preview_signature = self._signature()
        self.changed.emit()

    def _automatic_preview(self) -> None:
        definition = self._active_definition
        if definition is None or not self.can_preview:
            return
        if definition.preview_policy is PreviewPolicy.IMMEDIATE:
            self._submit_preview(0)
        elif definition.preview_policy is PreviewPolicy.DEBOUNCED:
            self._submit_preview(None)

    def set_apply_candidate(self, artifact_key: str | None) -> None:
        if artifact_key is not None and (
            self._active_result is None
            or artifact_key
            not in {item.artifact_key for item in self._active_result.apply_candidates}
        ):
            raise InputValidationError("The selected apply candidate is unavailable.")
        self._selected_apply_candidate = artifact_key
        self._persist()
        self.changed.emit()

    def apply(self) -> None:
        definition = self._require_definition()
        if not self.can_apply or self._preview_signature != self._signature():
            self._failure_message = "Preview a valid result before applying it."
            self._workspace_state = OperationWorkspaceState.FAILURE
            self.changed.emit()
            return
        self._workspace_state = OperationWorkspaceState.PROCESSING
        self._progress_percent = 0.0
        self._progress_message = "Processing full-resolution result…"
        self._apply_request = self.execution_manager.request_apply(
            definition,
            inputs=self.resolved_inputs(),
            parameters=self._parameter_values,
            document_metadata=self._document_metadata(),
        )
        self.changed.emit()

    def cancel(self) -> None:
        self._cancel_work()
        self._workspace_state = (
            OperationWorkspaceState.RESULT
            if self._active_result is not None
            else self._ready_state()
        )
        self.changed.emit()

    def clear_result(self) -> None:
        self._cancel_work()
        self.document_controller.clear_active_preview()
        self._clear_result()
        self._validate()
        self.changed.emit()

    def document_changed(self) -> None:
        self._cancel_work()
        self.document_controller.clear_active_preview()
        self._clear_result()
        definition = self._active_definition
        if definition is not None:
            saved = self.document_controller.document_store.get_operation_state(str(definition.id))
            if saved is None:
                self._parameter_values = {
                    spec.key: spec.default for spec in definition.parameter_schema
                }
                self._input_source = self._default_source()
            self._selected_apply_candidate = None
            self._persist()
        self._validate()
        self.changed.emit()

    def _validate(self) -> None:
        self._input_errors = {}
        self._parameter_errors = {}
        definition = self._active_definition
        if definition is None:
            self._workspace_state = OperationWorkspaceState.NO_OPERATION
            return
        inputs = self.resolved_inputs()
        spec = definition.input_spec[0]
        value = inputs.get(spec.key)
        if not isinstance(value, ImageAsset):
            self._input_errors[spec.key] = f"{spec.label} is required."
        elif spec.accepted_colour_models and value.colour_model not in spec.accepted_colour_models:
            self._input_errors[spec.key] = f"{spec.label} has an unsupported colour model."
        for parameter_spec in definition.parameter_schema:
            try:
                parameter_spec.validate(
                    self._parameter_values.get(parameter_spec.key), self._parameter_values
                )
            except ParameterValidationError as error:
                self._parameter_errors[parameter_spec.key] = str(error)
        if self._workspace_state is not OperationWorkspaceState.PROCESSING:
            self._workspace_state = self._ready_state()

    def _ready_state(self) -> OperationWorkspaceState:
        return (
            OperationWorkspaceState.MISSING_INPUT
            if self._input_errors or self._parameter_errors
            else OperationWorkspaceState.READY
        )

    def _invalidate_result(self) -> None:
        self._cancel_work()
        self.document_controller.clear_active_preview()
        self._clear_result()
        self._validate()
        self._persist()
        self.changed.emit()

    def _clear_result(self) -> None:
        self._active_result = None
        self._preview_request = None
        self._apply_request = None
        self._preview_signature = None
        self._progress_percent = 0.0
        self._progress_message = ""
        self._failure_message = ""
        self._applied = False

    def _cancel_work(self) -> None:
        self.execution_manager.cancel_all()
        self._preview_request = None
        self._apply_request = None

    def _preview_succeeded(self, event: object) -> None:
        if not isinstance(event, ExecutionSuccess) or event.request is not self._preview_request:
            return
        if self._preview_signature != self._signature():
            return
        self._active_result = event.result
        self._workspace_state = OperationWorkspaceState.RESULT
        self._progress_percent = 100.0
        self._progress_message = "Complete"
        candidates = event.result.apply_candidates
        if len(candidates) == 1:
            self._selected_apply_candidate = candidates[0].artifact_key
        self.document_controller.set_operation_preview(
            operation_id=str(event.request.operation_id),
            input_asset_ids=self._input_asset_ids(event.request.inputs),
            parameters=event.request.parameters,
            interaction_data=event.request.interaction_data,
            result=event.result,
            request_generation=event.request.generation,
        )
        self._persist()
        self.changed.emit()

    def _apply_succeeded(self, event: object) -> None:
        if not isinstance(event, ExecutionSuccess) or event.request is not self._apply_request:
            return
        if self._preview_signature != self._signature() or not self._request_document_current(
            event.request
        ):
            self._failure_message = "The document changed before the result could be applied."
            self._workspace_state = OperationWorkspaceState.FAILURE
            self.changed.emit()
            return
        definition = self._require_definition()
        artifact = (
            event.result.primary_artifact
            if definition.apply_policy is ApplyPolicy.PRIMARY_ARTIFACT
            else event.result.get_artifact(self._selected_apply_candidate or "")
        )
        if not isinstance(artifact.data, ImageAsset):
            self._failure_message = "The selected result cannot be applied as an image."
            self._workspace_state = OperationWorkspaceState.FAILURE
            self.changed.emit()
            return
        asset = self.document_controller.apply_operation_image(
            artifact.data,
            operation_id=str(definition.id),
            operation_name=definition.display_name,
            parameters=self._parameter_values,
            input_source=self._input_source.value,
            metadata={
                "selected_artifact_key": artifact.key,
                "processing_time_ms": event.processing_time_ms,
            },
        )
        self._active_result = event.result
        self._workspace_state = OperationWorkspaceState.RESULT
        self._applied = True
        self._apply_request = None
        self.document_controller.clear_selected_region()
        self.image_applied.emit(asset)
        self.changed.emit()

    def _progress(self, event: object) -> None:
        if not isinstance(event, ProgressUpdate) or not self._is_active_request(event.request):
            return
        self._progress_percent = event.percent
        self._progress_message = event.message
        self.changed.emit()

    def _failed(self, event: object) -> None:
        if not isinstance(event, ExecutionFailure) or not self._is_active_request(event.request):
            return
        self._failure_message = str(event.error)
        self._workspace_state = OperationWorkspaceState.FAILURE
        self.changed.emit()

    def _cancelled(self, event: object) -> None:
        if not isinstance(event, ExecutionCancelled) or not self._is_active_request(event.request):
            return
        self._workspace_state = (
            OperationWorkspaceState.RESULT
            if self._active_result is not None
            else self._ready_state()
        )
        self.changed.emit()

    def _persist(self) -> None:
        if self._active_definition is None or not self.document_controller.has_document:
            return
        self.document_controller.document_store.set_operation_state(
            str(self._active_definition.id),
            {
                "parameters": dict(self._parameter_values),
                "input_source": self._input_source.value,
                "selected_apply_candidate": self._selected_apply_candidate,
            },
        )

    def _default_source(self) -> InputSource:
        definition = self._require_definition()
        primary = definition.input_spec[0]
        return InputSource.ORIGINAL if primary.allow_original else InputSource.CURRENT

    def _source_allowed(self, source: InputSource) -> bool:
        definition = self._active_definition
        if definition is None:
            return False
        primary = definition.input_spec[0]
        return primary.allow_original if source is InputSource.ORIGINAL else primary.allow_current

    def _require_definition(self) -> OperationDefinition:
        if self._active_definition is None:
            raise InputValidationError("No academic operation is selected.")
        return self._active_definition

    def _document_metadata(self) -> Mapping[str, object]:
        original = self.document_controller.original_image
        current = self.document_controller.current_image
        return {
            "original_asset_id": original.id if original is not None else None,
            "current_asset_id": current.id if current is not None else None,
            "selected_source": self._input_source.value,
        }

    def _signature(self) -> tuple[object, ...]:
        metadata = self._document_metadata()
        return (
            str(self._active_definition.id) if self._active_definition else None,
            tuple(sorted((key, repr(value)) for key, value in self._parameter_values.items())),
            metadata["original_asset_id"],
            metadata["current_asset_id"],
            self._input_source,
        )

    def _request_document_current(self, request: OperationRequest) -> bool:
        metadata = self._document_metadata()
        return (
            request.document_metadata.get("original_asset_id") == metadata["original_asset_id"]
            and request.document_metadata.get("current_asset_id") == metadata["current_asset_id"]
            and request.document_metadata.get("selected_source") == metadata["selected_source"]
        )

    @staticmethod
    def _input_asset_ids(inputs: Mapping[str, object]) -> tuple[str, ...]:
        ids: list[str] = []
        for value in inputs.values():
            values = value if isinstance(value, (tuple, list)) else (value,)
            ids.extend(item.id for item in values if isinstance(item, ImageAsset))
        return tuple(ids)

    def _candidate_artifact(self):  # type: ignore[no-untyped-def]
        if self._active_result is None or self._selected_apply_candidate is None:
            return None
        try:
            artifact = self._active_result.get_artifact(self._selected_apply_candidate)
        except InputValidationError:
            return None
        return artifact if isinstance(artifact.data, ImageAsset) else None

    def _is_active_request(self, request: OperationRequest) -> bool:
        return request is self._preview_request or request is self._apply_request
