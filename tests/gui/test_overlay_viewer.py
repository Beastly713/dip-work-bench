"""GUI coverage for reduced overlay viewing and export."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import numpy as np

from dip_workbench.core import ColourModel, ImageAsset
from dip_workbench.operations import (
    CircleOverlay,
    LineOverlay,
    OverlayArtifact,
    OverlayData,
    PointOverlay,
)
from dip_workbench.services import ExportService, ImageIOService
from dip_workbench.ui.widgets import OverlayViewer


def test_overlay_viewer_renders_bakes_and_exports_without_mutating(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    data = np.zeros((12, 16), dtype=np.uint8)
    asset = ImageAsset("base", data, ColourModel.GRAY, metadata={"source": "unit"})
    overlays = OverlayData(
        (
            LineOverlay(0, 0, 15, 11),
            CircleOverlay(8, 6, 3),
            PointOverlay(4, 5, 2),
        )
    )

    viewer = OverlayViewer()
    qtbot.addWidget(viewer)
    viewer.set_content(asset, overlays)
    viewer.visible_toggle.setChecked(False)
    viewer.visible_toggle.setChecked(True)

    rendered = viewer.render_image()
    assert not rendered.isNull()
    assert rendered.width() == asset.width and rendered.height() == asset.height

    baked = viewer.baked_image("baked")
    assert baked.colour_model is ColourModel.RGB
    assert baked.shape == (asset.height, asset.width, 3)
    assert baked.metadata["overlay_baked"] is True
    np.testing.assert_array_equal(asset.data, data)

    destination = ExportService(ImageIOService()).export(
        OverlayArtifact("overlay", "Overlay", overlays),
        tmp_path / "overlay.png",
        render_source=viewer,
    )
    assert destination.exists() and destination.stat().st_size > 0
