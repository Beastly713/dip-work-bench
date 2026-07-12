"""Tests for Unicode-safe canonical image file I/O."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from dip_workbench.core import ColourModel, ExportError, ImageAsset, UnsupportedImageError
from dip_workbench.services import ImageIOService


def asset(data: np.ndarray, model: ColourModel) -> ImageAsset:
    return ImageAsset(name="generated", data=data, colour_model=model)


@pytest.mark.parametrize("suffix", [".png", ".bmp", ".tif"])
def test_lossless_rgb_round_trip(tmp_path: Path, suffix: str) -> None:
    service = ImageIOService()
    data = np.array([[[255, 10, 20], [0, 100, 200]]], dtype=np.uint8)
    path = tmp_path / f"colour{suffix}"
    assert service.save(asset(data, ColourModel.RGB), path) == path
    loaded = service.load(path)
    assert loaded.colour_model is ColourModel.RGB
    np.testing.assert_array_equal(loaded.data, data)


def test_lossless_grayscale_and_binary_png_round_trips(tmp_path: Path) -> None:
    service = ImageIOService()
    grayscale = np.array([[0, 70], [180, 255]], dtype=np.uint8)
    binary = np.array([[0, 255], [255, 0]], dtype=np.uint8)
    gray_path = tmp_path / "gray.png"
    binary_path = tmp_path / "mask.png"
    service.save(asset(grayscale, ColourModel.GRAY), gray_path)
    service.save(asset(binary, ColourModel.BINARY), binary_path)
    np.testing.assert_array_equal(service.load(gray_path).data, grayscale)
    np.testing.assert_array_equal(service.load(binary_path).data, binary)


def test_jpeg_preserves_dimensions_and_model(tmp_path: Path) -> None:
    service = ImageIOService()
    data = np.full((12, 15, 3), (40, 100, 180), dtype=np.uint8)
    path = service.save(asset(data, ColourModel.RGB), tmp_path / "photo.jpg")
    loaded = service.load(path)
    assert loaded.colour_model is ColourModel.RGB
    assert loaded.shape == data.shape


@pytest.mark.parametrize(
    "relative", [Path("unicode-目录") / "चित्र.png", Path("with spaces") / "a b.png"]
)
def test_unicode_and_space_paths(tmp_path: Path, relative: Path) -> None:
    directory = tmp_path / relative.parent
    directory.mkdir()
    path = directory / relative.name
    data = np.array([[[1, 2, 3]]], dtype=np.uint8)
    service = ImageIOService()
    service.save(asset(data, ColourModel.RGB), path)
    np.testing.assert_array_equal(service.load(path).data, data)


def test_uppercase_suffix_is_supported(tmp_path: Path) -> None:
    service = ImageIOService()
    path = tmp_path / "UPPER.PNG"
    service.save(asset(np.zeros((2, 2), dtype=np.uint8), ColourModel.GRAY), path)
    assert service.load(path).colour_model is ColourModel.GRAY


def test_bgra_png_loads_composited_with_metadata(tmp_path: Path) -> None:
    bgra = np.array([[[30, 20, 10, 0], [60, 50, 40, 255]]], dtype=np.uint8)
    succeeded, encoded = cv2.imencode(".png", bgra)
    assert succeeded
    path = tmp_path / "alpha.png"
    path.write_bytes(encoded.tobytes())
    loaded = ImageIOService().load(path)
    np.testing.assert_array_equal(loaded.data, [[[255, 255, 255], [40, 50, 60]]])
    assert loaded.colour_model is ColourModel.RGB
    assert loaded.metadata["source_had_alpha"] is True
    assert loaded.metadata["alpha_composite_background"] == (255, 255, 255)


def test_missing_unsupported_empty_and_corrupt_sources(tmp_path: Path) -> None:
    service = ImageIOService()
    with pytest.raises(UnsupportedImageError):
        service.load(tmp_path / "missing.png")
    unsupported = tmp_path / "image.gif"
    unsupported.write_bytes(b"data")
    with pytest.raises(UnsupportedImageError):
        service.load(unsupported)
    empty = tmp_path / "empty.png"
    empty.write_bytes(b"")
    with pytest.raises(UnsupportedImageError):
        service.load(empty)
    corrupt = tmp_path / "corrupt.png"
    corrupt.write_bytes(b"not an image")
    with pytest.raises(UnsupportedImageError):
        service.load(corrupt)


def test_16_bit_source_is_rejected(tmp_path: Path) -> None:
    succeeded, encoded = cv2.imencode(".png", np.array([[1024]], dtype=np.uint16))
    assert succeeded
    path = tmp_path / "sixteen-bit.png"
    path.write_bytes(encoded.tobytes())
    with pytest.raises(UnsupportedImageError, match="8-bit"):
        ImageIOService().load(path)


def test_save_rejections_and_parameters(tmp_path: Path) -> None:
    service = ImageIOService()
    gray = asset(np.zeros((2, 2), dtype=np.uint8), ColourModel.GRAY)
    binary = asset(np.zeros((2, 2), dtype=np.uint8), ColourModel.BINARY)
    with pytest.raises(ExportError, match="parent"):
        service.save(gray, tmp_path / "missing" / "image.png")
    with pytest.raises(ExportError, match="JPEG"):
        service.save(binary, tmp_path / "mask.jpg")
    with pytest.raises(ExportError, match="quality"):
        service.save(gray, tmp_path / "image.jpg", jpeg_quality=0)
    with pytest.raises(ExportError, match="compression"):
        service.save(gray, tmp_path / "image.png", png_compression=10)
    with pytest.raises(ExportError, match="extension"):
        service.save(gray, tmp_path / "image.gif")
