"""Result presenter contract for focused operation UIs."""

from dataclasses import dataclass
from typing import Protocol

from PySide6.QtCore import Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import OperationResult, ResultArtifact


class RenderSource(Protocol):
    def render_image(self, *, minimum_width: int = 1200, minimum_height: int = 800) -> QImage: ...


@dataclass(frozen=True, slots=True)
class DisplayedExportTarget:
    artifact: ResultArtifact
    render_source: RenderSource | None = None


class OperationResultPresenter(QWidget):
    displayed_export_target_changed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._displayed_export_target: DisplayedExportTarget | None = None

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        raise NotImplementedError

    def clear_result(self) -> None:
        self._set_displayed_export_target(None)

    def displayed_export_target(self) -> DisplayedExportTarget | None:
        return self._displayed_export_target

    def supports_before_after_comparison(self) -> bool:
        return False

    def activate_before_after_comparison(self) -> bool:
        return False

    def _set_displayed_export_target(self, target: DisplayedExportTarget | None) -> None:
        self._displayed_export_target = target
        self.displayed_export_target_changed.emit(target)
