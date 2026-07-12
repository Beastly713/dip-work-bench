"""Custom parameter and result interfaces for M03-01."""

from collections.abc import Mapping

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ImageAsset
from dip_workbench.operations import OperationResult
from dip_workbench.ui.panels import OperationParameterEditor
from dip_workbench.ui.widgets.image_canvas import ImageCanvas
from dip_workbench.ui.widgets.operation_result_presenter import OperationResultPresenter


class ImageNegativeParameterEditor(OperationParameterEditor):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QFormLayout(self)
        self.colour_handling_combo = QComboBox()
        for label, value in (
            ("Luminance only", "luminance"),
            ("Each RGB channel", "channels"),
            ("Grayscale output", "grayscale"),
        ):
            self.colour_handling_combo.addItem(label, value)
        self.error_label = QLabel()
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("color: #b91c1c;")
        layout.addRow("Colour Handling", self.colour_handling_combo)
        layout.addRow(self.error_label)
        self.colour_handling_combo.currentIndexChanged.connect(self._emit_values)

    def _emit_values(self) -> None:
        self.values_changed.emit({"colour_handling": self.colour_handling_combo.currentData()})

    def set_values(self, values: Mapping[str, object]) -> None:
        index = self.colour_handling_combo.findData(values.get("colour_handling"))
        self.colour_handling_combo.blockSignals(True)
        self.colour_handling_combo.setCurrentIndex(max(index, 0))
        self.colour_handling_combo.blockSignals(False)

    def set_validation_errors(self, errors: Mapping[str, str]) -> None:
        self.error_label.setText(errors.get("colour_handling", ""))


class NegativeCurveWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(170)

    def paintEvent(self, event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        area = QRectF(self.rect()).adjusted(34, 12, -16, -28)
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        painter.drawLine(area.bottomLeft(), area.topLeft())
        painter.drawLine(area.bottomLeft(), area.bottomRight())
        painter.setPen(QPen(QColor("#2563eb"), 2))
        painter.drawLine(QPointF(area.left(), area.top()), QPointF(area.right(), area.bottom()))
        painter.setPen(QColor("#475569"))
        painter.drawText(4, int(area.top() + 5), "255")
        painter.drawText(int(area.right() - 8), int(area.bottom() + 20), "255")
        painter.drawText(18, int(area.bottom() + 20), "0")


class ImageNegativeResultPresenter(OperationResultPresenter):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        comparison = QHBoxLayout()
        self.input_canvas = ImageCanvas()
        self.result_canvas = ImageCanvas()
        for title, canvas in (
            ("Input", self.input_canvas),
            ("Negative Result", self.result_canvas),
        ):
            column = QVBoxLayout()
            label = QLabel(title)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-weight: 600;")
            buttons = QHBoxLayout()
            fit = QPushButton("Fit")
            actual = QPushButton("100%")
            fit.clicked.connect(canvas.fit_to_view)
            actual.clicked.connect(canvas.show_actual_size)
            buttons.addWidget(fit)
            buttons.addWidget(actual)
            column.addWidget(label)
            column.addLayout(buttons)
            column.addWidget(canvas)
            comparison.addLayout(column)
        layout.addLayout(comparison, 1)
        self.mapping_toggle = QToolButton()
        self.mapping_toggle.setText("Input–Output Mapping")  # noqa: RUF001
        self.mapping_toggle.setCheckable(True)
        self.mapping_toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.mapping_curve = NegativeCurveWidget()
        self.mapping_curve.hide()
        self.mapping_toggle.toggled.connect(self._toggle_mapping)
        layout.addWidget(self.mapping_toggle)
        layout.addWidget(self.mapping_curve)
        self._synchronise_canvases()

    def _toggle_mapping(self, visible: bool) -> None:
        self.mapping_toggle.setArrowType(
            Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow
        )
        self.mapping_curve.setVisible(visible)

    def _synchronise_canvases(self) -> None:
        self.input_canvas.zoom_changed.connect(self.result_canvas.set_zoom_percent)
        self.result_canvas.zoom_changed.connect(self.input_canvas.set_zoom_percent)
        for first, second in (
            (self.input_canvas, self.result_canvas),
            (self.result_canvas, self.input_canvas),
        ):
            first.horizontalScrollBar().valueChanged.connect(second.horizontalScrollBar().setValue)
            first.verticalScrollBar().valueChanged.connect(second.verticalScrollBar().setValue)

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        output = result.primary_artifact.data
        if not isinstance(output, ImageAsset):
            self.clear_result()
            return
        self.input_canvas.set_image(input_asset)
        self.result_canvas.set_image(output)

    def clear_result(self) -> None:
        self.input_canvas.clear_image()
        self.result_canvas.clear_image()
        self.mapping_toggle.setChecked(False)
