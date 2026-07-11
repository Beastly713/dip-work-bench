"""Coordination for the primary image document workflow."""

from pathlib import Path

from dip_workbench.core import ImageAsset, InputValidationError, RectangularRegion
from dip_workbench.services import (
    FlipDirection,
    ImageIOService,
    ImageTransformService,
    InterpolationMode,
    RotationCanvasMode,
)
from dip_workbench.state import ActivePreview, DocumentStore


class DocumentController:
    def __init__(
        self,
        image_io: ImageIOService,
        image_transforms: ImageTransformService,
        document_store: DocumentStore,
    ) -> None:
        self.image_io = image_io
        self.image_transforms = image_transforms
        self.document_store = document_store
        self._preview_generation = 0

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

    @property
    def selected_region(self) -> RectangularRegion | None:
        state = self.document_store.get_operation_state("U-14")
        if state is None:
            return None
        region = state.get("region")
        return region if isinstance(region, RectangularRegion) else None

    def set_selected_region(self, region: RectangularRegion) -> None:
        current = self._require_current()
        if not isinstance(region, RectangularRegion) or not region.fits_within(
            current.width, current.height
        ):
            raise InputValidationError("Selected region must fit within Current Result.")
        self.document_store.set_operation_state("U-14", {"region": region})

    def clear_selected_region(self) -> None:
        self.document_store.clear_operation_state("U-14")

    def preview_crop(self, region: RectangularRegion | None = None) -> ImageAsset:
        selected = region or self.selected_region
        if selected is None:
            raise InputValidationError("Select a region before previewing Crop.")
        return self._set_preview(
            "U-05",
            "Crop",
            self.image_transforms.crop(self._require_current(), selected),
            {"region": selected},
        )

    def preview_resize(
        self, *, width: int, height: int, interpolation: InterpolationMode
    ) -> ImageAsset:
        return self._set_preview(
            "U-06",
            "Resize",
            self.image_transforms.resize(
                self._require_current(), width=width, height=height, interpolation=interpolation
            ),
            {"width": width, "height": height, "interpolation": interpolation.value},
        )

    def preview_rotate(
        self,
        *,
        angle_degrees: float,
        canvas_mode: RotationCanvasMode,
        interpolation: InterpolationMode,
    ) -> ImageAsset:
        return self._set_preview(
            "U-07",
            "Rotate",
            self.image_transforms.rotate(
                self._require_current(),
                angle_degrees=angle_degrees,
                canvas_mode=canvas_mode,
                interpolation=interpolation,
            ),
            {
                "angle_degrees": angle_degrees,
                "canvas_mode": canvas_mode.value,
                "interpolation": interpolation.value,
            },
        )

    def preview_flip(self, *, direction: FlipDirection) -> ImageAsset:
        return self._set_preview(
            "U-08",
            "Flip/Mirror",
            self.image_transforms.flip(self._require_current(), direction=direction),
            {"direction": direction.value},
        )

    def apply_active_preview(self) -> ImageAsset:
        preview = self.document_store.active_preview
        current = self._require_current()
        if preview is None or not isinstance(preview.result, ImageAsset):
            raise InputValidationError("No image preview is available to apply.")
        if preview.input_asset_ids != (current.id,):
            raise InputValidationError("The utility preview is stale.")
        names = {"U-05": "Crop", "U-06": "Resize", "U-07": "Rotate", "U-08": "Flip/Mirror"}
        if preview.operation_id not in names:
            raise InputValidationError("The active preview is not a supported image utility.")
        result = self.document_store.apply_image(
            preview.result,
            operation_id=preview.operation_id,
            operation_name=names[preview.operation_id],
            parameters=preview.parameters,
        )
        self.clear_selected_region()
        return result

    def clear_active_preview(self) -> None:
        self.document_store.clear_active_preview()

    def _set_preview(
        self,
        operation_id: str,
        operation_name: str,
        result: ImageAsset,
        parameters: dict[str, object],
    ) -> ImageAsset:
        current = self._require_current()
        self._preview_generation += 1
        self.document_store.set_active_preview(
            ActivePreview(
                operation_id,
                (current.id,),
                parameters,
                {"region": parameters["region"]} if "region" in parameters else {},
                result,
                self._preview_generation,
            )
        )
        return result

    def _require_current(self) -> ImageAsset:
        if self.current_image is None:
            raise InputValidationError("No current image is available.")
        return self.current_image
