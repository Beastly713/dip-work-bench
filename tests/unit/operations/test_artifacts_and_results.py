import numpy as np
import pytest

from dip_workbench.core import ColourModel, ImageAsset, InputValidationError
from dip_workbench.operations import (
    ApplyCandidate,
    ArtifactType,
    CircleOverlay,
    ImageArtifact,
    MaskArtifact,
    MatrixArtifact,
    OperationResult,
    OverlayArtifact,
    OverlayData,
    TextArtifact,
)


def image(model: ColourModel) -> ImageAsset:
    return ImageAsset(name="x", data=np.zeros((2, 2), dtype=np.uint8), colour_model=model)


def test_artifacts_freeze_and_validate() -> None:
    array = np.ones((2, 2))
    artifact = MatrixArtifact("matrix", "Matrix", array)
    array.fill(9)
    assert artifact.artifact_type is ArtifactType.MATRIX and not artifact.data.flags.writeable  # type: ignore[union-attr]
    assert (
        ImageArtifact("image", "Image", image(ColourModel.GRAY)).artifact_type is ArtifactType.IMAGE
    )
    MaskArtifact("mask", "Mask", image(ColourModel.BINARY))
    OverlayArtifact("overlay", "Overlay", OverlayData((CircleOverlay(1, 1, 1),)))
    TextArtifact("text", "Text", "ok")
    with pytest.raises(InputValidationError):
        MaskArtifact("mask", "Mask", image(ColourModel.GRAY))
    with pytest.raises(InputValidationError):
        OverlayArtifact("overlay", "Overlay", object())


def test_result_apply_candidates_metrics_and_lookup() -> None:
    artifact = ImageArtifact("image", "Image", image(ColourModel.GRAY))
    result = OperationResult(
        artifact, metrics={"score": 1.0}, apply_candidates=(ApplyCandidate("image", "Apply"),)
    )
    assert result.get_artifact("image") is artifact and result.all_artifacts == (artifact,)
    with pytest.raises(InputValidationError):
        OperationResult(
            TextArtifact("text", "Text", "x"), apply_candidates=(ApplyCandidate("text", "Apply"),)
        )
