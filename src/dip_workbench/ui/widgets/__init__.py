"""Reusable user-interface widgets."""

from dip_workbench.ui.widgets.generated_parameter_editor import GeneratedParameterEditor
from dip_workbench.ui.widgets.image_canvas import CanvasInteractionMode, ImageCanvas
from dip_workbench.ui.widgets.module_card import ModuleCard
from dip_workbench.ui.widgets.operation_header import OperationHeader
from dip_workbench.ui.widgets.operation_input_strip import OperationInputStrip
from dip_workbench.ui.widgets.operation_result_presenter import OperationResultPresenter
from dip_workbench.ui.widgets.parameter_controls import KernelEditor
from dip_workbench.ui.widgets.result_workspace_host import ResultWorkspaceHost

__all__ = [
    "CanvasInteractionMode",
    "GeneratedParameterEditor",
    "ImageCanvas",
    "KernelEditor",
    "ModuleCard",
    "OperationHeader",
    "OperationInputStrip",
    "OperationResultPresenter",
    "ResultWorkspaceHost",
]
