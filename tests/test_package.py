"""Package-level smoke tests."""

import dip_workbench
from dip_workbench import application
from dip_workbench.core import (
    CancelledOperation,
    DIPWorkbenchError,
    ExportError,
    InputValidationError,
    OperationExecutionError,
    ParameterValidationError,
    UnsupportedImageError,
    ValidationError,
)


def test_package_public_surface() -> None:
    assert dip_workbench.__version__ == "0.1.0"
    assert callable(application.main)
    assert all(
        isinstance(error_type, type)
        for error_type in (
            DIPWorkbenchError,
            ValidationError,
            InputValidationError,
            ParameterValidationError,
            UnsupportedImageError,
            OperationExecutionError,
            ExportError,
            CancelledOperation,
        )
    )
