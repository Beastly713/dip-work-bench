"""Unicode-safe image loading and saving at the OpenCV boundary."""

from pathlib import Path
from typing import ClassVar

import cv2
import numpy as np

from dip_workbench.core.errors import ExportError, UnsupportedImageError
from dip_workbench.core.image import ColourModel, ImageAsset
from dip_workbench.core.image_conversion import (
    bgr_to_rgb,
    bgra_to_rgba,
    composite_rgba_on_background,
    rgb_to_bgr,
)


class ImageIOService:
    """Load and save supported canonical document images."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".tif",
        ".tiff",
    }

    def load(self, path: str | Path) -> ImageAsset:
        source = Path(path)
        suffix = source.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise UnsupportedImageError(
                f"Unsupported image extension: {source.suffix or '(none)'}."
            )
        if not source.exists() or not source.is_file():
            raise UnsupportedImageError("Image source does not exist or is not a file.")
        try:
            encoded = source.read_bytes()
        except OSError as error:
            raise UnsupportedImageError("Image source could not be read.") from error
        if not encoded:
            raise UnsupportedImageError("Image source is empty.")
        try:
            decoded = cv2.imdecode(np.frombuffer(encoded, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        except cv2.error as error:
            raise UnsupportedImageError("Image source could not be decoded.") from error
        if decoded is None:
            raise UnsupportedImageError("Image source could not be decoded.")
        if decoded.dtype != np.uint8:
            raise UnsupportedImageError("Only 8-bit document images are supported.")

        metadata: dict[str, object] = {
            "source_format": suffix,
            "source_filename": source.name,
        }
        if decoded.ndim == 2:
            canonical = np.ascontiguousarray(decoded)
            colour_model = ColourModel.GRAY
        elif decoded.ndim == 3 and decoded.shape[2] == 3:
            canonical = bgr_to_rgb(decoded)
            colour_model = ColourModel.RGB
        elif decoded.ndim == 3 and decoded.shape[2] == 4:
            canonical = composite_rgba_on_background(bgra_to_rgba(decoded))
            colour_model = ColourModel.RGB
            metadata.update(
                {
                    "source_had_alpha": True,
                    "alpha_composite_background": (255, 255, 255),
                }
            )
        else:
            raise UnsupportedImageError("Decoded image has an unsupported channel layout.")
        return ImageAsset(
            name=source.name,
            data=canonical,
            colour_model=colour_model,
            source_path=source,
            metadata=metadata,
        )

    def save(
        self,
        asset: ImageAsset,
        path: str | Path,
        *,
        jpeg_quality: int = 95,
        png_compression: int = 3,
    ) -> Path:
        if not isinstance(asset, ImageAsset):
            raise ExportError("Only canonical image assets can be saved.")
        destination = Path(path)
        suffix = destination.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            raise ExportError(f"Unsupported output extension: {destination.suffix or '(none)'}.")
        if asset.colour_model not in {ColourModel.RGB, ColourModel.GRAY, ColourModel.BINARY}:
            raise ExportError("This image asset cannot be saved.")
        if (
            isinstance(jpeg_quality, bool)
            or not isinstance(jpeg_quality, int)
            or not 1 <= jpeg_quality <= 100
        ):
            raise ExportError("JPEG quality must be an integer from 1 to 100.")
        if (
            isinstance(png_compression, bool)
            or not isinstance(png_compression, int)
            or not 0 <= png_compression <= 9
        ):
            raise ExportError("PNG compression must be an integer from 0 to 9.")
        if suffix in {".jpg", ".jpeg"} and asset.colour_model is ColourModel.BINARY:
            raise ExportError("Binary masks cannot be saved as JPEG.")
        if not destination.parent.is_dir():
            raise ExportError("Output parent directory does not exist.")
        if destination.is_dir():
            raise ExportError("Output destination is a directory.")

        boundary_data = (
            rgb_to_bgr(asset.data) if asset.colour_model is ColourModel.RGB else asset.data
        )
        parameters: list[int] = []
        if suffix in {".jpg", ".jpeg"}:
            parameters = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
        elif suffix == ".png":
            parameters = [cv2.IMWRITE_PNG_COMPRESSION, png_compression]
        try:
            succeeded, encoded = cv2.imencode(suffix, boundary_data, parameters)
        except cv2.error as error:
            raise ExportError("Image encoding failed.") from error
        if not succeeded:
            raise ExportError("Image encoding failed.")
        try:
            destination.write_bytes(encoded.tobytes())
        except OSError as error:
            raise ExportError("Encoded image could not be written.") from error
        return destination
