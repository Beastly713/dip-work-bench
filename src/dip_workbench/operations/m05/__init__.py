"""Module 5 filtering operations."""

from dip_workbench.operations.m05.blur_filters import BLUR_FILTERS_DEFINITION, BlurFiltersExecutor
from dip_workbench.operations.m05.custom_convolution import (
    CUSTOM_CONVOLUTION_DEFINITION,
    CustomConvolutionExecutor,
)

__all__ = [
    "BLUR_FILTERS_DEFINITION",
    "CUSTOM_CONVOLUTION_DEFINITION",
    "BlurFiltersExecutor",
    "CustomConvolutionExecutor",
]
