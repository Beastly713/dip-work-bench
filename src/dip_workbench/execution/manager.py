"""Debounced latest-wins threaded operation execution manager."""

import uuid
from collections.abc import Mapping

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal

from dip_workbench.core import InputValidationError
from dip_workbench.execution.cancellation import CancellationToken
from dip_workbench.execution.contracts import ExecutionMode, OperationRequest
from dip_workbench.execution.preview import PreviewInputReducer, PreviewResolutionPolicy
from dip_workbench.execution.worker import OperationWorker
from dip_workbench.operations import OperationDefinition, validate_parameter_values


class OperationExecutionManager(QObject):
    preview_succeeded = Signal(object)
    apply_succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal(object)
    progress = Signal(object)
    stale_discarded = Signal(object)
    busy_changed = Signal(bool)

    def __init__(
        self,
        *,
        thread_pool: QThreadPool | None = None,
        preview_debounce_ms: int = 200,
        preview_policy: PreviewResolutionPolicy | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        if (
            isinstance(preview_debounce_ms, bool)
            or not isinstance(preview_debounce_ms, int)
            or preview_debounce_ms < 0
        ):
            raise InputValidationError("Preview debounce cannot be negative.")
        self.thread_pool = thread_pool or QThreadPool(self)
        self._owned = thread_pool is None
        self.preview_debounce_ms = preview_debounce_ms
        self.reducer = PreviewInputReducer(preview_policy or PreviewResolutionPolicy())
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._submit_pending)
        self._generation = 0
        self._pending: OperationRequest | None = None
        self._active: dict[str, OperationRequest] = {}
        self._workers: dict[str, OperationWorker] = {}
        self._latest_preview_generation = 0
        self._latest_apply_id: str | None = None
        self._busy = False
        self._shutdown = False

    def request_preview(
        self,
        definition: OperationDefinition,
        *,
        inputs: Mapping[str, object],
        parameters: Mapping[str, object] | None = None,
        interaction_data: Mapping[str, object] | None = None,
        document_metadata: Mapping[str, object] | None = None,
        debounce_ms: int | None = None,
    ) -> OperationRequest:
        request = self._request(
            definition,
            ExecutionMode.PREVIEW,
            inputs,
            parameters,
            interaction_data,
            document_metadata,
        )
        self.cancel_preview()
        self._latest_preview_generation = request.generation
        self._pending = request
        delay = self.preview_debounce_ms if debounce_ms is None else debounce_ms
        if isinstance(delay, bool) or not isinstance(delay, int) or delay < 0:
            raise InputValidationError("Preview debounce cannot be negative.")
        self._set_busy()
        self._submit_pending() if delay == 0 else self._timer.start(delay)
        return request

    def request_apply(
        self,
        definition: OperationDefinition,
        *,
        inputs: Mapping[str, object],
        parameters: Mapping[str, object] | None = None,
        interaction_data: Mapping[str, object] | None = None,
        document_metadata: Mapping[str, object] | None = None,
    ) -> OperationRequest:
        self.cancel_preview()
        self.cancel_apply()
        request = self._request(
            definition, ExecutionMode.APPLY, inputs, parameters, interaction_data, document_metadata
        )
        self._latest_apply_id = request.request_id
        self._submit(request)
        return request

    def _request(
        self,
        definition: OperationDefinition,
        mode: ExecutionMode,
        inputs: Mapping[str, object],
        parameters: Mapping[str, object] | None,
        interaction_data: Mapping[str, object] | None,
        document_metadata: Mapping[str, object] | None,
    ) -> OperationRequest:
        if not isinstance(definition, OperationDefinition) or not isinstance(inputs, Mapping):
            raise InputValidationError(
                "Execution requires an operation definition and input mapping."
            )
        self._generation += 1
        resolved = validate_parameter_values(definition.parameter_schema, parameters or {})
        return OperationRequest(
            str(uuid.uuid4()),
            definition,
            mode,
            self._generation,
            inputs,
            resolved,
            interaction_data or {},
            document_metadata or {},
            CancellationToken(),
        )

    def _submit_pending(self) -> None:
        if self._pending is not None:
            request = self._pending
            self._pending = None
            self._submit(request)
        else:
            self._set_busy()

    def _submit(self, request: OperationRequest) -> None:
        worker = OperationWorker(request, self.reducer)
        self._active[request.request_id] = request
        self._workers[request.request_id] = worker
        worker.signals.progress.connect(self._route)
        worker.signals.succeeded.connect(self._route)
        worker.signals.failed.connect(self._route)
        worker.signals.cancelled.connect(self._route)
        self.thread_pool.start(worker)
        self._set_busy()

    def _current(self, event: object) -> bool:
        request = event.request  # type: ignore[attr-defined]
        return (
            request.generation == self._latest_preview_generation
            if request.mode is ExecutionMode.PREVIEW
            else request.request_id == self._latest_apply_id
        )

    def _route(self, event: object) -> None:
        from dip_workbench.execution.contracts import (
            ExecutionCancelled,
            ExecutionFailure,
            ExecutionSuccess,
            ProgressUpdate,
        )

        request = event.request  # type: ignore[attr-defined]
        terminal = not isinstance(event, ProgressUpdate)
        if terminal:
            self._active.pop(request.request_id, None)
            self._workers.pop(request.request_id, None)
        if not self._current(event):
            self.stale_discarded.emit(event)
        elif isinstance(event, ProgressUpdate):
            self.progress.emit(event)
        elif isinstance(event, ExecutionSuccess):
            (
                self.preview_succeeded
                if request.mode is ExecutionMode.PREVIEW
                else self.apply_succeeded
            ).emit(event)
        elif isinstance(event, ExecutionFailure):
            self.failed.emit(event)
        elif isinstance(event, ExecutionCancelled):
            self.cancelled.emit(event)
        self._set_busy()

    def cancel_preview(self) -> None:
        self._timer.stop()
        if self._pending is not None:
            self._pending.cancellation_token.cancel()
            self._pending = None
        for request in self._active.values():
            if request.mode is ExecutionMode.PREVIEW:
                request.cancellation_token.cancel()
        self._set_busy()

    def cancel_apply(self) -> None:
        for request in self._active.values():
            if request.mode is ExecutionMode.APPLY:
                request.cancellation_token.cancel()

    def cancel_all(self) -> None:
        self.cancel_preview()
        self.cancel_apply()

    def _set_busy(self) -> None:
        value = self._pending is not None or bool(self._active)
        if value != self._busy:
            self._busy = value
            self.busy_changed.emit(value)

    def wait_for_done(self, timeout_ms: int = -1) -> bool:
        return self.thread_pool.waitForDone(timeout_ms)

    def shutdown(self, timeout_ms: int = 5000) -> bool:
        if self._shutdown:
            return self.wait_for_done(timeout_ms)
        self._shutdown = True
        self._timer.stop()
        self.cancel_all()
        if hasattr(self.thread_pool, "clear"):
            self.thread_pool.clear()
        return self.wait_for_done(timeout_ms)
