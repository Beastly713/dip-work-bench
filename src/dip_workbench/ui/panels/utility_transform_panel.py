"""Focused controls for C06 image-editing utilities."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ColourModel, ImageAsset, RectangularRegion
from dip_workbench.services import FlipDirection, InterpolationMode, RotationCanvasMode


class UtilityTransformPanel(QWidget):
    preview_crop_requested = Signal()
    preview_resize_requested = Signal(int, int, object)
    preview_rotate_requested = Signal(float, object, object)
    preview_flip_requested = Signal(object)
    apply_preview_requested = Signal()
    clear_preview_requested = Signal()
    select_region_requested = Signal()
    clear_region_requested = Signal()
    finish_region_requested = Signal()
    cancel_utility_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.heading = QLabel("Image Utility")
        layout.addWidget(self.heading)
        form = QFormLayout()
        self.width_spin = QSpinBox()
        self.height_spin = QSpinBox()
        for spin in (self.width_spin, self.height_spin):
            spin.setRange(1, 100000)
        self.aspect_lock = QCheckBox("Lock aspect ratio")
        self.aspect_lock.setChecked(True)
        self.interpolation_combo = QComboBox()
        for mode in InterpolationMode:
            self.interpolation_combo.addItem(mode.value.title(), mode)
        self.angle_spin = QDoubleSpinBox()
        self.angle_spin.setRange(-36000, 36000)
        self.rotate_minus_90_button = QPushButton("-90°")
        self.rotate_plus_90_button = QPushButton("90°")
        self.rotate_180_button = QPushButton("180°")
        self.canvas_combo = QComboBox()
        for canvas_mode in RotationCanvasMode:
            self.canvas_combo.addItem(canvas_mode.value.title(), canvas_mode)
        self.flip_combo = QComboBox()
        for direction in FlipDirection:
            self.flip_combo.addItem(direction.value.title(), direction)
        self.region_label = QLabel("No region selected")
        for label, widget in (
            ("Width", self.width_spin),
            ("Height", self.height_spin),
            ("Interpolation", self.interpolation_combo),
            ("Angle", self.angle_spin),
            ("Canvas", self.canvas_combo),
            ("Direction", self.flip_combo),
        ):
            form.addRow(label, widget)
        form.addRow(self.aspect_lock)
        form.addRow(
            self.rotate_minus_90_button,
            self.rotate_plus_90_button,
        )
        form.addRow(self.rotate_180_button)
        form.addRow("Region", self.region_label)
        self.select_region_button = QPushButton("Select/Reselect Region")
        self.clear_region_button = QPushButton("Clear Region")
        self.preview_button = QPushButton("Preview")
        self.apply_button = QPushButton("Apply")
        self.clear_preview_button = QPushButton("Clear Preview")
        self.finish_button = QPushButton("Finish Region")
        self.cancel_button = QPushButton("Cancel")
        self.mode_stack = QStackedWidget()
        self._mode_indices: dict[str, int] = {}
        crop_page = QWidget()
        crop_layout = QVBoxLayout(crop_page)
        crop_layout.addWidget(self.region_label)
        crop_layout.addWidget(self.select_region_button)
        crop_layout.addWidget(self.clear_region_button)
        crop_layout.addWidget(self.preview_button)
        self._mode_indices["crop"] = self.mode_stack.addWidget(crop_page)
        resize_page = QWidget()
        resize_form = QFormLayout(resize_page)
        resize_form.addRow("Width", self.width_spin)
        resize_form.addRow("Height", self.height_spin)
        resize_form.addRow(self.aspect_lock)
        self.resize_interpolation_combo = self.interpolation_combo
        resize_form.addRow("Interpolation", self.resize_interpolation_combo)
        self.resize_preview_button = QPushButton("Preview Resize")
        resize_form.addRow(self.resize_preview_button)
        self._mode_indices["resize"] = self.mode_stack.addWidget(resize_page)
        rotate_page = QWidget()
        rotate_form = QFormLayout(rotate_page)
        rotate_form.addRow("Angle", self.angle_spin)
        rotate_form.addRow(self.rotate_minus_90_button, self.rotate_plus_90_button)
        rotate_form.addRow(self.rotate_180_button)
        rotate_form.addRow("Canvas", self.canvas_combo)
        self.rotation_interpolation_combo = QComboBox()
        for interpolation in (
            InterpolationMode.NEAREST,
            InterpolationMode.LINEAR,
            InterpolationMode.CUBIC,
        ):
            self.rotation_interpolation_combo.addItem(interpolation.value.title(), interpolation)
        rotate_form.addRow("Interpolation", self.rotation_interpolation_combo)
        self.rotate_preview_button = QPushButton("Preview Rotate")
        rotate_form.addRow(self.rotate_preview_button)
        self._mode_indices["rotate"] = self.mode_stack.addWidget(rotate_page)
        flip_page = QWidget()
        flip_layout = QFormLayout(flip_page)
        flip_layout.addRow("Direction", self.flip_combo)
        self.flip_preview_button = QPushButton("Preview Flip")
        flip_layout.addRow(self.flip_preview_button)
        self._mode_indices["flip"] = self.mode_stack.addWidget(flip_page)
        region_page = QWidget()
        region_layout = QVBoxLayout(region_page)
        self.region_instructions = QLabel("Drag on the image to select a reusable region.")
        self.region_page_label = QLabel("No region selected")
        region_layout.addWidget(self.region_instructions)
        region_layout.addWidget(self.region_page_label)
        self.region_select_button = QPushButton("Select/Reselect")
        self.region_clear_button = QPushButton("Clear")
        region_layout.addWidget(self.region_select_button)
        region_layout.addWidget(self.region_clear_button)
        region_layout.addWidget(self.finish_button)
        self._mode_indices["select_region"] = self.mode_stack.addWidget(region_page)
        layout.addWidget(self.mode_stack)
        layout.addWidget(self.apply_button)
        layout.addWidget(self.clear_preview_button)
        layout.addWidget(self.cancel_button)
        layout.addStretch()
        self.mode = "crop"
        self._ratio = 1.0
        self._updating = False
        self.select_region_button.clicked.connect(self.select_region_requested)
        self.clear_region_button.clicked.connect(self.clear_region_requested)
        self.apply_button.clicked.connect(self.apply_preview_requested)
        self.clear_preview_button.clicked.connect(self.clear_preview_requested)
        self.finish_button.clicked.connect(self.finish_region_requested)
        self.cancel_button.clicked.connect(self.cancel_utility_requested)
        self.preview_button.clicked.connect(self._emit_preview)
        self.resize_preview_button.clicked.connect(self._emit_preview)
        self.rotate_preview_button.clicked.connect(self._emit_preview)
        self.flip_preview_button.clicked.connect(self._emit_preview)
        self.region_select_button.clicked.connect(self.select_region_requested)
        self.region_clear_button.clicked.connect(self.clear_region_requested)
        self.rotate_minus_90_button.clicked.connect(lambda: self.angle_spin.setValue(-90))
        self.rotate_plus_90_button.clicked.connect(lambda: self.angle_spin.setValue(90))
        self.rotate_180_button.clicked.connect(lambda: self.angle_spin.setValue(180))
        self.width_spin.valueChanged.connect(self._width_changed)
        self.height_spin.valueChanged.connect(self._height_changed)
        self.set_preview_available(False)

    def configure(self, mode: str, asset: ImageAsset, region: RectangularRegion | None) -> None:
        self.mode = mode
        self.mode_stack.setCurrentIndex(self._mode_indices[mode])
        self.heading.setText(mode.replace("_", " ").title())
        self._ratio = asset.width / asset.height
        self._updating = True
        self.width_spin.setValue(asset.width)
        self.height_spin.setValue(asset.height)
        self._updating = False
        binary = asset.colour_model is ColourModel.BINARY
        for combo in (self.resize_interpolation_combo, self.rotation_interpolation_combo):
            combo.setCurrentIndex(0 if binary else 1)
            combo.setEnabled(not binary)
        self.apply_button.setVisible(mode != "select_region")
        self.clear_preview_button.setVisible(mode != "select_region")
        self.set_region(region)
        self.set_preview_available(False)

    def set_region(self, region: RectangularRegion | None) -> None:
        self.region_label.setText(
            "No region selected"
            if region is None
            else f"x={region.x}, y={region.y}, {region.width} × {region.height}"  # noqa: RUF001
        )
        self.region_page_label.setText(self.region_label.text())
        if self.mode == "crop":
            self.preview_button.setEnabled(region is not None)

    def set_preview_available(self, available: bool) -> None:
        self.apply_button.setEnabled(available)
        self.clear_preview_button.setEnabled(available)

    def _emit_preview(self) -> None:
        if self.mode == "crop":
            self.preview_crop_requested.emit()
        elif self.mode == "resize":
            self.preview_resize_requested.emit(
                self.width_spin.value(),
                self.height_spin.value(),
                self.resize_interpolation_combo.currentData(),
            )
        elif self.mode == "rotate":
            self.preview_rotate_requested.emit(
                self.angle_spin.value(),
                self.canvas_combo.currentData(),
                self.rotation_interpolation_combo.currentData(),
            )
        elif self.mode == "flip":
            self.preview_flip_requested.emit(self.flip_combo.currentData())

    def _width_changed(self, value: int) -> None:
        if self.aspect_lock.isChecked() and not self._updating:
            self._updating = True
            self.height_spin.setValue(max(1, round(value / self._ratio)))
            self._updating = False

    def _height_changed(self, value: int) -> None:
        if self.aspect_lock.isChecked() and not self._updating:
            self._updating = True
            self.width_spin.setValue(max(1, round(value * self._ratio)))
            self._updating = False
