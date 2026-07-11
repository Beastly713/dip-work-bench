import pytest

from dip_workbench.core import InputValidationError, RectangularRegion


def test_region_properties_and_fit() -> None:
    region = RectangularRegion(2, 3, 4, 5)
    assert (region.x2, region.y2, region.area, region.bounds) == (6, 8, 20, (2, 3, 6, 8))
    assert (
        region.fits_within(6, 8) and not region.fits_within(5, 8) and not region.fits_within(6, 7)
    )


@pytest.mark.parametrize(
    "values", [(-1, 0, 1, 1), (0, 0, 0, 1), (0, 0, 1, 0), (False, 0, 1, 1), (0.5, 0, 1, 1)]
)
def test_invalid_regions(values: tuple[object, ...]) -> None:
    with pytest.raises(InputValidationError):
        RectangularRegion(*values)  # type: ignore[arg-type]
