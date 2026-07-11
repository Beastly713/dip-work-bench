"""Tests for the typed application-error hierarchy."""

import pytest

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


def test_required_errors_derive_from_application_base() -> None:
    error_types = (
        ValidationError,
        InputValidationError,
        ParameterValidationError,
        UnsupportedImageError,
        OperationExecutionError,
        ExportError,
        CancelledOperation,
    )
    assert all(issubclass(error_type, DIPWorkbenchError) for error_type in error_types)
    assert issubclass(InputValidationError, ValidationError)
    assert issubclass(ParameterValidationError, ValidationError)


@pytest.mark.parametrize(
    "error_type",
    [
        DIPWorkbenchError,
        ValidationError,
        InputValidationError,
        ParameterValidationError,
        UnsupportedImageError,
        OperationExecutionError,
        ExportError,
        CancelledOperation,
    ],
)
def test_error_message_is_preserved(error_type: type[DIPWorkbenchError]) -> None:
    assert str(error_type("useful message")) == "useful message"


def test_cancelled_operation_is_catchable() -> None:
    with pytest.raises(DIPWorkbenchError, match="cancelled"):
        raise CancelledOperation("cancelled")
