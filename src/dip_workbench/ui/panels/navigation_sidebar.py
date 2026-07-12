"""Registry-driven accordion navigation and operation search."""

from collections.abc import Callable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from dip_workbench.operations import MODULE_NAMES, ModuleId, OperationDefinition, OperationRegistry


class NavigationSidebar(QWidget):
    operation_selected = Signal(object)
    MINIMUM_WIDTH = 220
    COLLAPSED_WIDTH = 64

    def __init__(
        self,
        show_home: Callable[[], None],
        registry: OperationRegistry,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.registry = registry
        self._show_home = show_home
        self._collapsed = False
        self._expanded_module = ModuleId.M03
        self._active_operation: str | None = None
        self.module_buttons: dict[ModuleId, QPushButton] = {}
        self.module_contents: dict[ModuleId, QWidget] = {}
        self.operation_buttons: dict[str, QPushButton] = {}
        self.collapsed_module_buttons: dict[ModuleId, QPushButton] = {}
        self.setMinimumWidth(self.MINIMUM_WIDTH)
        self.setStyleSheet("background: #f1f5f9;")
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.home_button = QPushButton("Home")
        self.home_button.clicked.connect(show_home)
        self.collapse_button = QPushButton("<")
        self.collapse_button.setFixedWidth(34)
        self.collapse_button.clicked.connect(self.toggle_collapsed)
        top.addWidget(self.home_button, 1)
        top.addWidget(self.collapse_button)
        layout.addLayout(top)
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Search operations…")
        self.search_field.textChanged.connect(self._search)
        layout.addWidget(self.search_field)
        self.content_stack = QStackedWidget()
        self.accordion_page = QWidget()
        self.accordion_layout = QVBoxLayout(self.accordion_page)
        self.search_page = QWidget()
        self.search_layout = QVBoxLayout(self.search_page)
        self.collapsed_page = QWidget()
        self.collapsed_layout = QVBoxLayout(self.collapsed_page)
        self._build_modules()
        for page in (self.accordion_page, self.search_page, self.collapsed_page):
            page.layout().addStretch()  # type: ignore[union-attr]
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.content_stack.addWidget(scroll)
        layout.addWidget(self.content_stack, 1)
        self.expand_module(ModuleId.M03)

    @property
    def is_collapsed(self) -> bool:
        return self._collapsed

    @property
    def expanded_module(self) -> ModuleId:
        return self._expanded_module

    def _build_modules(self) -> None:
        for module_id in ModuleId:
            button = QPushButton(f"{module_id.value[1:]} {MODULE_NAMES[module_id]}")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=module_id: self.expand_module(value))
            self.module_buttons[module_id] = button
            self.accordion_layout.addWidget(button)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            operations = self.registry.by_module(module_id)
            if not operations:
                empty = QLabel("No registered tools yet.")
                empty.setStyleSheet("color: #64748b; padding-left: 12px;")
                content_layout.addWidget(empty)
            for definition in operations:
                operation = QPushButton(f"{definition.id} {definition.display_name}")
                operation.clicked.connect(
                    lambda checked=False, item=definition: self.operation_selected.emit(item)
                )
                self.operation_buttons[str(definition.id)] = operation
                content_layout.addWidget(operation)
            self.module_contents[module_id] = content
            self.accordion_layout.addWidget(content)
            number = QPushButton(module_id.value[1:])
            number.setToolTip(MODULE_NAMES[module_id])
            number.clicked.connect(
                lambda checked=False, value=module_id: self._collapsed_module(value)
            )
            self.collapsed_module_buttons[module_id] = number
            self.collapsed_layout.addWidget(number)

    def expand_module(self, module_id: ModuleId) -> None:
        self._expanded_module = module_id
        for value, content in self.module_contents.items():
            expanded = value is module_id
            content.setVisible(expanded)
            self.module_buttons[value].setChecked(expanded)
        if not self._collapsed and not self.search_field.text():
            self.content_stack.setCurrentIndex(0)

    def set_active_operation(self, definition: OperationDefinition | None) -> None:
        self._active_operation = str(definition.id) if definition is not None else None
        if definition is not None:
            self.expand_module(definition.module_id)
        for operation_id, button in self.operation_buttons.items():
            active = operation_id == self._active_operation
            button.setStyleSheet(
                "QPushButton { border-left: 4px solid #2563eb; background: #dbeafe; font-weight: 700; }"
                if active
                else ""
            )
        active_module = definition.module_id if definition is not None else None
        for module_id in ModuleId:
            active = module_id is active_module
            style = (
                "QPushButton { background: #dbeafe; color: #1d4ed8; font-weight: 700; }"
                if active
                else ""
            )
            self.module_buttons[module_id].setStyleSheet(style)
            self.collapsed_module_buttons[module_id].setStyleSheet(style)

    def _search(self, text: str) -> None:
        if self._collapsed:
            return
        while self.search_layout.count() > 1:
            item = self.search_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        term = text.strip().casefold()
        if not term:
            self.content_stack.setCurrentIndex(0)
            return
        found = {item.id: item for item in self.registry.search(term)}
        for module_id in ModuleId:
            if term in MODULE_NAMES[module_id].casefold():
                found.update({item.id: item for item in self.registry.by_module(module_id)})
        for module_id in ModuleId:
            matches = [item for item in found.values() if item.module_id is module_id]
            if not matches:
                continue
            heading = QLabel(f"{module_id.value[1:]} {MODULE_NAMES[module_id]}")
            heading.setStyleSheet("font-weight: 600;")
            self.search_layout.insertWidget(self.search_layout.count() - 1, heading)
            for definition in sorted(matches, key=lambda item: item.id.value):
                button = QPushButton(f"{definition.id} {definition.display_name}")
                button.clicked.connect(
                    lambda checked=False, item=definition: self.operation_selected.emit(item)
                )
                self.search_layout.insertWidget(self.search_layout.count() - 1, button)
        self.content_stack.setCurrentIndex(1)

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.search_field.setVisible(not collapsed)
        self.home_button.setText("⌂" if collapsed else "Home")
        self.collapse_button.setText(">" if collapsed else "<")
        self.setMinimumWidth(self.COLLAPSED_WIDTH if collapsed else self.MINIMUM_WIDTH)
        self.setMaximumWidth(self.COLLAPSED_WIDTH if collapsed else 16_777_215)
        self.content_stack.setCurrentIndex(
            2 if collapsed else (1 if self.search_field.text() else 0)
        )

    def _collapsed_module(self, module_id: ModuleId) -> None:
        self.set_collapsed(False)
        self.expand_module(module_id)

    def focus_search(self) -> None:
        self.set_collapsed(False)
        self.search_field.setFocus(Qt.FocusReason.ShortcutFocusReason)
        self.search_field.selectAll()
