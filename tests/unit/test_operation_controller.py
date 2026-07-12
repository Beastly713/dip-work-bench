"""Tests for generic academic-operation coordination."""

import uuid

import numpy as np
from PySide6.QtCore import QObject, Signal

from dip_workbench.controllers import (
    DocumentController,
    InputSource,
    OperationController,
    OperationWorkspaceState,
)
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import (
    CancellationToken,
    ExecutionMode,
    ExecutionSuccess,
    OperationRequest,
)
from dip_workbench.operations import (
    ApplyPolicy,
    ImageArtifact,
    InputSpec,
    ModuleId,
    OperationDefinition,
    OperationId,
    OperationResult,
    ParameterSpec,
    ParameterType,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.services import ImageIOService, ImageTransformService
from dip_workbench.state import DocumentStore, HistorySnapshotStore


class FakeManager(QObject):
    preview_succeeded = Signal(object)
    apply_succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal(object)
    progress = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.request: OperationRequest | None = None
        self.generation = 0
        self.debounce_ms: int | None = -1

    def _request(self, definition, mode, inputs, parameters, document_metadata):
        self.generation += 1
        self.request = OperationRequest(
            str(uuid.uuid4()),
            definition,
            mode,
            self.generation,
            inputs,
            parameters or {},
            {},
            document_metadata or {},
            CancellationToken(),
        )
        return self.request

    def request_preview(
        self,
        definition,
        *,
        inputs,
        parameters=None,
        interaction_data=None,
        document_metadata=None,
        debounce_ms=None,
    ):
        self.debounce_ms = debounce_ms
        return self._request(
            definition, ExecutionMode.PREVIEW, inputs, parameters, document_metadata
        )

    def request_apply(
        self, definition, *, inputs, parameters=None, interaction_data=None, document_metadata=None
    ):
        return self._request(definition, ExecutionMode.APPLY, inputs, parameters, document_metadata)

    def cancel_all(self) -> None:
        pass


def definition(
    *,
    allow_original=True,
    apply_policy=ApplyPolicy.PRIMARY_ARTIFACT,
    preview_policy=PreviewPolicy.IMMEDIATE,
) -> OperationDefinition:
    return OperationDefinition(
        OperationId("M03-01"),
        ModuleId.M03,
        "Synthetic",
        "Test the generic workspace.",
        (InputSpec("image", "Image", allow_original=allow_original),),
        (ParameterSpec("amount", "Amount", ParameterType.INTEGER, 2, minimum=1),),
        preview_policy,
        apply_policy,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        lambda: object(),
        lambda: object(),
    )


def controller(tmp_path, *, with_image=True):
    io = ImageIOService()
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "history").mkdir()
    store = DocumentStore(HistorySnapshotStore(tmp_path / "history", io))
    document = DocumentController(io, ImageTransformService(), store)
    if with_image:
        store.set_primary_image(
            ImageAsset(
                name="source", data=np.zeros((4, 5), dtype=np.uint8), colour_model=ColourModel.GRAY
            )
        )
    manager = FakeManager()
    return OperationController(document, manager), manager, store


def test_defaults_source_state_and_missing_input(tmp_path) -> None:
    item, _, _ = controller(tmp_path)
    item.select_operation(definition())
    assert item.input_source is InputSource.ORIGINAL
    assert item.parameter_values["amount"] == 2
    assert item.workspace_state is OperationWorkspaceState.READY
    missing, manager, _ = controller(tmp_path / "missing", with_image=False)
    missing.select_operation(definition())
    missing.preview_or_run()
    assert missing.workspace_state is OperationWorkspaceState.MISSING_INPUT
    assert manager.request is None


def test_parameter_state_switch_reset_and_validation(tmp_path) -> None:
    item, _, _ = controller(tmp_path)
    first = definition()
    second = OperationDefinition(
        OperationId("M03-02"),
        ModuleId.M03,
        "Other",
        "Other synthetic operation.",
        first.input_spec,
        first.parameter_schema,
        first.preview_policy,
        first.apply_policy,
        first.presenter_id,
        lambda: object(),
        lambda: object(),
    )
    item.select_operation(first)
    item.set_parameter_value("amount", 4)
    item.select_operation(second)
    item.select_operation(first)
    assert item.parameter_values["amount"] == 4
    item.set_parameter_value("amount", 0)
    assert item.parameter_errors
    item.reset_parameters()
    assert item.parameter_values["amount"] == 2


def test_preview_is_non_destructive_and_apply_adds_one_history(tmp_path) -> None:
    item, manager, store = controller(tmp_path)
    item.select_operation(definition())
    current = store.current_image
    item.preview_or_run()
    request = manager.request
    assert request is not None
    result = OperationResult(
        ImageArtifact(
            "image",
            "Result",
            ImageAsset(
                name="result", data=np.ones((4, 5), dtype=np.uint8), colour_model=ColourModel.GRAY
            ),
        )
    )
    manager.preview_succeeded.emit(ExecutionSuccess(request, result, 1))
    assert item.active_result is result
    assert store.current_image is current
    assert not store.history
    assert store.active_preview is not None
    item.apply()
    apply_request = manager.request
    assert apply_request is not None
    manager.apply_succeeded.emit(ExecutionSuccess(apply_request, result, 2))
    assert len(store.history) == 1
    assert not item.can_apply


def test_apply_none_and_document_change(tmp_path) -> None:
    item, _, store = controller(tmp_path)
    item.select_operation(definition(apply_policy=ApplyPolicy.NONE))
    item.apply()
    assert item.workspace_state is OperationWorkspaceState.FAILURE
    current = store.current_image
    item.document_changed()
    assert store.current_image is current


def test_policy_driven_parameter_preview(tmp_path) -> None:
    immediate, immediate_manager, _ = controller(tmp_path / "immediate")
    immediate.select_operation(definition())
    immediate.parameter_values_changed({"amount": 3})
    assert immediate_manager.request is not None and immediate_manager.debounce_ms == 0

    debounced, debounced_manager, _ = controller(tmp_path / "debounced")
    debounced.select_operation(definition(preview_policy=PreviewPolicy.DEBOUNCED))
    debounced.parameter_values_changed({"amount": 3})
    assert debounced_manager.request is not None and debounced_manager.debounce_ms is None

    explicit, explicit_manager, _ = controller(tmp_path / "explicit")
    explicit.select_operation(definition(preview_policy=PreviewPolicy.EXPLICIT))
    explicit.parameter_values_changed({"amount": 3})
    assert explicit_manager.request is None


def test_single_input_contract_and_source_validation(tmp_path) -> None:
    item, _, _ = controller(tmp_path)

    def with_input(spec: InputSpec, value: str) -> OperationDefinition:
        return OperationDefinition(
            OperationId(value),
            ModuleId.M03,
            "Single Input",
            "Validate single image input.",
            (spec,),
            (),
            PreviewPolicy.EXPLICIT,
            ApplyPolicy.NONE,
            PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
            lambda: object(),
            lambda: object(),
        )

    item.select_operation(with_input(InputSpec("image", "Image"), "M03-02"))
    assert not item.input_errors

    current_only = with_input(
        InputSpec("image", "Image", allow_original=False, allow_current=True),
        "M03-03",
    )
    item.select_operation(current_only)
    assert item.input_source is InputSource.CURRENT
    assert not item.input_errors

    rgb_only = with_input(
        InputSpec("image", "Image", accepted_colour_models=frozenset({ColourModel.RGB})),
        "M03-04",
    )
    item.select_operation(rgb_only)
    assert "image" in item.input_errors
