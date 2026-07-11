"""Conversion from canonical image assets to detached Qt images."""

from PySide6.QtGui import QImage

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError


def image_asset_to_qimage(asset: ImageAsset) -> QImage:
    if not isinstance(asset, ImageAsset) or asset.colour_model not in {
        ColourModel.RGB,
        ColourModel.GRAY,
        ColourModel.BINARY,
    }:
        raise InputValidationError("Only RGB, grayscale, and binary assets can be displayed.")
    image_format = (
        QImage.Format.Format_RGB888
        if asset.colour_model is ColourModel.RGB
        else QImage.Format.Format_Grayscale8
    )
    return QImage(
        asset.data.data,
        asset.width,
        asset.height,
        asset.data.strides[0],
        image_format,
    ).copy()
