"""Reusable before/after and multi-image comparison widgets."""

from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QEvent, QObject, Qt, Signal
from PySide6.QtGui import QKeyEvent, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ImageAsset
from dip_workbench.ui.widgets.comparison_canvas import SplitComparisonCanvas
from dip_workbench.ui.widgets.image_canvas import ImageCanvas
from dip_workbench.ui.widgets.view_transform_controller import ViewTransformController


class ComparisonMode(StrEnum):
    SIDE_BY_SIDE = "side_by_side"
    SPLIT = "split"


class LabeledImagePanel(QFrame):
    maximize_requested = Signal(object)

    def __init__(
        self, title: str, controller: ViewTransformController, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._base_title = title
        self.controller = controller
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        self.label = QLabel(title)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("font-weight: 600;")
        buttons = QHBoxLayout()
        self.fit_button = QPushButton("Fit")
        self.actual_button = QPushButton("100%")
        self.zoom_out_button = QPushButton("-")
        self.zoom_in_button = QPushButton("+")
        self.max_button = QPushButton("Maximize")
        for button, text in (
            (self.fit_button, "Fit image to panel"),
            (self.actual_button, "Show at 100%"),
            (self.zoom_out_button, "Zoom out"),
            (self.zoom_in_button, "Zoom in"),
            (self.max_button, "Maximize or restore this panel"),
        ):
            button.setToolTip(text)
            button.setAccessibleName(text)
            buttons.addWidget(button)
        self.canvas = ImageCanvas()
        self.empty_label = QLabel("No image to display")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.empty_label)
        self.stack.addWidget(self.canvas)
        layout.addWidget(self.label)
        layout.addLayout(buttons)
        layout.addWidget(self.stack, 1)
        self.fit_button.clicked.connect(controller.fit_all)
        self.actual_button.clicked.connect(controller.actual_size_all)
        self.zoom_out_button.clicked.connect(controller.zoom_out_all)
        self.zoom_in_button.clicked.connect(controller.zoom_in_all)
        self.max_button.clicked.connect(lambda: self.maximize_requested.emit(self))

    def set_image(self, asset: ImageAsset, *, fit: bool = False) -> None:
        self.canvas.set_image(asset, fit=fit)
        self.stack.setCurrentWidget(self.canvas)

    def clear(self) -> None:
        self.canvas.clear_image()
        self.label.setText(self._base_title)
        self.stack.setCurrentWidget(self.empty_label)

    def set_title(self, title: str) -> None:
        self._base_title = title
        self.label.setText(title)

    def restore_title(self) -> None:
        self.label.setText(self._base_title)

    def set_maximized(self, maximized: bool) -> None:
        self.max_button.setText("Restore" if maximized else "Maximize")


class _PanelComparison(QWidget):
    def __init__(self, labels: tuple[str, ...], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = ViewTransformController(self)
        self.panels = [LabeledImagePanel(label, self.controller) for label in labels]
        self._maximized: LabeledImagePanel | None = None
        self._layout = QHBoxLayout(self)
        for panel in self.panels:
            panel.maximize_requested.connect(self._toggle_maximize)
            self._layout.addWidget(panel, 1)
        self.controller.set_canvases(tuple(panel.canvas for panel in self.panels))

    def _toggle_maximize(self, panel: LabeledImagePanel) -> None:
        self._maximized = None if self._maximized is panel else panel
        for item in self.panels:
            item.setVisible(self._maximized is None or item is self._maximized)
            item.set_maximized(self._maximized is item)

    def clear(self) -> None:
        self._maximized = None
        for panel in self.panels:
            panel.clear()
            panel.setVisible(True)
            panel.set_maximized(False)


class SideBySideComparisonWidget(_PanelComparison):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(("Input", "Result"), parent)

    def set_images(
        self,
        left_label: str,
        left_asset: ImageAsset,
        right_label: str,
        right_asset: ImageAsset,
    ) -> None:
        self.clear()
        self.panels[0].set_title(left_label)
        self.panels[1].set_title(right_label)
        self.panels[0].set_image(left_asset)
        self.panels[1].set_image(right_asset)
        self.controller.fit_all()


class TripleComparisonWidget(_PanelComparison):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(("Image A", "Image B", "Result"), parent)

    def set_images(
        self, images: tuple[tuple[str, ImageAsset], tuple[str, ImageAsset], tuple[str, ImageAsset]]
    ) -> None:
        self.clear()
        for panel, (label, asset) in zip(self.panels, images, strict=True):
            panel.set_title(label)
            panel.set_image(asset)
        self.controller.fit_all()


class BeforeAfterComparisonWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._input_asset: ImageAsset | None = None
        self._result_asset: ImageAsset | None = None
        self._input_label = "Input"
        self._result_label = "Result"
        self._held_split: float | None = None
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout = QVBoxLayout(self)
        controls = QHBoxLayout()
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Side by side", ComparisonMode.SIDE_BY_SIDE.value)
        self.mode_combo.addItem("Split", ComparisonMode.SPLIT.value)
        self.hint_label = QLabel("Hold B to view Input")
        controls.addWidget(QLabel("Comparison mode:"))
        controls.addWidget(self.mode_combo)
        controls.addStretch()
        controls.addWidget(self.hint_label)
        self.stack = QStackedWidget()
        self.side_by_side = SideBySideComparisonWidget()
        self.split = SplitComparisonCanvas()
        self.stack.addWidget(self.side_by_side)
        self.stack.addWidget(self.split)
        layout.addLayout(controls)
        layout.addWidget(self.stack, 1)
        self.mode_combo.currentIndexChanged.connect(self._mode_changed)
        self.installEventFilter(self)
        for child in self.findChildren(QWidget):
            child.installEventFilter(self)

    def set_images(
        self,
        input_asset: ImageAsset,
        result_asset: ImageAsset,
        *,
        input_label: str = "Input",
        result_label: str = "Result",
    ) -> None:
        self._input_asset = input_asset
        self._result_asset = result_asset
        self._input_label = input_label
        self._result_label = result_label
        self.side_by_side.set_images(input_label, input_asset, result_label, result_asset)
        self.split.set_images(input_asset, result_asset)
        model = self.mode_combo.model()
        if isinstance(model, QStandardItemModel):
            model.item(1).setEnabled(input_asset.shape == result_asset.shape)
        if input_asset.shape != result_asset.shape and self.mode() is ComparisonMode.SPLIT:
            self.set_mode(ComparisonMode.SIDE_BY_SIDE)

    def mode(self) -> ComparisonMode:
        return ComparisonMode(self.mode_combo.currentData())

    def set_mode(self, mode: ComparisonMode) -> None:
        index = self.mode_combo.findData(mode.value)
        model = self.mode_combo.model()
        if index >= 0 and isinstance(model, QStandardItemModel) and model.item(index).isEnabled():
            self.mode_combo.setCurrentIndex(index)

    def focus_comparison_controls(self) -> None:
        self.mode_combo.setFocus(Qt.FocusReason.ShortcutFocusReason)

    def clear(self) -> None:
        self._input_asset = None
        self._result_asset = None
        self.side_by_side.clear()
        self.split.clear()
        self.mode_combo.setCurrentIndex(0)

    def _mode_changed(self) -> None:
        self.stack.setCurrentWidget(
            self.split if self.mode() is ComparisonMode.SPLIT else self.side_by_side
        )

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if not isinstance(event, QKeyEvent) or event.isAutoRepeat():
            return super().eventFilter(watched, event)
        if event.key() != Qt.Key.Key_B:
            return super().eventFilter(watched, event)
        if event.type() == QEvent.Type.KeyPress:
            self._hold_input()
            return True
        if event.type() == QEvent.Type.KeyRelease:
            self._release_input()
            return True
        return super().eventFilter(watched, event)

    def _hold_input(self) -> None:
        if self._input_asset is None or self._result_asset is None:
            return
        if self.mode() is ComparisonMode.SIDE_BY_SIDE:
            self.side_by_side.panels[1].label.setText(f"{self._input_label} - Hold B")
            self.side_by_side.panels[1].set_image(self._input_asset)
        else:
            self._held_split = self.split.split_percent
            self.split.set_split_percent(100.0)

    def _release_input(self) -> None:
        if self._input_asset is None or self._result_asset is None:
            return
        if self.mode() is ComparisonMode.SIDE_BY_SIDE:
            self.side_by_side.panels[1].label.setText(self._result_label)
            self.side_by_side.panels[1].set_image(self._result_asset)
        elif self._held_split is not None:
            self.split.set_split_percent(self._held_split)
            self._held_split = None
