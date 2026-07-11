"""Persistent image and pixel status bar."""

from PySide6.QtWidgets import QLabel, QStatusBar, QWidget

from dip_workbench.core import ColourModel, ImageAsset


class WorkbenchStatusBar(QStatusBar):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(26)
        self.left_label = QLabel()
        self.centre_label = QLabel()
        self.right_label = QLabel()
        self.addWidget(self.left_label)
        self.addWidget(self.centre_label, 1)
        self.addPermanentWidget(self.right_label)
        self.clear_document_status()

    def clear_document_status(self) -> None:
        self.left_label.setText("No image loaded")
        self.centre_label.clear()
        self.right_label.setText("Ready")

    def set_image_status(self, asset: ImageAsset) -> None:
        names = {
            ColourModel.RGB: "RGB",
            ColourModel.GRAY: "Grayscale",
            ColourModel.BINARY: "Binary",
        }
        self.left_label.setText(
            f"Image: {asset.width} × {asset.height} • {names[asset.colour_model]} • {asset.bit_depth}-bit"  # noqa: RUF001
        )

    def set_pixel_status(self, x: int, y: int, value: object, model: ColourModel) -> None:
        if model is ColourModel.RGB:
            text = f"x: {x}  y: {y}  RGB: {value}"
        elif model is ColourModel.BINARY:
            label = "Foreground" if value == 255 else "Background"
            text = f"x: {x}  y: {y}  Value: {label} ({value})"
        else:
            text = f"x: {x}  y: {y}  Value: {value}"
        self.centre_label.setText(text)

    def clear_pixel_status(self) -> None:
        self.centre_label.clear()

    def set_zoom_status(self, percent: float) -> None:
        self.right_label.setText(f"Zoom: {percent:.0f}%")

    def set_left_status(self, text: str) -> None:
        self.left_label.setText(text)

    def set_centre_status(self, text: str) -> None:
        self.centre_label.setText(text)

    def set_right_status(self, text: str) -> None:
        self.right_label.setText(text)
