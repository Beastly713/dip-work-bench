"""Focused custom academic-operation interfaces."""

from dip_workbench.ui.operations.common import (
    BeforeAfterImagePresenter,
    BeforeAfterImageWithCurvePresenter,
    BeforeAfterImageWithMetricsPresenter,
)
from dip_workbench.ui.operations.fundamentals import ChannelExtractionPresenter
from dip_workbench.ui.operations.image_negative import (
    ImageNegativeParameterEditor,
    ImageNegativeResultPresenter,
)

__all__ = [
    "BeforeAfterImagePresenter",
    "BeforeAfterImageWithCurvePresenter",
    "BeforeAfterImageWithMetricsPresenter",
    "ChannelExtractionPresenter",
    "ImageNegativeParameterEditor",
    "ImageNegativeResultPresenter",
]
