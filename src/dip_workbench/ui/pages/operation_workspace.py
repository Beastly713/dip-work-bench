"""Primary document workspace foundation."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QLabel, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.controllers import OperationController
from dip_workbench.core import ImageAsset
from dip_workbench.ui.widgets import (
    ImageCanvas,
    OperationHeader,
    OperationInputStrip,
    OperationResultPresenter,
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
        self._result_presenter: OperationResultPresenter | None = None
        self._presenter_operation_id: str | None = None
        self._presented_result: object | None = None
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
            operation_id = str(definition.id)
            if operation_id != self._presenter_operation_id:
                candidate = definition.presenter_factory()
                self._result_presenter = (
                    candidate if isinstance(candidate, OperationResultPresenter) else None
                )
                self._presenter_operation_id = operation_id
                self._presented_result = None
                self.result_workspace.set_result_widget(self._result_presenter)
        self.refresh_academic_operation(controller)
        self.mode_stack.setCurrentIndex(1)

    def refresh_academic_operation(self, controller: OperationController) -> None:
        self.operation_input_strip.refresh(controller)
        self.result_workspace.refresh(controller)
        result = controller.active_result
        if self._result_presenter is not None and result is not self._presented_result:
            if result is None:
                self._result_presenter.clear_result()
            else:
                input_asset = result.metadata.get("input_asset")
                if not isinstance(input_asset, ImageAsset):
                    selected = controller.resolved_inputs().get("image")
                    input_asset = selected if isinstance(selected, ImageAsset) else None
                if input_asset is not None:
                    self._result_presenter.present(input_asset, result)
            self._presented_result = result

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
