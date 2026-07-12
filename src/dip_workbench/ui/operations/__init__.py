"""Focused custom academic-operation interfaces."""

from dip_workbench.ui.operations.advanced_edges import DoGEdgePresenter, LoGEdgePresenter
from dip_workbench.ui.operations.common import (
    BeforeAfterImagePresenter,
    BeforeAfterImageWithCurvePresenter,
    BeforeAfterImageWithMetricsPresenter,
)
from dip_workbench.ui.operations.derivatives import (
    DerivativeTriplePresenter,
    LaplacianResponsePresenter,
)
from dip_workbench.ui.operations.filters import (
    ConvolutionParameterEditor,
    CustomConvolutionPresenter,
)
from dip_workbench.ui.operations.fundamentals import ChannelExtractionPresenter
from dip_workbench.ui.operations.geometric_features import GeometricFeaturePresenter
from dip_workbench.ui.operations.histograms import (
    HistogramAnalysisPresenter,
    HistogramEqualizationPresenter,
)
from dip_workbench.ui.operations.image_negative import (
    ImageNegativeParameterEditor,
    ImageNegativeResultPresenter,
)
from dip_workbench.ui.operations.noise import AddNoisePresenter, NoiseParameterEditor
from dip_workbench.ui.operations.sharpening import (
    DetailSharpeningPresenter,
    LaplacianSharpeningPresenter,
)

__all__ = [
    "AddNoisePresenter",
    "BeforeAfterImagePresenter",
    "BeforeAfterImageWithCurvePresenter",
    "BeforeAfterImageWithMetricsPresenter",
    "ChannelExtractionPresenter",
    "ConvolutionParameterEditor",
    "CustomConvolutionPresenter",
    "DerivativeTriplePresenter",
    "DetailSharpeningPresenter",
    "DoGEdgePresenter",
    "GeometricFeaturePresenter",
    "HistogramAnalysisPresenter",
    "HistogramEqualizationPresenter",
    "ImageNegativeParameterEditor",
    "ImageNegativeResultPresenter",
    "LaplacianResponsePresenter",
    "LaplacianSharpeningPresenter",
    "LoGEdgePresenter",
    "NoiseParameterEditor",
]
