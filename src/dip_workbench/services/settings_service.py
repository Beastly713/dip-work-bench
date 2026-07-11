"""Typed settings service backed by Qt settings."""

from typing import TypeVar, cast

from PySide6.QtCore import QSettings

T = TypeVar("T")


class SettingsService:
    """Keep persistent application preferences behind a small API."""

    def __init__(self, settings: QSettings | None = None) -> None:
        self._settings = settings if settings is not None else QSettings()

    @property
    def backend(self) -> QSettings:
        """Return the injected backend for composition-level inspection."""
        return self._settings

    def get(self, key: str, default: T, value_type: type[T]) -> T:
        """Read a typed value or return the supplied default."""
        return cast(T, self._settings.value(key, default, type=value_type))

    def set(self, key: str, value: object) -> None:
        """Store a value."""
        self._settings.setValue(key, value)

    def contains(self, key: str) -> bool:
        """Return whether a key exists."""
        return self._settings.contains(key)

    def remove(self, key: str) -> None:
        """Remove a key and its value."""
        self._settings.remove(key)

    def sync(self) -> None:
        """Flush pending changes to the backing store."""
        self._settings.sync()
