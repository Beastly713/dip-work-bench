import threading
import time

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset, OperationExecutionError
from dip_workbench.execution import OperationExecutionManager
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
    operation_registry,
)


class Executor:
    def __init__(self, seen: list[object], delay: float = 0, fail: bool = False) -> None:
        self.seen = seen
        self.delay = delay
        self.fail = fail

    def execute(self, context):  # type: ignore[no-untyped-def]
        self.seen.append((threading.get_ident(), context.inputs))
        context.report_progress(50, "half")
        if self.delay:
            time.sleep(self.delay)
        context.cancellation_token.raise_if_cancelled()
        if self.fail:
            raise RuntimeError("raw details")
        asset = next(value for value in context.inputs.values() if isinstance(value, ImageAsset))
        return OperationResult(ImageArtifact("image", "Image", asset))


def definition(factory) -> OperationDefinition:  # type: ignore[no-untyped-def]
    return OperationDefinition(
        OperationId("M01-01"),
        ModuleId.M01,
        "Demo",
        "Description",
        (InputSpec("image", "Image"),),
        (),
        PreviewPolicy.DEBOUNCED,
        ApplyPolicy.NONE,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        factory,
        lambda: object(),
    )


def image(width: int = 20) -> ImageAsset:
    return ImageAsset(
        name="x", data=np.zeros((10, width), dtype=np.uint8), colour_model=ColourModel.GRAY
    )


def test_threaded_preview_progress_debounce_and_reduction(qtbot) -> None:
    seen = []
    factory_calls = []
    item = definition(lambda: factory_calls.append(True) or Executor(seen))
    manager = OperationExecutionManager(preview_debounce_ms=20)
    progress = []
    manager.progress.connect(progress.append)
    with qtbot.waitSignal(manager.preview_succeeded, timeout=2000) as signal:
        manager.request_preview(item, inputs={"image": image(2000)}, debounce_ms=0)
    assert (
        factory_calls
        and seen[0][0] != threading.get_ident()
        and seen[0][1]["image"].width == 1024
        and progress
        and signal.args
    )
    assert manager.shutdown()


def test_latest_pending_preview_and_apply_full_resolution(qtbot) -> None:
    seen = []
    item = definition(lambda: Executor(seen))
    manager = OperationExecutionManager(preview_debounce_ms=50)
    first = manager.request_preview(item, inputs={"image": image(30)})
    second = manager.request_preview(item, inputs={"image": image(40)})
    assert first.cancellation_token.is_cancelled
    with qtbot.waitSignal(manager.preview_succeeded, timeout=2000) as signal:
        pass
    assert signal.args[0].request.request_id == second.request_id and len(seen) == 1
    with qtbot.waitSignal(manager.apply_succeeded, timeout=2000):
        manager.request_apply(item, inputs={"image": image(2000)})
    assert seen[-1][1]["image"].width == 2000 and manager.shutdown()


def test_cancel_and_failure_are_typed(qtbot) -> None:
    manager = OperationExecutionManager()
    slow = definition(lambda: Executor([], delay=0.05))
    with qtbot.waitSignal(manager.cancelled, timeout=2000):
        manager.request_preview(slow, inputs={"image": image()}, debounce_ms=0)
        manager.cancel_preview()
    failing = definition(lambda: Executor([], fail=True))
    with qtbot.waitSignal(manager.failed, timeout=2000) as signal:
        manager.request_apply(failing, inputs={"image": image()})
    assert isinstance(signal.args[0].error, OperationExecutionError) and "raw" not in str(
        signal.args[0].error
    )
    assert manager.shutdown() and tuple(str(item.id) for item in operation_registry.all()) == (
        "M01-01",
        "M01-02",
        "M01-03",
        "M02-02",
        "M03-01",
        "M03-03",
    )
