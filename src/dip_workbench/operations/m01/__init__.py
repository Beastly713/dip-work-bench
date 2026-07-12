"""Module 1 fundamentals operations."""

from dip_workbench.operations.m01.black_and_white import (
    BLACK_AND_WHITE_DEFINITION,
    BlackAndWhiteExecutor,
)
from dip_workbench.operations.m01.channel_extraction import (
    CHANNEL_EXTRACTION_DEFINITION,
    ChannelExtractionExecutor,
)
from dip_workbench.operations.m01.colour_to_grayscale import (
    COLOUR_TO_GRAYSCALE_DEFINITION,
    ColourToGrayscaleExecutor,
)

__all__ = [
    "BLACK_AND_WHITE_DEFINITION",
    "CHANNEL_EXTRACTION_DEFINITION",
    "COLOUR_TO_GRAYSCALE_DEFINITION",
    "BlackAndWhiteExecutor",
    "ChannelExtractionExecutor",
    "ColourToGrayscaleExecutor",
]
