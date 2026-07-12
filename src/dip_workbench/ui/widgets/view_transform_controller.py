"""Synchronize view transforms across comparison image canvases."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager, suppress
from typing import Any

from PySide6.QtCore import QObject

from dip_workbench.ui.widgets.image_canvas import ImageCanvas


class ViewTransformController(QObject):
    """Coordinate zoom, fit and normalized pan for two or three canvases."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._canvases: list[ImageCanvas] = []
        self._connections: list[tuple[Any, Callable[..., None]]] = []
        self._syncing = False

    def set_canvases(self, canvases: list[ImageCanvas] | tuple[ImageCanvas, ...]) -> None:
        self.clear()
        self._canvases = list(canvases)
        for canvas in self._canvases:

            def zoom_callback(value: float, source: ImageCanvas = canvas) -> None:
                self._sync_zoom(source, value)

            def horizontal_callback(_value: int, source: ImageCanvas = canvas) -> None:
                self._sync_scroll(source, horizontal=True)

            def vertical_callback(_value: int, source: ImageCanvas = canvas) -> None:
                self._sync_scroll(source, horizontal=False)

            canvas.zoom_changed.connect(zoom_callback)
            canvas.horizontalScrollBar().valueChanged.connect(horizontal_callback)
            canvas.verticalScrollBar().valueChanged.connect(vertical_callback)
            self._connections.extend(
                [
                    (canvas.zoom_changed, zoom_callback),
                    (canvas.horizontalScrollBar().valueChanged, horizontal_callback),
                    (canvas.verticalScrollBar().valueChanged, vertical_callback),
                ]
            )

    def clear(self) -> None:
        for signal, callback in self._connections:
            with suppress(RuntimeError, TypeError):
                signal.disconnect(callback)
        self._connections = []
        self._canvases = []

    def fit_all(self) -> None:
        with self._guard():
            for canvas in self._canvases:
                canvas.fit_to_view()

    def actual_size_all(self) -> None:
        with self._guard():
            for canvas in self._canvases:
                canvas.show_actual_size()

    def zoom_in_all(self) -> None:
        if self._canvases:
            self._canvases[0].zoom_in()

    def zoom_out_all(self) -> None:
        if self._canvases:
            self._canvases[0].zoom_out()

    def _sync_zoom(self, source: ImageCanvas, percent: float) -> None:
        if self._syncing:
            return
        with self._guard():
            for canvas in self._canvases:
                if canvas is not source:
                    canvas.set_zoom_percent(percent)

    def _sync_scroll(self, source: ImageCanvas, *, horizontal: bool) -> None:
        if self._syncing:
            return
        scrollbar = source.horizontalScrollBar() if horizontal else source.verticalScrollBar()
        span = scrollbar.maximum() - scrollbar.minimum()
        ratio = 0.0 if span <= 0 else (scrollbar.value() - scrollbar.minimum()) / span
        with self._guard():
            for canvas in self._canvases:
                if canvas is source:
                    continue
                target = canvas.horizontalScrollBar() if horizontal else canvas.verticalScrollBar()
                target_span = target.maximum() - target.minimum()
                target.setValue(
                    target.minimum()
                    if target_span <= 0
                    else round(target.minimum() + ratio * target_span)
                )

    @contextmanager
    def _guard(self):  # type: ignore[no-untyped-def]
        self._syncing = True
        try:
            yield
        finally:
            self._syncing = False
