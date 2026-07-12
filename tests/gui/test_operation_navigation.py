"""Tests for registry navigation, search, module cards, and recent tools."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QLabel

from dip_workbench.operations import ModuleId, operation_registry
from dip_workbench.ui.pages import HomePage
from dip_workbench.ui.panels import NavigationSidebar


def test_eleven_ordered_groups_and_home_cards(qtbot) -> None:  # type: ignore[no-untyped-def]
    sidebar = NavigationSidebar(lambda: None, operation_registry)
    home = HomePage(operation_registry)
    qtbot.addWidget(sidebar)
    qtbot.addWidget(home)
    sidebar.show()
    assert list(sidebar.module_buttons) == list(ModuleId)
    assert list(home.module_cards) == list(ModuleId)
    assert tuple(sidebar.operation_buttons) == ("M03-01",)
    assert "1 registered tool" in [
        label.text() for label in home.module_cards[ModuleId.M03].findChildren(QLabel)
    ]


def test_accordion_search_alias_module_and_selection(qtbot) -> None:  # type: ignore[no-untyped-def]
    sidebar = NavigationSidebar(lambda: None, operation_registry)
    qtbot.addWidget(sidebar)
    sidebar.show()
    sidebar.expand_module(ModuleId.M01)
    assert sidebar.expanded_module is ModuleId.M01
    assert sidebar.module_contents[ModuleId.M01].isVisible()
    assert not sidebar.module_contents[ModuleId.M03].isVisible()
    selected: list[object] = []
    sidebar.operation_selected.connect(selected.append)
    for query in ("negative", "invert", "photographic negative", "intensity", "M03-01"):
        sidebar.search_field.setText(query)
        buttons = sidebar.search_page.findChildren(type(sidebar.home_button))
        assert any("Image Negative" in button.text() for button in buttons)
    sidebar.search_page.findChildren(type(sidebar.home_button))[-1].click()
    assert selected and str(selected[-1].id) == "M03-01"  # type: ignore[union-attr]


def test_active_collapsed_focus_and_recent(qtbot) -> None:  # type: ignore[no-untyped-def]
    sidebar = NavigationSidebar(lambda: None, operation_registry)
    home = HomePage(operation_registry)
    qtbot.addWidget(sidebar)
    qtbot.addWidget(home)
    sidebar.show()
    home.show()
    definition = operation_registry.get("M03-01")
    sidebar.set_active_operation(definition)
    assert sidebar.expanded_module is ModuleId.M03
    assert "font-weight: 700" in sidebar.operation_buttons["M03-01"].styleSheet()
    assert "font-weight: 700" in sidebar.module_buttons[ModuleId.M03].styleSheet()
    assert "font-weight: 700" in sidebar.collapsed_module_buttons[ModuleId.M03].styleSheet()
    sidebar.set_active_operation(None)
    assert not sidebar.operation_buttons["M03-01"].styleSheet()
    assert not sidebar.module_buttons[ModuleId.M03].styleSheet()
    assert not sidebar.collapsed_module_buttons[ModuleId.M03].styleSheet()
    assert sidebar.expanded_module is ModuleId.M03
    sidebar.set_active_operation(definition)
    sidebar.set_collapsed(True)
    assert sidebar.is_collapsed and sidebar.minimumWidth() == sidebar.COLLAPSED_WIDTH
    sidebar.activateWindow()
    sidebar.focus_search()
    qtbot.waitUntil(sidebar.search_field.hasFocus)
    assert not sidebar.is_collapsed
    home.set_recent_operations((definition,))
    assert home.recent_frame.isVisibleTo(home)
