"""Module 4 histogram operations."""

from dip_workbench.operations.m04.histogram_analysis import (
    HISTOGRAM_ANALYSIS_DEFINITION,
    HistogramAnalysisExecutor,
)
from dip_workbench.operations.m04.histogram_equalization import (
    HISTOGRAM_EQUALIZATION_DEFINITION,
    HistogramEqualizationExecutor,
    equalization_lut,
)

__all__ = [
    "HISTOGRAM_ANALYSIS_DEFINITION",
    "HISTOGRAM_EQUALIZATION_DEFINITION",
    "HistogramAnalysisExecutor",
    "HistogramEqualizationExecutor",
    "equalization_lut",
]
