import uuid

import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.execution import (
    CancellationToken,
    ExecutionMode,
    ExecutionSuccess,
    OperationContext,
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
    PresenterId,
    PreviewPolicy,
)


def definition() -> OperationDefinition:
    return OperationDefinition(
        OperationId("M01-01"),
        ModuleId.M01,
        "Demo",
        "Description",
        (InputSpec("image", "Image"),),
        (),
        PreviewPolicy.NONE,
        ApplyPolicy.NONE,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        lambda: object(),
        lambda: object(),
    )


def request(generation: int = 1) -> OperationRequest:
    return OperationRequest(
        str(uuid.uuid4()),
        definition(),
        ExecutionMode.PREVIEW,
        generation,
        {"x": 1},
        {},
        {},
        {},
        CancellationToken(),
    )


def test_request_uuid_generation_and_immutability() -> None:
    item = request()
    assert uuid.UUID(item.request_id) and item.operation_id == OperationId("M01-01")
    with pytest.raises(TypeError):
        item.inputs["x"] = 2  # type: ignore[index]
    with pytest.raises(InputValidationError):
        request(0)


def test_context_freezes_nested_arrays_and_progress() -> None:
    array = np.ones((2, 2))
    updates = []
    context = OperationContext(
        {"nested": {"array": array}},
        {},
        {},
        {},
        CancellationToken(),
        lambda p, m: updates.append((p, m)),
    )
    array.fill(9)
    stored = context.inputs["nested"]["array"]  # type: ignore[index]
    assert not stored.flags.writeable and stored[0, 0] == 1  # type: ignore[union-attr]
    context.report_progress(0)
    context.report_progress(100, "done")
    assert updates[-1] == (100.0, "done")
    with pytest.raises(InputValidationError):
        context.report_progress(101)


def test_success_processing_time() -> None:
    asset = ImageAsset(
        name="x", data=np.zeros((1, 1), dtype=np.uint8), colour_model=ColourModel.GRAY
    )
    result = OperationResult(ImageArtifact("image", "Image", asset))
    ExecutionSuccess(request(), result, 0)
    with pytest.raises(InputValidationError):
        ExecutionSuccess(request(), result, -1)
