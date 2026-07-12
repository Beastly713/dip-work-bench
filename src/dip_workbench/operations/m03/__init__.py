"""Module 3 production academic operations."""

from dip_workbench.operations.m03.gamma_correction import (
    GAMMA_CORRECTION_DEFINITION,
    GammaCorrectionExecutor,
)
from dip_workbench.operations.m03.image_negative import (
    IMAGE_NEGATIVE_DEFINITION,
    ImageNegativeExecutor,
)

__all__ = [
    "GAMMA_CORRECTION_DEFINITION",
    "IMAGE_NEGATIVE_DEFINITION",
    "GammaCorrectionExecutor",
    "ImageNegativeExecutor",
]
