"""Typed application errors shared across DIP Workbench."""


class DIPWorkbenchError(Exception):
    """Base exception for expected DIP Workbench failures."""


class ValidationError(DIPWorkbenchError):
    """Base exception for invalid user-controlled values."""


class InputValidationError(ValidationError):
    """Raised when an operation input is invalid."""


class ParameterValidationError(ValidationError):
    """Raised when an operation parameter is invalid."""


class UnsupportedImageError(DIPWorkbenchError):
    """Raised when an image cannot be supported."""


class OperationExecutionError(DIPWorkbenchError):
    """Raised when an operation cannot complete."""


class ExportError(DIPWorkbenchError):
    """Raised when a result cannot be exported."""


class CancelledOperation(DIPWorkbenchError):
    """Raised when an operation is cancelled."""
