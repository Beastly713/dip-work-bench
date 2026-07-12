"""Minimum result presenter contract for focused operation UIs."""

from PySide6.QtWidgets import QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import OperationResult


class OperationResultPresenter(QWidget):
    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        raise NotImplementedError

    def clear_result(self) -> None:
        raise NotImplementedError
