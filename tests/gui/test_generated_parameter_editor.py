"""Tests for schema-generated parameter controls."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dip_workbench.operations import (
    ConditionOperator,
    ParameterChoice,
    ParameterCondition,
    ParameterSpec,
    ParameterType,
)
from dip_workbench.ui.widgets import GeneratedParameterEditor, KernelEditor


def schema() -> tuple[ParameterSpec, ...]:
    return (
        ParameterSpec("count", "Count", ParameterType.INTEGER, 2, minimum=1, maximum=9),
        ParameterSpec("gain", "Gain", ParameterType.FLOAT, 0.5, step=0.1),
        ParameterSpec("enabled", "Enabled", ParameterType.BOOLEAN, True),
        ParameterSpec(
            "mode",
            "Mode",
            ParameterType.ENUM,
            "a",
            choices=(ParameterChoice("a", "A"), ParameterChoice("b", "B")),
        ),
        ParameterSpec(
            "radio",
            "Radio",
            ParameterType.RADIO,
            1,
            choices=(ParameterChoice(1, "One"), ParameterChoice(2, "Two")),
        ),
        ParameterSpec("integer_range", "Integer range", ParameterType.INTEGER_RANGE, (1, 3)),
        ParameterSpec("float_range", "Float range", ParameterType.FLOAT_RANGE, (0.1, 0.9)),
        ParameterSpec(
            "selected",
            "Selected",
            ParameterType.MULTI_SELECT,
            ("x",),
            choices=(ParameterChoice("x", "X"), ParameterChoice("y", "Y")),
        ),
        ParameterSpec("names", "Names", ParameterType.TEXT_LIST, ("one",)),
        ParameterSpec("numbers", "Numbers", ParameterType.NUMERIC_LIST, (1, 2.5)),
        ParameterSpec("kernel", "Kernel", ParameterType.KERNEL, ((1, 0), (0, 1)), advanced=True),
        ParameterSpec(
            "conditional",
            "Conditional",
            ParameterType.INTEGER,
            1,
            visible_when=ParameterCondition("enabled", ConditionOperator.TRUTHY),
            enabled_when=ParameterCondition("mode", ConditionOperator.EQUALS, "a"),
        ),
    )


def test_controls_values_conditions_advanced_and_no_recursive_emit(qtbot) -> None:  # type: ignore[no-untyped-def]
    editor = GeneratedParameterEditor(schema())
    qtbot.addWidget(editor)
    assert set(editor.controls) == {item.key for item in schema()}
    emissions: list[object] = []
    editor.values_changed.connect(emissions.append)
    editor.set_values({item.key: item.default for item in schema()})
    assert not emissions
    editor.controls["enabled"].setChecked(False)  # type: ignore[attr-defined]
    assert editor.rows["conditional"].isHidden()
    editor.controls["enabled"].setChecked(True)  # type: ignore[attr-defined]
    editor.controls["mode"].setCurrentIndex(1)  # type: ignore[attr-defined]
    assert not editor.controls["conditional"].isEnabled()
    assert not editor.advanced_container.isVisible()
    editor.advanced_toggle.click()
    assert editor.advanced_container.isVisibleTo(editor)
    assert emissions and set(emissions[-1]) == {item.key for item in schema()}  # type: ignore[arg-type]


def test_kernel_invalid_value_and_inline_error(qtbot) -> None:  # type: ignore[no-untyped-def]
    editor = GeneratedParameterEditor(schema())
    qtbot.addWidget(editor)
    kernel = editor.controls["kernel"]
    assert isinstance(kernel, KernelEditor)
    kernel.table.item(0, 0).setText("invalid")
    assert kernel.value()[0][0] == "invalid"
    editor.set_validation_errors({"kernel": "Kernel values must be numeric."})
    assert "numeric" in editor.error_labels["kernel"].text()
    assert editor.advanced_toggle.isChecked()
