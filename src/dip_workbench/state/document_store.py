"""Non-GUI state for one active image document."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.state.history_snapshot_store import HistorySnapshotStore
from dip_workbench.state.models import ActivePreview, AuxiliaryInput, HistoryEntry


class DocumentStore:
    """Own original/current images, previews, auxiliary state, and undo history."""

    DEFAULT_HISTORY_LIMIT = 25
    _DOCUMENT_MODELS: ClassVar[frozenset[ColourModel]] = frozenset(
        {ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY}
    )

    def __init__(
        self,
        snapshot_store: HistorySnapshotStore,
        *,
        history_limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> None:
        if (
            isinstance(history_limit, bool)
            or not isinstance(history_limit, int)
            or history_limit <= 0
        ):
            raise InputValidationError("History limit must be a positive integer.")
        self._snapshot_store = snapshot_store
        self._history_limit = history_limit
        self._original_image: ImageAsset | None = None
        self._current_image: ImageAsset | None = None
        self._active_preview: ActivePreview | None = None
        self._history: list[HistoryEntry] = []
        self._redo_history: list[HistoryEntry] = []
        self._auxiliary_inputs: dict[str, AuxiliaryInput] = {}
        self._operation_states: dict[str, Mapping[str, object]] = {}
        self._closed = False

    @property
    def original_image(self) -> ImageAsset | None:
        return self._original_image

    @property
    def current_image(self) -> ImageAsset | None:
        return self._current_image

    @property
    def active_preview(self) -> ActivePreview | None:
        return self._active_preview

    @property
    def history(self) -> tuple[HistoryEntry, ...]:
        return tuple(self._history)

    @property
    def redo_history(self) -> tuple[HistoryEntry, ...]:
        return tuple(self._redo_history)

    @property
    def auxiliary_inputs(self) -> Mapping[str, AuxiliaryInput]:
        return MappingProxyType(dict(self._auxiliary_inputs))

    @property
    def operation_states(self) -> Mapping[str, Mapping[str, object]]:
        return MappingProxyType(dict(self._operation_states))

    @property
    def has_document(self) -> bool:
        return self._original_image is not None

    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo_history)

    def set_primary_image(self, asset: ImageAsset) -> None:
        self._validate_document_asset(asset)
        self.clear_document()
        self._original_image = asset
        self._current_image = self._copy_asset(asset)

    def clear_document(self) -> None:
        self._snapshot_store.clear()
        self._original_image = None
        self._current_image = None
        self._active_preview = None
        self._history.clear()
        self._redo_history.clear()
        self._auxiliary_inputs.clear()
        self._operation_states.clear()

    def set_active_preview(self, preview: ActivePreview) -> None:
        self._require_document()
        if not isinstance(preview, ActivePreview):
            raise InputValidationError("A valid active preview is required.")
        self._active_preview = preview

    def clear_active_preview(self) -> None:
        self._active_preview = None

    def set_auxiliary_input(self, role: str, value: AuxiliaryInput) -> None:
        self._validate_key(role, "Auxiliary role")
        if not isinstance(value, ImageAsset) and not (
            isinstance(value, tuple)
            and bool(value)
            and all(isinstance(item, ImageAsset) for item in value)
        ):
            raise InputValidationError("Auxiliary input must contain one or more image assets.")
        self._auxiliary_inputs[role] = value

    def get_auxiliary_input(self, role: str) -> AuxiliaryInput | None:
        self._validate_key(role, "Auxiliary role")
        return self._auxiliary_inputs.get(role)

    def remove_auxiliary_input(self, role: str) -> None:
        self._validate_key(role, "Auxiliary role")
        self._auxiliary_inputs.pop(role, None)

    def clear_auxiliary_inputs(self) -> None:
        self._auxiliary_inputs.clear()

    def set_operation_state(self, operation_id: str, state: Mapping[str, object]) -> None:
        self._validate_key(operation_id, "Operation id")
        try:
            copied = MappingProxyType(dict(state))
        except (TypeError, ValueError) as error:
            raise InputValidationError("Operation state must be a mapping.") from error
        self._operation_states[operation_id] = copied

    def get_operation_state(self, operation_id: str) -> Mapping[str, object] | None:
        self._validate_key(operation_id, "Operation id")
        return self._operation_states.get(operation_id)

    def clear_operation_state(self, operation_id: str) -> None:
        self._validate_key(operation_id, "Operation id")
        self._operation_states.pop(operation_id, None)

    def clear_all_operation_states(self) -> None:
        self._operation_states.clear()

    def apply_image(
        self,
        asset: ImageAsset,
        *,
        operation_id: str,
        operation_name: str,
        parameters: Mapping[str, object] | None = None,
        input_source: str = "Current Result",
        metadata: Mapping[str, object] | None = None,
    ) -> ImageAsset:
        self._require_document()
        self._validate_document_asset(asset)
        for value, label in (
            (operation_id, "Operation id"),
            (operation_name, "Operation name"),
            (input_source, "Input source"),
        ):
            self._validate_key(value, label)
        try:
            safe_parameters = dict(parameters or {})
            safe_metadata = dict(metadata or {})
        except (TypeError, ValueError) as error:
            raise InputValidationError("Applied action metadata must be mappings.") from error
        entry = self._snapshot_store.create_entry(
            asset,
            operation_id=operation_id,
            operation_name=operation_name,
            parameters=safe_parameters,
            input_source=input_source,
            metadata=safe_metadata,
        )
        self._current_image = asset
        self._history.append(entry)
        self._active_preview = None
        for redo_entry in self._redo_history:
            self._snapshot_store.delete(redo_entry)
        self._redo_history.clear()
        while len(self._history) > self._history_limit:
            self._snapshot_store.delete(self._history.pop(0))
        return asset

    def undo(self) -> ImageAsset:
        self._require_document()
        if not self._history:
            raise InputValidationError("No applied image state is available to undo.")
        self._redo_history.append(self._history.pop())
        if self._history:
            restored = self._snapshot_store.restore(self._history[-1])
        else:
            assert self._original_image is not None
            restored = self._copy_asset(self._original_image)
        self._current_image = restored
        self._active_preview = None
        return restored

    def redo(self) -> ImageAsset:
        self._require_document()
        if not self._redo_history:
            raise InputValidationError("No image state is available to redo.")
        entry = self._redo_history.pop()
        restored = self._snapshot_store.restore(entry)
        self._history.append(entry)
        self._current_image = restored
        self._active_preview = None
        return restored

    def reset_to_original(self) -> ImageAsset:
        self._require_document()
        assert self._original_image is not None
        return self.apply_image(
            self._copy_asset(self._original_image),
            operation_id="U-11",
            operation_name="Reset to Original",
            input_source="Original",
        )

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.clear_document()
        self._snapshot_store.close()

    def _require_document(self) -> None:
        if not self.has_document:
            raise InputValidationError("No primary image document is active.")

    def _validate_document_asset(self, asset: object) -> None:
        if not isinstance(asset, ImageAsset) or asset.colour_model not in self._DOCUMENT_MODELS:
            raise InputValidationError("Current images must be RGB, grayscale, or binary assets.")

    @staticmethod
    def _validate_key(value: object, label: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise InputValidationError(f"{label} must be a non-empty string.")

    @staticmethod
    def _copy_asset(asset: ImageAsset) -> ImageAsset:
        return ImageAsset(
            name=asset.name,
            data=asset.data,
            colour_model=asset.colour_model,
            source_path=asset.source_path,
            metadata=asset.metadata,
        )
