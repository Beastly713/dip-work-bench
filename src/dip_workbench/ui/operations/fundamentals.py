"""Custom presenters for fundamentals operations."""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout, QWidget

from dip_workbench.core import ImageAsset
from dip_workbench.operations import ImageArtifact, OperationResult
from dip_workbench.ui.widgets import (
    BeforeAfterComparisonWidget,
    DisplayedExportTarget,
    OperationResultPresenter,
    TripleComparisonWidget,
)


class ChannelExtractionPresenter(OperationResultPresenter):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.single = BeforeAfterComparisonWidget()
        self.triple = TripleComparisonWidget()
        self.stack.addWidget(self.single)
        self.stack.addWidget(self.triple)
        layout.addWidget(self.stack, 1)
        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Displayed/export channel:"))
        self.export_selector = QComboBox()
        self.export_selector.currentIndexChanged.connect(
            lambda _index: self._refresh_export_target()
        )
        selector_row.addWidget(self.export_selector)
        selector_row.addStretch()
        layout.addLayout(selector_row)
        self._artifacts: dict[str, ImageArtifact] = {}
        self._has_image = False

    def present(self, input_asset: ImageAsset, result: OperationResult) -> None:
        self.clear_result()
        artifacts = [
            artifact for artifact in result.all_artifacts if isinstance(artifact, ImageArtifact)
        ]
        if not artifacts or any(
            not isinstance(artifact.data, ImageAsset) for artifact in artifacts
        ):
            return
        self._artifacts = {artifact.key: artifact for artifact in artifacts}
        self._has_image = True
        if len(artifacts) == 3:
            ordered = [
                self._artifacts[key] for key in ("red_channel", "green_channel", "blue_channel")
            ]
            self.triple.set_images(
                tuple((artifact.label, artifact.data) for artifact in ordered)  # type: ignore[arg-type]
            )
            self.stack.setCurrentWidget(self.triple)
            self.export_selector.setVisible(True)
            for artifact in ordered:
                self.export_selector.addItem(artifact.label.removesuffix(" Channel"), artifact.key)
        else:
            artifact = artifacts[0]
            self.single.set_images(input_asset, artifact.data, result_label="Selected Channel")  # type: ignore[arg-type]
            self.stack.setCurrentWidget(self.single)
            self.export_selector.setVisible(False)
            self.export_selector.addItem(artifact.label, artifact.key)
        self._refresh_export_target()

    def clear_result(self) -> None:
        self.single.clear()
        self.triple.clear()
        self.export_selector.blockSignals(True)
        self.export_selector.clear()
        self.export_selector.blockSignals(False)
        self._artifacts = {}
        self._has_image = False
        super().clear_result()

    def supports_before_after_comparison(self) -> bool:
        return self._has_image and self.stack.currentWidget() is self.single

    def activate_before_after_comparison(self) -> bool:
        if not self.supports_before_after_comparison():
            return False
        self.single.focus_comparison_controls()
        return True

    def _refresh_export_target(self) -> None:
        key = self.export_selector.currentData()
        artifact = self._artifacts.get(key) if isinstance(key, str) else None
        self._set_displayed_export_target(DisplayedExportTarget(artifact) if artifact else None)
