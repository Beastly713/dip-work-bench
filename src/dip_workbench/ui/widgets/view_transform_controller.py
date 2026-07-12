"""Synchronize view transforms across comparison image canvases."""

from __future__ import annotations

from contextlib import contextmanager, suppress

from PySide6.QtCore import QObject

from dip_workbench.ui.widgets.image_canvas import ImageCanvas


class ViewTransformController(QObject):
    """Coordinate zoom, fit and normalized pan for two or three canvases."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._canvases: list[ImageCanvas] = []
        self._syncing = False

    def set_canvases(self, canvases: list[ImageCanvas] | tuple[ImageCanvas, ...]) -> None:
        self.clear()
        self._canvases = list(canvases)
        for canvas in self._canvases:
            canvas.zoom_changed.connect(lambda value, source=canvas: self._sync_zoom(source, value))
            canvas.horizontalScrollBar().valueChanged.connect(
                lambda _value, source=canvas: self._sync_scroll(source, horizontal=True)
            )
            canvas.verticalScrollBar().valueChanged.connect(
                lambda _value, source=canvas: self._sync_scroll(source, horizontal=False)
            )

    def clear(self) -> None:
        for canvas in self._canvases:
            with suppress(RuntimeError, TypeError):
                canvas.zoom_changed.disconnect()
            for scrollbar in (canvas.horizontalScrollBar(), canvas.verticalScrollBar()):
                with suppress(RuntimeError, TypeError):
                    scrollbar.valueChanged.disconnect()
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
