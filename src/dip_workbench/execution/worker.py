"""Thread-pool operation worker."""

import logging
import time

from PySide6.QtCore import QObject, QRunnable, Signal

from dip_workbench.core import CancelledOperation, DIPWorkbenchError, OperationExecutionError
from dip_workbench.execution.contracts import (
    ExecutionCancelled,
    ExecutionFailure,
    ExecutionMode,
    ExecutionSuccess,
    OperationContext,
    OperationRequest,
    ProgressUpdate,
)
from dip_workbench.execution.preview import PreviewInputReducer
from dip_workbench.operations import OperationResult


class OperationWorkerSignals(QObject):
    progress = Signal(object)
    succeeded = Signal(object)
    failed = Signal(object)
    cancelled = Signal(object)


class OperationWorker(QRunnable):
    def __init__(self, request: OperationRequest, reducer: PreviewInputReducer) -> None:
        super().__init__()
        self.request = request
        self.reducer = reducer
        self.signals = OperationWorkerSignals()

    def run(self) -> None:
        started = time.perf_counter()
        try:
            self.request.cancellation_token.raise_if_cancelled()
            executor = self.request.definition.executor_factory()
            execute = getattr(executor, "execute", None)
            if not callable(execute):
                raise OperationExecutionError("The operation executor is invalid.")
            inputs = (
                self.reducer.reduce_inputs(self.request.inputs)
                if self.request.mode is ExecutionMode.PREVIEW
                else self.request.inputs
            )
            context = OperationContext(
                inputs,
                self.request.parameters,
                self.request.interaction_data,
                self.request.document_metadata,
                self.request.cancellation_token,
                lambda percent, message: self.signals.progress.emit(
                    ProgressUpdate(self.request, percent, message)
                ),
            )
            result = execute(context)
            if not isinstance(result, OperationResult):
                raise OperationExecutionError("The operation returned an invalid result.")
            self.request.cancellation_token.raise_if_cancelled()
            elapsed = (time.perf_counter() - started) * 1000
            self.signals.succeeded.emit(ExecutionSuccess(self.request, result, elapsed))
        except CancelledOperation:
            self.signals.cancelled.emit(ExecutionCancelled(self.request))
        except DIPWorkbenchError as error:
            self.signals.failed.emit(ExecutionFailure(self.request, error))
        except Exception:
            logging.getLogger("dip_workbench").exception("Unexpected operation execution failure")
            self.signals.failed.emit(
                ExecutionFailure(
                    self.request, OperationExecutionError("The operation could not be completed.")
                )
            )
