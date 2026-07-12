"""GUI coverage for the generic operation workspace."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np
from PySide6.QtWidgets import QLabel

from dip_workbench.controllers import DocumentController, OperationController
from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.operations import (
    ApplyPolicy,
    InputSpec,
    ModuleId,
    OperationDefinition,
    OperationId,
    ParameterSpec,
    ParameterType,
    PresenterId,
    PreviewPolicy,
)
from dip_workbench.services import ImageIOService, ImageTransformService
from dip_workbench.state import DocumentStore, HistorySnapshotStore
from dip_workbench.ui.pages import OperationWorkspace
from dip_workbench.ui.panels import OperationParameterPanel


def definition(*, apply_policy=ApplyPolicy.PRIMARY_ARTIFACT):
    return OperationDefinition(
        OperationId("M03-01"),
        ModuleId.M03,
        "Synthetic",
        "Test the generic workspace.",
        (InputSpec("image", "Image"),),
        (ParameterSpec("amount", "Amount", ParameterType.INTEGER, 2),),
        PreviewPolicy.IMMEDIATE,
        apply_policy,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        lambda: object(),
        lambda: object(),
    )


def controller(tmp_path, *, with_image=True):
    history = tmp_path / "history"
    history.mkdir()
    io = ImageIOService()
    store = DocumentStore(HistorySnapshotStore(history, io))
    document = DocumentController(io, ImageTransformService(), store)
    if with_image:
        store.set_primary_image(
            ImageAsset(
                name="source", data=np.zeros((4, 5), dtype=np.uint8), colour_model=ColourModel.GRAY
            )
        )
    manager = OperationExecutionManager()
    return OperationController(document, manager), manager, store


def test_identity_inputs_ready_and_parameter_host(qtbot, tmp_path) -> None:
    item, _, _ = controller(tmp_path)
    item.select_operation(definition())
    workspace = OperationWorkspace()
    panel = OperationParameterPanel()
    qtbot.addWidget(workspace)
    qtbot.addWidget(panel)
    workspace.show_academic_operation(item)
    panel.configure(item)
    assert workspace.operation_header.operation_id_label.text() == "M03-01"
    assert workspace.operation_header.name_label.text() == "Synthetic"
    assert "generic workspace" in workspace.operation_header.purpose_label.text()
    assert workspace.operation_input_strip.original_button.isChecked()
    assert "Inputs are ready" in workspace.result_workspace._messages[item.workspace_state].text()
    assert panel.preview_button.text() == "Preview"
    assert "Amount" in [label.text() for label in panel.host.findChildren(QLabel)]


def test_missing_input_open_action_and_apply_policy(qtbot, tmp_path) -> None:
    item, _, _ = controller(tmp_path, with_image=False)
    item.select_operation(definition(apply_policy=ApplyPolicy.NONE))
    workspace = OperationWorkspace()
    panel = OperationParameterPanel()
    qtbot.addWidget(workspace)
    qtbot.addWidget(panel)
    workspace.show_academic_operation(item)
    panel.configure(item)
    assert workspace.result_workspace.open_button.isVisibleTo(workspace)
    assert not panel.apply_button.isVisibleTo(panel)


def test_run_label_and_reset_signal(qtbot, tmp_path) -> None:
    item, _, _ = controller(tmp_path)
    base = definition()
    explicit = type(base)(
        base.id,
        base.module_id,
        base.display_name,
        base.short_description,
        base.input_spec,
        base.parameter_schema,
        PreviewPolicy.EXPLICIT,
        base.apply_policy,
        base.presenter_id,
        base.executor_factory,
        base.presenter_factory,
    )
    item.select_operation(explicit)
    panel = OperationParameterPanel()
    qtbot.addWidget(panel)
    panel.configure(item)
    assert panel.preview_button.text() == "Run"
    item.set_parameter_value("amount", 4)
    panel.reset_requested.connect(item.reset_parameters)
    panel.reset_button.click()
    assert item.parameter_values["amount"] == 2
