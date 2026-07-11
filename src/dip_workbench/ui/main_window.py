"""Single-window desktop application shell."""

from enum import IntEnum

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import QMainWindow, QMenu, QSplitter, QStackedWidget, QToolBar, QWidget

from dip_workbench.services import SettingsService
from dip_workbench.ui.pages import HomePage, OperationWorkspace, ReportBuilderPage
from dip_workbench.ui.panels import NavigationSidebar, ParameterPanel, WorkbenchStatusBar


class PageIndex(IntEnum):
    HOME = 0
    OPERATION = 1
    REPORT = 2


class MainWindow(QMainWindow):
    """Host the persistent DIP Workbench desktop shell."""

    DEFAULT_SIZE = QSize(1440, 900)
    MINIMUM_SIZE = QSize(1180, 720)
    DEFAULT_NAVIGATION_WIDTH = 270
    DEFAULT_PARAMETER_WIDTH = 320

    def __init__(self, settings: SettingsService, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.action_map: dict[str, QAction] = {}
        self.setWindowTitle("DIP Workbench")
        self.setMinimumSize(self.MINIMUM_SIZE)
        self.resize(self.DEFAULT_SIZE)

        self.page_stack = QStackedWidget()
        self.home_page = HomePage()
        self.operation_workspace = OperationWorkspace()
        self.report_builder_page = ReportBuilderPage(self.show_home_page)
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.operation_workspace)
        self.page_stack.addWidget(self.report_builder_page)

        self.navigation_sidebar = NavigationSidebar(self.show_home_page)
        self.parameter_panel = ParameterPanel()
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.addWidget(self.navigation_sidebar)
        self.main_splitter.addWidget(self.page_stack)
        self.main_splitter.addWidget(self.parameter_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setStretchFactor(2, 0)
        self.setCentralWidget(self.main_splitter)

        self._navigation_width = self._read_width(
            "layout/navigation_width",
            self.DEFAULT_NAVIGATION_WIDTH,
            NavigationSidebar.MINIMUM_WIDTH,
        )
        self._parameter_width = self._read_width(
            "layout/parameter_width",
            self.DEFAULT_PARAMETER_WIDTH,
            ParameterPanel.MINIMUM_WIDTH,
        )
        self.main_splitter.setSizes([self._navigation_width, 850, self._parameter_width])
        self.main_splitter.splitterMoved.connect(self._remember_panel_widths)

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self.workbench_status_bar = WorkbenchStatusBar()
        self.setStatusBar(self.workbench_status_bar)
        self._restore_geometry()
        self.show_home_page()

    def show_home_page(self) -> None:
        self.page_stack.setCurrentIndex(PageIndex.HOME)

    def show_operation_workspace(self) -> None:
        self.page_stack.setCurrentIndex(PageIndex.OPERATION)

    def show_report_builder(self) -> None:
        self.page_stack.setCurrentIndex(PageIndex.REPORT)

    def _add_action(
        self,
        key: str,
        text: str,
        *,
        enabled: bool = False,
        shortcut: str | None = None,
        checkable: bool = False,
    ) -> QAction:
        action = QAction(text, self)
        action.setEnabled(enabled)
        action.setCheckable(checkable)
        if shortcut is not None:
            action.setShortcut(QKeySequence(shortcut))
        self.action_map[key] = action
        return action

    def _create_actions(self) -> None:
        self._add_action("home", "Home", enabled=True).triggered.connect(self.show_home_page)
        self._add_action("open", "Open Primary Image", shortcut="Ctrl+O")
        self._add_action("sample", "Open Sample Image")
        self._add_action("save", "Save Current Image", shortcut="Ctrl+S")
        self._add_action("export_result", "Export Displayed Result")
        self._add_action("report", "Open Report Builder", enabled=True).triggered.connect(
            self.show_report_builder
        )
        self._add_action("export_report", "Export Report")
        self._add_action("exit", "Exit", enabled=True).triggered.connect(self.close)
        self._add_action("undo", "Undo", shortcut="Ctrl+Z")
        self._add_action("redo", "Redo", shortcut="Ctrl+Y")
        self._add_action("reset", "Reset Current Image")
        self._add_action("clear_preview", "Clear Operation Preview")
        self._add_action("fit", "Fit Image")
        self._add_action("actual_size", "Actual Size")
        self._add_action("zoom_in", "Zoom In")
        self._add_action("zoom_out", "Zoom Out")
        navigation = self._add_action(
            "show_navigation", "Show Navigation", enabled=True, checkable=True
        )
        navigation.setChecked(True)
        navigation.toggled.connect(self.set_navigation_visible)
        parameters = self._add_action(
            "show_parameters", "Show Parameters", enabled=True, checkable=True
        )
        parameters.setChecked(True)
        parameters.toggled.connect(self.set_parameters_visible)
        self._add_action("show_details", "Show Details")
        self._add_action("presentation", "Presentation Mode", shortcut="F11")
        self._add_action("about_operation", "About This Operation")
        self._add_action("shortcuts", "Keyboard Shortcuts")
        self._add_action("about", "About DIP Workbench")
        self._add_action("compare", "Compare")
        self._add_action("add_report", "Add to Report")

    def _create_menus(self) -> None:
        menu_specs = (
            (
                "File",
                ("open", "sample", "save", "export_result", "report", "export_report", "exit"),
            ),
            ("Edit", ("undo", "redo", "reset", "clear_preview")),
            (
                "View",
                (
                    "fit",
                    "actual_size",
                    "zoom_in",
                    "zoom_out",
                    "show_navigation",
                    "show_parameters",
                    "show_details",
                    "presentation",
                ),
            ),
            ("Help", ("about_operation", "shortcuts", "about")),
        )
        self.menus: dict[str, QMenu] = {}
        for title, action_keys in menu_specs:
            menu = self.menuBar().addMenu(title)
            self.menus[title] = menu
            menu.addActions([self.action_map[key] for key in action_keys])

    def _create_toolbar(self) -> None:
        self.global_toolbar = QToolBar("Global Toolbar", self)
        self.global_toolbar.setMovable(False)
        self.global_toolbar.setFixedHeight(54)
        self.global_toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.addToolBar(self.global_toolbar)
        for keys in (
            ("home", "open", "save"),
            ("undo", "redo", "reset"),
            ("compare", "add_report", "export_result"),
            ("presentation",),
        ):
            if self.global_toolbar.actions():
                self.global_toolbar.addSeparator()
            self.global_toolbar.addActions([self.action_map[key] for key in keys])

    def set_navigation_visible(self, visible: bool) -> None:
        if not visible and self.navigation_sidebar.isVisible():
            self._navigation_width = max(
                self.main_splitter.sizes()[0], NavigationSidebar.MINIMUM_WIDTH
            )
        self.navigation_sidebar.setVisible(visible)
        if visible:
            sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([self._navigation_width, max(sizes[1], 1), sizes[2]])

    def set_parameters_visible(self, visible: bool) -> None:
        if not visible and self.parameter_panel.isVisible():
            self._parameter_width = max(self.main_splitter.sizes()[2], ParameterPanel.MINIMUM_WIDTH)
        self.parameter_panel.setVisible(visible)
        if visible:
            sizes = self.main_splitter.sizes()
            self.main_splitter.setSizes([sizes[0], max(sizes[1], 1), self._parameter_width])

    def _remember_panel_widths(self) -> None:
        sizes = self.main_splitter.sizes()
        if self.navigation_sidebar.isVisible() and sizes[0] > 0:
            self._navigation_width = max(sizes[0], NavigationSidebar.MINIMUM_WIDTH)
        if self.parameter_panel.isVisible() and sizes[2] > 0:
            self._parameter_width = max(sizes[2], ParameterPanel.MINIMUM_WIDTH)

    def _read_width(self, key: str, default: int, minimum: int) -> int:
        try:
            value = self.settings.get(key, default, int)
            return max(value, minimum) if value > 0 else default
        except (TypeError, ValueError):
            return default

    def _restore_geometry(self) -> None:
        try:
            geometry = self.settings.get("window/geometry", QByteArray(), QByteArray)
            if not isinstance(geometry, QByteArray) or (
                not geometry.isEmpty() and not self.restoreGeometry(geometry)
            ):
                self.resize(self.DEFAULT_SIZE)
        except (AttributeError, TypeError, ValueError):
            self.resize(self.DEFAULT_SIZE)

    def closeEvent(self, event: QCloseEvent) -> None:
        self._remember_panel_widths()
        self.settings.set("window/geometry", self.saveGeometry())
        self.settings.set("layout/navigation_width", self._navigation_width)
        self.settings.set("layout/parameter_width", self._parameter_width)
        self.settings.sync()
        super().closeEvent(event)
