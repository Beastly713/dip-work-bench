"""Operation results and explicit apply candidates."""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from dip_workbench.core import ImageAsset, InputValidationError
from dip_workbench.operations.artifacts import ResultArtifact


@dataclass(frozen=True, slots=True)
class ApplyCandidate:
    artifact_key: str
    label: str

    def __post_init__(self) -> None:
        if not self.artifact_key or not self.label.strip():
            raise InputValidationError("Apply candidate is invalid.")


@dataclass(frozen=True, slots=True)
class OperationResult:
    primary_artifact: ResultArtifact
    artifacts: tuple[ResultArtifact, ...] = ()
    metrics: Mapping[str, int | float] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    processing_time_ms: float | None = None
    apply_candidates: tuple[ApplyCandidate, ...] = ()

    def __post_init__(self) -> None:
        all_items = (self.primary_artifact, *self.artifacts)
        keys = [item.key for item in all_items]
        if len(keys) != len(set(keys)):
            raise InputValidationError("Artifact keys must be unique.")
        for key, value in self.metrics.items():
            if (
                not isinstance(key, str)
                or not key.strip()
                or isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
            ):
                raise InputValidationError("Metrics must be finite numeric values.")
        if any(not isinstance(w, str) or not w.strip() for w in self.warnings):
            raise InputValidationError("Warnings must be non-empty.")
        if self.processing_time_ms is not None and (
            isinstance(self.processing_time_ms, bool)
            or not math.isfinite(self.processing_time_ms)
            or self.processing_time_ms < 0
        ):
            raise InputValidationError("Processing time is invalid.")
        candidate_keys = [candidate.artifact_key for candidate in self.apply_candidates]
        if len(candidate_keys) != len(set(candidate_keys)):
            raise InputValidationError("Apply candidates must be unique.")
        mapping = {item.key: item for item in all_items}
        for key in candidate_keys:
            if key not in mapping or not isinstance(mapping[key].data, ImageAsset):
                raise InputValidationError("Apply candidate must reference an image artifact.")
        object.__setattr__(self, "metrics", MappingProxyType(dict(self.metrics)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def all_artifacts(self) -> tuple[ResultArtifact, ...]:
        return (self.primary_artifact, *self.artifacts)

    def get_artifact(self, key: str) -> ResultArtifact:
        for artifact in self.all_artifacts:
            if artifact.key == key:
                return artifact
        raise InputValidationError(f"Unknown artifact: {key}.")
