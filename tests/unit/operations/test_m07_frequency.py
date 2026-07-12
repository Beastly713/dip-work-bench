"""Focused tests for M07 frequency-domain operations."""

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.execution import CancellationToken, OperationContext
from dip_workbench.operations import FourierSpectrumExecutor, HighPassExecutor, LowPassExecutor
from dip_workbench.operations.m07.common import (
    circular_frequency_mask,
    grayscale_float,
    inverse_shifted_fft,
    shifted_fft,
)


def context(image: ImageAsset, parameters: dict[str, object]) -> OperationContext:
    return OperationContext(
        {"image": image}, parameters, {}, {}, CancellationToken(), lambda *_: None
    )


def test_fft_inverse_reconstructs_and_spectrum_displays() -> None:
    data = np.arange(25, dtype=np.uint8).reshape(5, 5)
    image = ImageAsset("gray", data, ColourModel.GRAY)
    gray = grayscale_float(image)
    np.testing.assert_allclose(inverse_shifted_fft(shifted_fft(gray)), gray, atol=1e-4)
    result = FourierSpectrumExecutor().execute(
        context(image, {"center_spectrum": True, "logarithmic_scale": True, "show_phase": True})
    )
    assert result.primary_artifact.data.data.shape == data.shape  # type: ignore[union-attr]
    assert result.primary_artifact.data.data.dtype == np.uint8  # type: ignore[union-attr]
    assert result.get_artifact("fourier_phase").data.data.shape == data.shape  # type: ignore[union-attr]
    constant = ImageAsset("constant", np.full((7, 7), 20, dtype=np.uint8), ColourModel.GRAY)
    spectrum = shifted_fft(grayscale_float(constant))
    assert np.abs(spectrum)[3, 3] == np.abs(spectrum).max()


def test_frequency_filters_masks_metrics_and_source_immutable() -> None:
    data = np.arange(35, dtype=np.uint8).reshape(5, 7)
    image = ImageAsset("odd", data, ColourModel.GRAY)
    low = LowPassExecutor().execute(context(image, {"cutoff_percent": 100.0}))
    np.testing.assert_array_equal(low.primary_artifact.data.data, data)  # type: ignore[union-attr]
    high = HighPassExecutor().execute(context(image, {"cutoff_percent": 100.0}))
    assert np.count_nonzero(high.primary_artifact.data.data) == 0  # type: ignore[union-attr]
    constant = HighPassExecutor().execute(
        context(
            ImageAsset("c", np.full((5, 7), 50, dtype=np.uint8), ColourModel.GRAY),
            {"cutoff_percent": 10.0},
        )
    )
    assert np.count_nonzero(constant.primary_artifact.data.data) == 0  # type: ignore[union-attr]
    low_mask, _ = circular_frequency_mask(data.shape, 30.0, pass_type="low")
    high_mask, _ = circular_frequency_mask(data.shape, 30.0, pass_type="high")
    np.testing.assert_array_equal(high_mask, ~low_mask)
    lp = LowPassExecutor().execute(context(image, {"cutoff_percent": 30.0}))
    mask = lp.get_artifact("low_pass_mask").data.data  # type: ignore[union-attr]
    assert set(np.unique(mask).tolist()).issubset({0, 255})
    assert lp.metrics["Retained Frequency Bins"] == int(np.count_nonzero(mask))
    assert lp.primary_artifact.data.data.shape == data.shape  # type: ignore[union-attr]
    np.testing.assert_array_equal(image.data, data)
