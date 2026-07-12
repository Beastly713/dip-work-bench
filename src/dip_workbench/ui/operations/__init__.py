"""Focused custom academic-operation interfaces."""

from dip_workbench.ui.operations.common import (
    BeforeAfterImagePresenter,
    BeforeAfterImageWithCurvePresenter,
    BeforeAfterImageWithMetricsPresenter,
)
from dip_workbench.ui.operations.filters import (
    ConvolutionParameterEditor,
    CustomConvolutionPresenter,
)
from dip_workbench.ui.operations.fundamentals import ChannelExtractionPresenter
from dip_workbench.ui.operations.histograms import (
    HistogramAnalysisPresenter,
    HistogramEqualizationPresenter,
)
from dip_workbench.ui.operations.image_negative import (
    ImageNegativeParameterEditor,
    ImageNegativeResultPresenter,
)
from dip_workbench.ui.operations.noise import AddNoisePresenter, NoiseParameterEditor

__all__ = [
    "AddNoisePresenter",
    "BeforeAfterImagePresenter",
    "BeforeAfterImageWithCurvePresenter",
    "BeforeAfterImageWithMetricsPresenter",
    "ChannelExtractionPresenter",
    "ConvolutionParameterEditor",
    "CustomConvolutionPresenter",
    "HistogramAnalysisPresenter",
    "HistogramEqualizationPresenter",
    "ImageNegativeParameterEditor",
    "ImageNegativeResultPresenter",
    "NoiseParameterEditor",
]
