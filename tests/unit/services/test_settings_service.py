"""Tests for the injectable settings service."""

from PySide6.QtCore import QSettings

from dip_workbench.services import SettingsService


def make_service(settings_path) -> SettingsService:  # type: ignore[no-untyped-def]
    return SettingsService(QSettings(str(settings_path), QSettings.Format.IniFormat))


def test_typed_values_defaults_contains_and_remove(tmp_path) -> None:  # type: ignore[no-untyped-def]
    service = make_service(tmp_path / "settings.ini")
    service.set("name", "demo")
    service.set("count", 7)
    service.set("enabled", True)
    assert service.get("name", "", str) == "demo"
    assert service.get("count", 0, int) == 7
    assert service.get("enabled", False, bool) is True
    assert service.get("missing", "fallback", str) == "fallback"
    assert service.contains("name")
    service.remove("name")
    assert not service.contains("name")


def test_sync_persists_between_backends(tmp_path) -> None:  # type: ignore[no-untyped-def]
    settings_path = tmp_path / "settings.ini"
    writer = make_service(settings_path)
    writer.set("shared", "value")
    writer.sync()
    reader = make_service(settings_path)
    reader.sync()
    assert reader.get("shared", "", str) == "value"
