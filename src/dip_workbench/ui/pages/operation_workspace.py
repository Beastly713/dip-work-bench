"""Primary document workspace foundation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.controllers import OperationController
from dip_workbench.core import ImageAsset
from dip_workbench.ui.widgets import (
    ImageCanvas,
    OperationHeader,
    OperationInputStrip,
    ResultWorkspaceHost,
)


class OperationWorkspace(QWidget):
    open_image_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.mode_stack = QStackedWidget()
        document_view = QWidget()
        document_layout = QVBoxLayout(document_view)
        self._states = QStackedWidget()
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.addStretch()
        heading = QLabel("No image loaded")
        heading.setStyleSheet("font-size: 22px; font-weight: 600;")
        message = QLabel("Open a primary image to begin working.")
        self.open_button = QPushButton("Open Image")
        self.open_button.clicked.connect(self.open_image_requested)
        empty_layout.addWidget(heading)
        empty_layout.addWidget(message)
        empty_layout.addWidget(self.open_button)
        empty_layout.addStretch()

        image_state = QWidget()
        image_layout = QVBoxLayout(image_state)
        self.image_name_label = QLabel()
        self.image_name_label.setStyleSheet("font-size: 17px; font-weight: 600;")
        self.image_info_label = QLabel()
        self.image_canvas = ImageCanvas()
        image_layout.addWidget(self.image_name_label)
        image_layout.addWidget(self.image_info_label)
        image_layout.addWidget(self.image_canvas, 1)
        self._states.addWidget(empty)
        self._states.addWidget(image_state)
        document_layout.addWidget(self._states)
        self.academic_view = QWidget()
        academic_layout = QVBoxLayout(self.academic_view)
        self.operation_header = OperationHeader()
        self.operation_input_strip = OperationInputStrip()
        self.result_workspace = ResultWorkspaceHost()
        academic_layout.addWidget(self.operation_header)
        academic_layout.addWidget(self.operation_input_strip)
        academic_layout.addWidget(self.result_workspace, 1)
        self.mode_stack.addWidget(document_view)
        self.mode_stack.addWidget(self.academic_view)
        layout.addWidget(self.mode_stack)
        self.show_document_view()

    def show_document_view(self) -> None:
        self.mode_stack.setCurrentIndex(0)

    def show_academic_operation(self, controller: OperationController) -> None:
        definition = controller.active_definition
        if definition is None:
            self.operation_header.clear_operation()
        else:
            self.operation_header.set_operation(definition)
        self.refresh_academic_operation(controller)
        self.mode_stack.setCurrentIndex(1)

    def refresh_academic_operation(self, controller: OperationController) -> None:
        self.operation_input_strip.refresh(controller)
        self.result_workspace.refresh(controller)

    def set_image(self, asset: ImageAsset) -> None:
        self.image_name_label.setText(asset.name)
        self.image_info_label.setText(
            f"{asset.width} × {asset.height} • {asset.colour_model.value}"  # noqa: RUF001
        )
        self.image_canvas.set_image(asset)
        self._states.setCurrentIndex(1)

    def set_preview_image(self, asset: ImageAsset, operation_name: str) -> None:
        self.image_name_label.setText(f"Preview: {operation_name}")
        self.image_info_label.setText("Not applied to Current Result")
        self.image_canvas.set_image(asset)
        self._states.setCurrentIndex(1)

    def show_current_image(self, asset: ImageAsset) -> None:
        self.set_image(asset)

    def clear_image(self) -> None:
        self.image_canvas.clear_image()
        self._states.setCurrentIndex(0)
