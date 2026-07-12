"""Module 10 advanced edge and geometric feature operations."""

from dip_workbench.operations.m10.canny import CANNY_DEFINITION, CannyExecutor
from dip_workbench.operations.m10.dog_edges import DOG_EDGES_DEFINITION, DoGEdgesExecutor
from dip_workbench.operations.m10.harris_corners import (
    HARRIS_CORNERS_DEFINITION,
    HarrisCornersExecutor,
)
from dip_workbench.operations.m10.hough_circles import (
    HOUGH_CIRCLES_DEFINITION,
    HoughCirclesExecutor,
)
from dip_workbench.operations.m10.hough_lines import HOUGH_LINES_DEFINITION, HoughLinesExecutor
from dip_workbench.operations.m10.log_edges import LOG_EDGES_DEFINITION, LoGEdgesExecutor

__all__ = [
    "CANNY_DEFINITION",
    "DOG_EDGES_DEFINITION",
    "HARRIS_CORNERS_DEFINITION",
    "HOUGH_CIRCLES_DEFINITION",
    "HOUGH_LINES_DEFINITION",
    "LOG_EDGES_DEFINITION",
    "CannyExecutor",
    "DoGEdgesExecutor",
    "HarrisCornersExecutor",
    "HoughCirclesExecutor",
    "HoughLinesExecutor",
    "LoGEdgesExecutor",
]
