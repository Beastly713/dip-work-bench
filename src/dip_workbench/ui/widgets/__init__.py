"""Reusable user-interface widgets."""

from dip_workbench.ui.widgets.comparison_canvas import SplitComparisonCanvas
from dip_workbench.ui.widgets.comparison_views import (
    BeforeAfterComparisonWidget,
    ComparisonMode,
    SideBySideComparisonWidget,
    TripleComparisonWidget,
)
from dip_workbench.ui.widgets.data_table import DataTableWidget
from dip_workbench.ui.widgets.generated_parameter_editor import GeneratedParameterEditor
from dip_workbench.ui.widgets.graph_widget import (
    GraphWidget,
    HistogramWidget,
    TransformationCurveWidget,
)
from dip_workbench.ui.widgets.image_canvas import CanvasInteractionMode, ImageCanvas
from dip_workbench.ui.widgets.matrix_viewer import MatrixViewer
from dip_workbench.ui.widgets.metrics_panel import MetricsPanel
from dip_workbench.ui.widgets.module_card import ModuleCard
from dip_workbench.ui.widgets.operation_header import OperationHeader
from dip_workbench.ui.widgets.operation_input_strip import OperationInputStrip
from dip_workbench.ui.widgets.operation_result_presenter import (
    DisplayedExportTarget,
    OperationResultPresenter,
)
from dip_workbench.ui.widgets.parameter_controls import KernelEditor
from dip_workbench.ui.widgets.result_workspace_host import ResultWorkspaceHost
from dip_workbench.ui.widgets.tree_viewer import TreeViewer
from dip_workbench.ui.widgets.view_transform_controller import ViewTransformController

__all__ = [
    "BeforeAfterComparisonWidget",
    "CanvasInteractionMode",
    "ComparisonMode",
    "DataTableWidget",
    "DisplayedExportTarget",
    "GeneratedParameterEditor",
    "GraphWidget",
    "HistogramWidget",
    "ImageCanvas",
    "KernelEditor",
    "MatrixViewer",
    "MetricsPanel",
    "ModuleCard",
    "OperationHeader",
    "OperationInputStrip",
    "OperationResultPresenter",
    "ResultWorkspaceHost",
    "SideBySideComparisonWidget",
    "SplitComparisonCanvas",
    "TransformationCurveWidget",
    "TreeViewer",
    "TripleComparisonWidget",
    "ViewTransformController",
]
