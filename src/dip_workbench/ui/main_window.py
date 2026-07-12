"""Single-window desktop application shell."""

import logging
from enum import IntEnum
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QToolBar,
    QWidget,
)

from dip_workbench.controllers import DocumentController, OperationController
from dip_workbench.core import (
    ExportError,
    ImageAsset,
    InputValidationError,
    OperationExecutionError,
    RectangularRegion,
    UnsupportedImageError,
)
from dip_workbench.execution import OperationExecutionManager
from dip_workbench.operations import OperationDefinition, operation_registry
from dip_workbench.services import (
    SettingsService,
)
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

    def __init__(
        self,
        settings: SettingsService,
        document_controller: DocumentController,
        operation_execution: OperationExecutionManager,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.document_controller = document_controller
        self.operation_controller = OperationController(
            document_controller, operation_execution, self
        )
        self.action_map: dict[str, QAction] = {}
        self.setWindowTitle("DIP Workbench")
        self.setMinimumSize(self.MINIMUM_SIZE)
        self.resize(self.DEFAULT_SIZE)
        self.setAcceptDrops(True)

        self.page_stack = QStackedWidget()
        self.home_page = HomePage(operation_registry)
        self.operation_workspace = OperationWorkspace()
        self.report_builder_page = ReportBuilderPage(self.show_home_page)
        self.page_stack.addWidget(self.home_page)
        self.page_stack.addWidget(self.operation_workspace)
        self.page_stack.addWidget(self.report_builder_page)

        self.navigation_sidebar = NavigationSidebar(self.show_home_page, operation_registry)
        self._recent_operations: list[OperationDefinition] = []
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
        self._connect_document_workflow()
        self._connect_operation_workflow()
        self._restore_geometry()
        self.show_home_page()
        self.refresh_document_actions()

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
        self._add_action("open", "Open Primary Image", enabled=True, shortcut="Ctrl+O")
        self._add_action("sample", "Open Sample Image")
        self._add_action("save", "Save Current Image", shortcut="Ctrl+S")
        self._add_action("export_result", "Export Displayed Result")
        self._add_action("image_negative", "M03-01 Image Negative", enabled=True)
        self._add_action("operation_search", "Search Operations", enabled=True, shortcut="Ctrl+K")
        self._add_action("report", "Open Report Builder", enabled=True).triggered.connect(
            self.show_report_builder
        )
        self._add_action("export_report", "Export Report")
        self._add_action("exit", "Exit", enabled=True).triggered.connect(self.close)
        self._add_action("undo", "Undo", shortcut="Ctrl+Z")
        self._add_action("redo", "Redo", shortcut="Ctrl+Y")
        self._add_action("reset", "Reset Current Image")
        self._add_action("clear_preview", "Clear Operation Preview")
        self._add_action("crop", "Crop…")
        self._add_action("resize", "Resize…")
        self._add_action("rotate", "Rotate…")
        self._add_action("flip", "Flip/Mirror…")
        self._add_action("select_region", "Select Region")
        self._add_action("fit", "Fit Image", shortcut="F")
        self._add_action("actual_size", "Actual Size", shortcut="1")
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
            (
                "Edit",
                (
                    "undo",
                    "redo",
                    "reset",
                    "clear_preview",
                    "crop",
                    "resize",
                    "rotate",
                    "flip",
                    "select_region",
                ),
            ),
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
            ("Operations", ("image_negative", "operation_search")),
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

    def _connect_document_workflow(self) -> None:
        self.action_map["open"].triggered.connect(self.open_primary_image_dialog)
        self.action_map["save"].triggered.connect(self.save_current_image_dialog)
        self.action_map["export_result"].triggered.connect(self.export_displayed_result_dialog)
        self.action_map["image_negative"].triggered.connect(
            lambda: self.open_operation(operation_registry.get("M03-01"))
        )
        self.action_map["operation_search"].triggered.connect(self.focus_operation_search)
        self.action_map["undo"].triggered.connect(self.undo_document)
        self.action_map["redo"].triggered.connect(self.redo_document)
        self.action_map["reset"].triggered.connect(self.reset_document)
        canvas = self.operation_workspace.image_canvas
        self.action_map["fit"].triggered.connect(canvas.fit_to_view)
        self.action_map["actual_size"].triggered.connect(canvas.show_actual_size)
        self.action_map["zoom_in"].triggered.connect(canvas.zoom_in)
        self.action_map["zoom_out"].triggered.connect(canvas.zoom_out)
        self.home_page.open_image_requested.connect(self.open_primary_image_dialog)
        self.home_page.continue_requested.connect(self.show_operation_workspace)
        self.home_page.module_requested.connect(self.show_home_module)
        self.home_page.recent_operation_requested.connect(self.open_operation)
        self.navigation_sidebar.operation_selected.connect(self.open_operation)
        self.operation_workspace.open_image_requested.connect(self.open_primary_image_dialog)
        canvas.zoom_changed.connect(self.workbench_status_bar.set_zoom_status)
        canvas.pixel_hovered.connect(self._show_pixel_status)
        canvas.pixel_left.connect(self.workbench_status_bar.clear_pixel_status)
        canvas.file_dropped.connect(self.open_primary_image_path)
        canvas.region_changed.connect(self._region_changed)
        canvas.region_finished.connect(self._region_finished)
        for key in ("crop", "resize", "rotate", "flip", "select_region"):
            self.action_map[key].triggered.connect(
                lambda checked=False, mode=key: self.open_utility(mode)
            )
        utility = self.parameter_panel.utility_panel
        utility.select_region_requested.connect(self.begin_region_selection)
        utility.clear_region_requested.connect(self.clear_region_selection)
        utility.finish_region_requested.connect(canvas.cancel_interaction)
        utility.cancel_utility_requested.connect(self.cancel_utility)
        utility.preview_crop_requested.connect(
            lambda: self._preview_transform(self.document_controller.preview_crop)
        )
        utility.preview_resize_requested.connect(
            lambda w, h, i: self._preview_transform(
                self.document_controller.preview_resize, width=w, height=h, interpolation=i
            )
        )
        utility.preview_rotate_requested.connect(
            lambda a, c, i: self._preview_transform(
                self.document_controller.preview_rotate,
                angle_degrees=a,
                canvas_mode=c,
                interpolation=i,
            )
        )
        utility.preview_flip_requested.connect(
            lambda d: self._preview_transform(self.document_controller.preview_flip, direction=d)
        )
        utility.apply_preview_requested.connect(self.apply_utility_preview)
        utility.clear_preview_requested.connect(self.clear_utility_preview)
        self.action_map["clear_preview"].triggered.connect(self.clear_active_preview)

    def _connect_operation_workflow(self) -> None:
        inputs = self.operation_workspace.operation_input_strip
        result = self.operation_workspace.result_workspace
        panel = self.parameter_panel.operation_panel
        inputs.source_changed.connect(self.operation_controller.set_input_source)
        inputs.open_image_requested.connect(self.open_primary_image_dialog)
        result.open_image_requested.connect(self.open_primary_image_dialog)
        result.cancel_requested.connect(self.operation_controller.cancel)
        panel.parameter_values_changed.connect(self.operation_controller.parameter_values_changed)
        panel.preview_requested.connect(self.operation_controller.preview_or_run)
        panel.apply_requested.connect(self.operation_controller.apply)
        panel.reset_requested.connect(self.operation_controller.reset_parameters)
        panel.apply_candidate_changed.connect(self.operation_controller.set_apply_candidate)
        self.operation_controller.changed.connect(self._refresh_operation_workspace)
        self.operation_controller.image_applied.connect(self._academic_image_applied)
        inputs.load_image_requested.connect(self.load_additional_image_dialog)
        inputs.clear_input_requested.connect(self.operation_controller.clear_additional_input)

    def open_operation(self, definition: OperationDefinition) -> None:
        preview = self.document_controller.document_store.active_preview
        if preview is not None and preview.operation_id in {"U-05", "U-06", "U-07", "U-08"}:
            self.clear_utility_preview()
        elif preview is not None:
            self.document_controller.clear_active_preview()
        self.operation_workspace.image_canvas.cancel_interaction()
        self.operation_controller.select_operation(definition)
        self.navigation_sidebar.set_active_operation(definition)
        self._recent_operations = [
            definition,
            *(item for item in self._recent_operations if item.id != definition.id),
        ][:5]
        self.home_page.set_recent_operations(tuple(self._recent_operations))
        self.operation_workspace.show_academic_operation(self.operation_controller)
        self.parameter_panel.operation_panel.configure(self.operation_controller)
        self.parameter_panel.show_operation_panel()
        self.show_operation_workspace()

    def focus_operation_search(self) -> None:
        self.action_map["show_navigation"].setChecked(True)
        self.navigation_sidebar.show()
        self.navigation_sidebar.focus_search()

    def show_home_module(self, module_id: object) -> None:
        from dip_workbench.operations import ModuleId

        if not isinstance(module_id, ModuleId):
            return
        self.action_map["show_navigation"].setChecked(True)
        self.navigation_sidebar.set_collapsed(False)
        self.navigation_sidebar.expand_module(module_id)
        self.show_home_page()

    def load_additional_image_dialog(self, key: str) -> None:
        definition = self.operation_controller.active_definition
        if definition is None or not any(item.key == key for item in definition.input_spec):
            return
        initial = self._initial_directory("paths/last_open_directory")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Operation Input",
            str(initial),
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        )
        if not path:
            return
        try:
            asset = self.document_controller.image_io.load(path)
        except (InputValidationError, UnsupportedImageError, OperationExecutionError) as error:
            self._show_open_error(str(error))
            return
        self.operation_controller.set_additional_input(key, asset)
        self.settings.set("paths/last_open_directory", str(Path(path).parent))
        self.settings.sync()

    def _refresh_operation_workspace(self) -> None:
        if (
            self.operation_workspace.mode_stack.currentWidget()
            is self.operation_workspace.academic_view
        ):
            self.operation_workspace.refresh_academic_operation(self.operation_controller)
            self.parameter_panel.operation_panel.refresh(self.operation_controller)
        self.refresh_document_actions()

    def _academic_image_applied(self, asset: ImageAsset) -> None:
        self._display_document(asset, fit=True)
        self.operation_workspace.show_academic_operation(self.operation_controller)
        self.parameter_panel.show_operation_panel()

    def clear_active_preview(self) -> None:
        if (
            self.operation_workspace.mode_stack.currentWidget()
            is self.operation_workspace.academic_view
        ):
            self.operation_controller.clear_result()
        else:
            self.clear_utility_preview()

    def refresh_document_actions(self) -> None:
        active = self.document_controller.has_document
        for key in ("save", "reset", "fit", "actual_size", "zoom_in", "zoom_out"):
            self.action_map[key].setEnabled(active)
        for key in ("crop", "resize", "rotate", "flip", "select_region"):
            self.action_map[key].setEnabled(active)
        self.action_map["undo"].setEnabled(self.document_controller.can_undo)
        self.action_map["redo"].setEnabled(self.document_controller.can_redo)
        self.action_map["clear_preview"].setEnabled(
            self.document_controller.document_store.active_preview is not None
        )
        result = self.operation_controller.active_result
        academic_image = result is not None and isinstance(result.primary_artifact.data, ImageAsset)
        self.action_map["export_result"].setEnabled(active or academic_image)

    def open_primary_image_dialog(self) -> None:
        initial = self._initial_directory("paths/last_open_directory")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Primary Image",
            str(initial),
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff);;PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tif *.tiff)",
        )
        if path:
            self.open_primary_image_path(path)

    def open_primary_image_path(self, path: str | Path) -> bool:
        candidate = Path(path)
        if candidate.suffix.lower() not in self.document_controller.image_io.SUPPORTED_EXTENSIONS:
            return False
        if self.document_controller.has_document and not self._confirm_replacement():
            return False
        try:
            asset = self.document_controller.open_primary_image(candidate)
        except (InputValidationError, UnsupportedImageError, OperationExecutionError) as error:
            self._show_open_error(str(error))
            return False
        except Exception:
            logging.getLogger("dip_workbench").exception("Unexpected image-open failure")
            self._show_open_error("An unexpected error occurred.")
            return False
        self.settings.set("paths/last_open_directory", str(candidate.parent))
        self.settings.sync()
        self._display_document(asset, fit=True)
        self.setWindowTitle(f"DIP Workbench — {candidate.name}")
        self.show_operation_workspace()
        self.parameter_panel.utility_panel.set_preview_available(False)
        self.parameter_panel.show_placeholder()
        self.operation_controller.document_changed()
        if self.operation_controller.active_definition is not None:
            self.operation_workspace.show_academic_operation(self.operation_controller)
            self.parameter_panel.operation_panel.configure(self.operation_controller)
            self.parameter_panel.show_operation_panel()
        else:
            self.operation_workspace.show_document_view()
        return True

    def save_current_image_dialog(self) -> None:
        asset = self.document_controller.current_image
        if asset is None:
            return
        stem = Path(asset.name).stem
        if not stem.endswith("-result"):
            stem += "-result"
        suggestion = self._initial_directory("paths/last_export_directory") / f"{stem}.png"
        filters = "PNG (*.png);;BMP (*.bmp);;TIFF (*.tif *.tiff)"
        if asset.colour_model.value != "BINARY":
            filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tif *.tiff)"
        path, selected = QFileDialog.getSaveFileName(
            self, "Save Current Image", str(suggestion), filters
        )
        if path:
            destination = Path(path)
            if not destination.suffix:
                extensions = {"JPEG": ".jpg", "BMP": ".bmp", "TIFF": ".tiff"}
                destination = destination.with_suffix(
                    next(
                        (ext for name, ext in extensions.items() if selected.startswith(name)),
                        ".png",
                    )
                )
            self.save_current_image_path(destination)

    def save_current_image_path(self, path: str | Path) -> bool:
        destination = Path(path)
        if not destination.suffix:
            destination = destination.with_suffix(".png")
        try:
            self.document_controller.save_current_image(destination)
        except (InputValidationError, ExportError) as error:
            self._show_save_error(str(error))
            return False
        except Exception:
            logging.getLogger("dip_workbench").exception("Unexpected image-save failure")
            self._show_save_error("An unexpected error occurred.")
            return False
        self.settings.set("paths/last_export_directory", str(destination.parent))
        self.settings.sync()
        self.workbench_status_bar.showMessage("Current image saved.", 3000)
        return True

    def export_displayed_result_dialog(self) -> None:
        asset = self._displayed_export_asset()
        if asset is None:
            return
        suggestion = (
            self._initial_directory("paths/last_export_directory") / f"{Path(asset.name).stem}.png"
        )
        filters = "PNG (*.png);;BMP (*.bmp);;TIFF (*.tif *.tiff)"
        if asset.colour_model.value != "BINARY":
            filters = "PNG (*.png);;JPEG (*.jpg *.jpeg);;BMP (*.bmp);;TIFF (*.tif *.tiff)"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Displayed Result", str(suggestion), filters
        )
        if path:
            self.export_displayed_result_path(path)

    def export_displayed_result_path(self, path: str | Path) -> bool:
        asset = self._displayed_export_asset()
        if asset is None:
            self._show_save_error("No image result is available to export.")
            return False
        destination = Path(path)
        if not destination.suffix:
            destination = destination.with_suffix(".png")
        try:
            self.document_controller.image_io.save(asset, destination)
        except (InputValidationError, ExportError) as error:
            self._show_save_error(str(error))
            return False
        self.settings.set("paths/last_export_directory", str(destination.parent))
        self.settings.sync()
        self.workbench_status_bar.showMessage("Displayed result exported.", 3000)
        return True

    def _displayed_export_asset(self) -> ImageAsset | None:
        result = self.operation_controller.active_result
        if result is not None and isinstance(result.primary_artifact.data, ImageAsset):
            return result.primary_artifact.data
        return self.document_controller.current_image

    def undo_document(self) -> None:
        self._run_history_action(self.document_controller.undo)

    def redo_document(self) -> None:
        self._run_history_action(self.document_controller.redo)

    def reset_document(self) -> None:
        self._run_history_action(self.document_controller.reset_to_original)

    def _run_history_action(self, action) -> None:  # type: ignore[no-untyped-def]
        try:
            restored = action()
        except (InputValidationError, OperationExecutionError):
            return
        self.document_controller.clear_active_preview()
        self.document_controller.clear_selected_region()
        canvas = self.operation_workspace.image_canvas
        canvas.clear_region_selection()
        canvas.cancel_interaction()
        self.parameter_panel.utility_panel.set_preview_available(False)
        self.parameter_panel.show_placeholder()
        self._display_document(restored, fit=False)
        self.operation_controller.document_changed()
        if self.operation_controller.active_definition is not None:
            self.operation_workspace.show_academic_operation(self.operation_controller)
            self.parameter_panel.operation_panel.refresh(self.operation_controller)
            self.parameter_panel.show_operation_panel()

    def _display_document(self, asset: ImageAsset, *, fit: bool) -> None:
        old = self.operation_workspace.image_canvas.current_asset
        self.operation_workspace.set_image(asset)
        if not fit and old is not None and old.shape == asset.shape:
            self.operation_workspace.image_canvas.show_actual_size()
        self.home_page.set_current_document(asset)
        self.workbench_status_bar.set_image_status(asset)
        self.workbench_status_bar.clear_pixel_status()
        self.refresh_document_actions()

    def _show_pixel_status(self, x: int, y: int, value: object) -> None:
        asset = self.operation_workspace.image_canvas.current_asset
        if asset is not None:
            self.workbench_status_bar.set_pixel_status(x, y, value, asset.colour_model)

    def open_utility(self, mode: str) -> None:
        asset = self.document_controller.current_image
        if asset is None:
            return
        self.operation_controller.clear_operation()
        self.navigation_sidebar.set_active_operation(None)
        self.operation_workspace.show_document_view()
        if self.document_controller.document_store.active_preview is not None:
            self.clear_utility_preview()
        self.parameter_panel.utility_panel.configure(
            mode, asset, self.document_controller.selected_region
        )
        self.parameter_panel.show_utility_panel()
        if mode in {"crop", "select_region"}:
            self.begin_region_selection()
        else:
            self.operation_workspace.image_canvas.cancel_interaction()

    def begin_region_selection(self) -> None:
        self.operation_workspace.image_canvas.begin_rectangle_selection(
            self.document_controller.selected_region
        )

    def _region_changed(self, region: object) -> None:
        if isinstance(region, RectangularRegion):
            self.parameter_panel.utility_panel.set_region(region)

    def _region_finished(self, region: object) -> None:
        if isinstance(region, RectangularRegion):
            self.document_controller.set_selected_region(region)
            self.parameter_panel.utility_panel.set_region(region)

    def clear_region_selection(self) -> None:
        self.document_controller.clear_selected_region()
        self.operation_workspace.image_canvas.clear_region_selection()
        self.parameter_panel.utility_panel.set_region(None)

    def _preview_transform(self, callback, **kwargs) -> None:  # type: ignore[no-untyped-def]
        try:
            preview = callback(**kwargs)
        except (InputValidationError, OperationExecutionError) as error:
            QMessageBox.warning(self, "Could Not Transform Image", str(error))
            return
        operation_name = str(preview.metadata["utility_operation_name"])
        self.operation_workspace.set_preview_image(preview, operation_name)
        self.workbench_status_bar.set_preview_image_status(preview)
        self.parameter_panel.utility_panel.set_preview_available(True)
        self.refresh_document_actions()

    def apply_utility_preview(self) -> None:
        try:
            asset = self.document_controller.apply_active_preview()
        except (InputValidationError, OperationExecutionError) as error:
            QMessageBox.warning(self, "Could Not Transform Image", str(error))
            return
        self.operation_workspace.image_canvas.cancel_interaction()
        self.operation_workspace.image_canvas.clear_region_selection()
        self.parameter_panel.utility_panel.set_preview_available(False)
        self._display_document(asset, fit=True)
        self.operation_controller.document_changed()

    def clear_utility_preview(self) -> None:
        self.document_controller.clear_active_preview()
        current = self.document_controller.current_image
        if current is not None:
            self.operation_workspace.show_current_image(current)
            self.workbench_status_bar.set_image_status(current)
            region = self.document_controller.selected_region
            if region is not None and region.fits_within(current.width, current.height):
                self.operation_workspace.image_canvas.set_selected_region(region)
            if self.parameter_panel.utility_panel.mode in {"crop", "select_region"}:
                self.operation_workspace.image_canvas.begin_rectangle_selection(region)
        self.parameter_panel.utility_panel.set_preview_available(False)
        self.refresh_document_actions()

    def cancel_utility(self) -> None:
        self.clear_utility_preview()
        self.operation_workspace.image_canvas.cancel_interaction()
        current = self.document_controller.current_image
        region = self.document_controller.selected_region
        if (
            current is not None
            and region is not None
            and region.fits_within(current.width, current.height)
        ):
            self.operation_workspace.image_canvas.set_selected_region(region)
        self.parameter_panel.show_placeholder()

    def _confirm_replacement(self) -> bool:
        answer = QMessageBox.question(
            self,
            "Replace Current Image",
            "Replace the current image?\n\nOpening a new primary image will clear the current undo/redo history and document-specific state.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        return answer == QMessageBox.StandardButton.Yes

    def _show_open_error(self, message: str) -> None:
        QMessageBox.warning(
            self, "Could Not Open Image", f"The selected image could not be opened.\n\n{message}"
        )

    def _show_save_error(self, message: str) -> None:
        QMessageBox.warning(
            self, "Could Not Save Image", f"The current image could not be saved.\n\n{message}"
        )

    def _initial_directory(self, key: str) -> Path:
        stored = Path(self.settings.get(key, "", str))
        if stored.is_dir():
            return stored
        source = self.document_controller.current_image
        if (
            source is not None
            and source.source_path is not None
            and source.source_path.parent.is_dir()
        ):
            return source.source_path.parent
        return Path.home()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        for url in event.mimeData().urls():
            if url.isLocalFile() and self.open_primary_image_path(Path(url.toLocalFile())):
                event.acceptProposedAction()
                return

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
