"""GUI integration tests for displayed export targets."""

from PySide6.QtGui import QImage

from dip_workbench.operations import CurveArtifact
from dip_workbench.services import ExportService, ImageIOService
from dip_workbench.ui.widgets import (
    DisplayedExportTarget,
    OperationResultPresenter,
    ResultWorkspaceHost,
)


class RenderSource:
    def __init__(self) -> None:
        self.called = False

    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage:
        self.called = True
        image = QImage(minimum_width, minimum_height, QImage.Format.Format_RGB32)
        image.fill(0xFFFFFFFF)
        return image


class Presenter(OperationResultPresenter):
    def present(self, input_asset, result) -> None:  # type: ignore[no-untyped-def]
        del input_asset, result


def test_graph_png_uses_render_source(tmp_path) -> None:  # type: ignore[no-untyped-def]
    source = RenderSource()
    service = ExportService(ImageIOService())
    destination = service.export(
        CurveArtifact("curve", "Curve", {"x": [0, 1], "y": [1, 0]}),
        tmp_path / "curve.png",
        render_source=source,
    )
    assert source.called
    assert destination.exists() and destination.stat().st_size > 0


def test_result_workspace_target_lifecycle(qtbot) -> None:  # type: ignore[no-untyped-def]
    host = ResultWorkspaceHost()
    qtbot.addWidget(host)
    seen: list[object] = []
    host.displayed_export_target_changed.connect(seen.append)
    presenter = Presenter()
    artifact = CurveArtifact("curve", "Curve", {"x": [0], "y": [1]})
    host.set_result_widget(presenter)
    presenter._set_displayed_export_target(DisplayedExportTarget(artifact))
    assert host.displayed_export_target().artifact is artifact  # type: ignore[union-attr]
    host.set_result_widget(None)
    assert seen[-1] is None
    assert host.displayed_export_target() is None
