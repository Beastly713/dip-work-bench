"""Module 9 basic segmentation operations."""

from dip_workbench.operations.m09.adaptive_thresholding import (
    ADAPTIVE_THRESHOLD_DEFINITION,
    AdaptiveThresholdExecutor,
)
from dip_workbench.operations.m09.colour_range import COLOUR_RANGE_DEFINITION, ColourRangeExecutor
from dip_workbench.operations.m09.range_thresholding import (
    RANGE_THRESHOLD_DEFINITION,
    RangeThresholdExecutor,
)

__all__ = [
    "ADAPTIVE_THRESHOLD_DEFINITION",
    "COLOUR_RANGE_DEFINITION",
    "RANGE_THRESHOLD_DEFINITION",
    "AdaptiveThresholdExecutor",
    "ColourRangeExecutor",
    "RangeThresholdExecutor",
]
