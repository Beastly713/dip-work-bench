"""Immutable document-state records."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from uuid import uuid4

from dip_workbench.core import ColourModel, InputValidationError


def _mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    try:
        return MappingProxyType(dict(value))
    except (TypeError, ValueError) as error:
        raise InputValidationError("State metadata must be a mapping.") from error


def _required(value: object, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise InputValidationError(f"{label} must be a non-empty string.")


@dataclass(frozen=True, slots=True)
class ActivePreview:
    operation_id: str
    input_asset_ids: tuple[str, ...]
    parameters: Mapping[str, object]
    interaction_data: Mapping[str, object]
    result: object
    request_generation: int

    def __post_init__(self) -> None:
        _required(self.operation_id, "Operation id")
        if any(not isinstance(item, str) or not item.strip() for item in self.input_asset_ids):
            raise InputValidationError("Preview input asset ids must be non-empty strings.")
        if (
            isinstance(self.request_generation, bool)
            or not isinstance(self.request_generation, int)
            or self.request_generation < 0
        ):
            raise InputValidationError("Preview request generation must be a non-negative integer.")
        object.__setattr__(self, "parameters", _mapping(self.parameters))
        object.__setattr__(self, "interaction_data", _mapping(self.interaction_data))


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    operation_id: str
    operation_name: str
    input_source: str
    snapshot_path: Path
    asset_id: str
    asset_name: str
    colour_model: ColourModel
    parameters: Mapping[str, object] = field(default_factory=dict)
    source_path: Path | None = None
    asset_metadata: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        for value, label in (
            (self.id, "History id"),
            (self.operation_id, "Operation id"),
            (self.operation_name, "Operation name"),
            (self.input_source, "Input source"),
            (self.asset_id, "Asset id"),
            (self.asset_name, "Asset name"),
        ):
            _required(value, label)
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() != UTC.utcoffset(None):
            raise InputValidationError("History timestamp must be timezone-aware UTC.")
        if not isinstance(self.colour_model, ColourModel):
            raise InputValidationError("History colour model is invalid.")
        object.__setattr__(self, "snapshot_path", Path(self.snapshot_path))
        if self.source_path is not None:
            object.__setattr__(self, "source_path", Path(self.source_path))
        object.__setattr__(self, "parameters", _mapping(self.parameters))
        object.__setattr__(self, "asset_metadata", _mapping(self.asset_metadata))
        object.__setattr__(self, "metadata", _mapping(self.metadata))
