"""Tests for immutable document-state models."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from dip_workbench.core import ColourModel, InputValidationError
from dip_workbench.state import ActivePreview, HistoryEntry


def test_active_preview_validates_and_copies_mappings() -> None:
    parameters: dict[str, object] = {"level": 2}
    interaction: dict[str, object] = {"seed": (1, 2)}
    preview = ActivePreview("M01", ("asset",), parameters, interaction, object(), 0)
    parameters["level"] = 3
    interaction.clear()
    assert preview.parameters["level"] == 2
    assert preview.interaction_data["seed"] == (1, 2)
    with pytest.raises(TypeError):
        preview.parameters["x"] = 1  # type: ignore[index]


@pytest.mark.parametrize(
    "values",
    [
        ("", ("asset",), 0),
        ("M01", ("",), 0),
        ("M01", ("asset",), -1),
        ("M01", ("asset",), True),
    ],
)
def test_invalid_preview_fields(values: tuple[str, tuple[str, ...], object]) -> None:
    with pytest.raises(InputValidationError):
        ActivePreview(values[0], values[1], {}, {}, None, values[2])  # type: ignore[arg-type]


def test_history_entry_is_utc_and_mappings_are_immutable(tmp_path: Path) -> None:
    entry = HistoryEntry(
        operation_id="M01",
        operation_name="Demo",
        input_source="Current Result",
        snapshot_path=tmp_path / "state.png",
        asset_id="asset",
        asset_name="image",
        colour_model=ColourModel.RGB,
        timestamp=datetime.now(UTC),
        parameters={"value": 1},
    )
    assert entry.timestamp.tzinfo is UTC
    assert entry.id
    with pytest.raises(TypeError):
        entry.parameters["value"] = 2  # type: ignore[index]


@pytest.mark.parametrize(
    "field", ["operation_id", "operation_name", "input_source", "asset_id", "asset_name"]
)
def test_history_required_fields(field: str, tmp_path: Path) -> None:
    values = {
        "operation_id": "M01",
        "operation_name": "Demo",
        "input_source": "Current Result",
        "asset_id": "asset",
        "asset_name": "image",
    }
    values[field] = ""
    with pytest.raises(InputValidationError):
        HistoryEntry(snapshot_path=tmp_path / "x.png", colour_model=ColourModel.RGB, **values)
