"""DIP Workbench home page."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ModuleId, OperationDefinition, OperationRegistry
from dip_workbench.ui.widgets.module_card import ModuleCard


class HomePage(QWidget):
    """Present primary-image opening and current-document choices."""

    module_requested = Signal(object)
    recent_operation_requested = Signal(object)

    def __init__(self, registry: OperationRegistry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(48, 42, 48, 42)
        layout.setSpacing(16)

        title = QLabel("DIP Workbench")
        title.setObjectName("pageTitle")
        title.setStyleSheet("font-size: 28px; font-weight: 600; color: #1f2937;")
        description = QLabel(
            "Demonstrate, compare, and document syllabus-based image-processing operations."
        )
        description.setStyleSheet("font-size: 15px; color: #4b5563;")

        buttons = QHBoxLayout()
        self.open_image_button = QPushButton("Open Image")
        self.sample_image_button = QPushButton("Use Sample Image")
        self.open_image_button.clicked.connect(self.open_image_requested)
        self.sample_image_button.setEnabled(False)
        buttons.addWidget(self.open_image_button)
        buttons.addWidget(self.sample_image_button)
        buttons.addStretch()

        drop_area = QFrame()
        drop_area.setObjectName("dropArea")
        drop_area.setMinimumHeight(160)
        drop_area.setStyleSheet(
            "QFrame#dropArea { background: #1f2937; border: 1px dashed #94a3b8; "
            "border-radius: 6px; }"
        )
        drop_layout = QVBoxLayout(drop_area)
        drop_label = QLabel("Drag and Drop Image Here")
        drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_label.setStyleSheet("color: #d1d5db; font-size: 15px;")
        drop_layout.addWidget(drop_label)

        empty_message = QLabel("No image loaded. Open an image or drag one here to begin.")
        self.empty_message_label = empty_message
        empty_message.setStyleSheet("color: #6b7280;")

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addLayout(buttons)
        layout.addWidget(drop_area, 1)
        layout.addWidget(empty_message)

        self.current_document = QFrame()
        current_layout = QHBoxLayout(self.current_document)
        self.current_document_label = QLabel()
        self.continue_button = QPushButton("Continue with Current Image")
        self.continue_button.clicked.connect(self.continue_requested)
        current_layout.addWidget(self.current_document_label, 1)
        current_layout.addWidget(self.continue_button)
        self.current_document.hide()
        layout.addWidget(self.current_document)

        modules_heading = QLabel("Academic Modules")
        modules_heading.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(modules_heading)
        module_host = QWidget()
        module_layout = QGridLayout(module_host)
        self.module_cards: dict[ModuleId, ModuleCard] = {}
        for index, module_id in enumerate(ModuleId):
            card = ModuleCard(module_id, registry.by_module(module_id))
            card.clicked.connect(self.module_requested)
            self.module_cards[module_id] = card
            module_layout.addWidget(card, index // 3, index % 3)
        module_scroll = QScrollArea()
        module_scroll.setWidgetResizable(True)
        module_scroll.setMinimumHeight(210)
        module_scroll.setWidget(module_host)
        layout.addWidget(module_scroll)

        self.recent_frame = QFrame()
        recent_layout = QVBoxLayout(self.recent_frame)
        recent_heading = QLabel("Recently Used Operations")
        recent_heading.setStyleSheet("font-size: 17px; font-weight: 600;")
        recent_layout.addWidget(recent_heading)
        self.recent_layout = QVBoxLayout()
        recent_layout.addLayout(self.recent_layout)
        self.recent_frame.hide()
        layout.addWidget(self.recent_frame)

    def set_current_document(self, asset: "ImageAsset | None") -> None:
        if asset is None:
            self.current_document.hide()
            return
        self.current_document_label.setText(
            f"{asset.name} — {asset.width} × {asset.height} • {asset.colour_model.value}"  # noqa: RUF001
        )
        self.current_document.show()

    open_image_requested = Signal()
    continue_requested = Signal()

    def set_recent_operations(self, definitions: tuple[OperationDefinition, ...]) -> None:
        while self.recent_layout.count():
            item = self.recent_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        for definition in definitions:
            button = QPushButton(f"{definition.id} {definition.display_name}")
            button.clicked.connect(
                lambda checked=False, item=definition: self.recent_operation_requested.emit(item)
            )
            self.recent_layout.addWidget(button)
        self.recent_frame.setVisible(bool(definitions))
