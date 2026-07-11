"""Coordination for the primary image document workflow."""

from pathlib import Path

from dip_workbench.core import ImageAsset, InputValidationError
from dip_workbench.services import ImageIOService
from dip_workbench.state import DocumentStore


class DocumentController:
    def __init__(self, image_io: ImageIOService, document_store: DocumentStore) -> None:
        self.image_io = image_io
        self.document_store = document_store

    @property
    def current_image(self) -> ImageAsset | None:
        return self.document_store.current_image

    @property
    def original_image(self) -> ImageAsset | None:
        return self.document_store.original_image

    @property
    def has_document(self) -> bool:
        return self.document_store.has_document

    @property
    def can_undo(self) -> bool:
        return self.document_store.can_undo

    @property
    def can_redo(self) -> bool:
        return self.document_store.can_redo

    def open_primary_image(self, path: str | Path) -> ImageAsset:
        asset = self.image_io.load(path)
        self.document_store.set_primary_image(asset)
        current = self.document_store.current_image
        assert current is not None
        return current

    def save_current_image(self, path: str | Path) -> Path:
        if self.current_image is None:
            raise InputValidationError("No current image is available to save.")
        return self.image_io.save(self.current_image, path)

    def undo(self) -> ImageAsset:
        return self.document_store.undo()

    def redo(self) -> ImageAsset:
        return self.document_store.redo()

    def reset_to_original(self) -> ImageAsset:
        return self.document_store.reset_to_original()
