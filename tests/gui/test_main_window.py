"""GUI tests for the C02 main window shell."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QSettings

from dip_workbench.services import SettingsService
from dip_workbench.ui.main_window import MainWindow, PageIndex


def make_window(qtbot, tmp_path) -> MainWindow:  # type: ignore[no-untyped-def]
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    window = MainWindow(SettingsService(backend))
    qtbot.addWidget(window)
    window.show()
    return window


def test_main_window_structure_and_navigation(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    assert window.windowTitle() == "DIP Workbench"
    assert window.minimumWidth() == 1180
    assert window.minimumHeight() == 720
    assert window.page_stack.count() == 3
    assert window.page_stack.currentIndex() == PageIndex.HOME

    window.action_map["report"].trigger()
    assert window.page_stack.currentIndex() == PageIndex.REPORT
    window.action_map["home"].trigger()
    assert window.page_stack.currentIndex() == PageIndex.HOME

    assert [action.text() for action in window.menuBar().actions()] == [
        "File",
        "Edit",
        "View",
        "Help",
    ]
    assert [action.text() for action in window.global_toolbar.actions()] == [
        "Home",
        "Open Primary Image",
        "Save Current Image",
        "",
        "Undo",
        "Redo",
        "Reset Current Image",
        "",
        "Compare",
        "Add to Report",
        "Export Displayed Result",
        "",
        "Presentation Mode",
    ]


def test_action_availability_and_panel_constraints(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    enabled = {"home", "report", "exit", "show_navigation", "show_parameters"}
    for key, action in window.action_map.items():
        assert action.isEnabled() is (key in enabled)
    assert window.navigation_sidebar.minimumWidth() == 220
    assert window.parameter_panel.minimumWidth() == 280


def test_panels_hide_and_restore_usable_widths(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    window = make_window(qtbot, tmp_path)
    window.main_splitter.setSizes([300, 700, 360])
    window.action_map["show_navigation"].setChecked(False)
    assert not window.navigation_sidebar.isVisible()
    window.action_map["show_navigation"].setChecked(True)
    assert window.navigation_sidebar.isVisible()
    assert window.main_splitter.sizes()[0] >= 220

    window.action_map["show_parameters"].setChecked(False)
    assert not window.parameter_panel.isVisible()
    window.action_map["show_parameters"].setChecked(True)
    assert window.parameter_panel.isVisible()
    assert window.main_splitter.sizes()[2] >= 280


def test_geometry_and_panel_widths_persist(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    settings_path = tmp_path / "settings.ini"
    first_backend = QSettings(str(settings_path), QSettings.Format.IniFormat)
    first = MainWindow(SettingsService(first_backend))
    qtbot.addWidget(first)
    first.show()
    first.resize(1250, 760)
    first.main_splitter.setSizes([300, 600, 350])
    first.close()

    second_backend = QSettings(str(settings_path), QSettings.Format.IniFormat)
    second = MainWindow(SettingsService(second_backend))
    qtbot.addWidget(second)
    second.show()
    assert second.size().width() >= 1180
    assert second.size().height() == 760
    assert second.main_splitter.sizes()[0] >= 220
    assert second.main_splitter.sizes()[2] >= 280
    assert second_backend.contains("window/geometry")


def test_corrupt_settings_fall_back_safely(qtbot, tmp_path) -> None:  # type: ignore[no-untyped-def]
    backend = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    backend.setValue("layout/navigation_width", -4)
    backend.setValue("layout/parameter_width", "invalid")
    backend.setValue("window/geometry", "not geometry")
    window = MainWindow(SettingsService(backend))
    qtbot.addWidget(window)
    assert window._navigation_width == 270
    assert window._parameter_width == 320
    assert window.size().width() == 1440
    assert window.size().height() == 900
