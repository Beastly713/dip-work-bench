import pytest

from dip_workbench.core import InputValidationError
from dip_workbench.operations import (
    MODULE_NAMES,
    ApplyPolicy,
    InputSpec,
    ModuleId,
    OperationDefinition,
    OperationId,
    OperationRegistry,
    OperationRegistryError,
    PresenterId,
    PreviewPolicy,
    operation_registry,
)


def definition(
    value: str = "M01-01", name: str = "Demo", aliases: tuple[str, ...] = ("sample",)
) -> OperationDefinition:
    return OperationDefinition(
        OperationId(value),
        ModuleId(value[:3]),
        name,
        "Short description",
        (InputSpec("image", "Image"),),
        (),
        PreviewPolicy.NONE,
        ApplyPolicy.NONE,
        PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
        lambda: "executor",
        lambda: "presenter",
        aliases,
        "sample-id",
    )


def test_registry_lookup_search_factories_and_verify() -> None:
    first = definition()
    second = definition("M01-02", "Another", ("other",))
    registry = OperationRegistry((second, first))
    assert (
        registry.all() == (first, second)
        and registry.get("M01-01") is first
        and registry.try_get("M01-99") is None
        and registry.by_module(ModuleId.M01) == (first, second)
    )
    assert (
        registry.search("sample")[0] is first
        and registry.create_executor(first.id) == "executor"
        and registry.create_presenter(first.id) == "presenter"
        and registry.sample_recommendation(first.id) == "sample-id"
        and registry.verify((first.id,)).operation_count == 2
    )
    with pytest.raises(OperationRegistryError):
        registry.verify(("M02-01",))


def test_registry_and_definition_validation() -> None:
    registry = OperationRegistry()
    item = definition()
    registry.register(item)
    with pytest.raises(OperationRegistryError):
        registry.register(item)
    with pytest.raises(InputValidationError):
        OperationDefinition(
            OperationId("M01-01"),
            ModuleId.M02,
            "X",
            "Y",
            (),
            (),
            PreviewPolicy.NONE,
            ApplyPolicy.NONE,
            PresenterId.T1_SINGLE_IMAGE_TRANSFORMATION,
            lambda: None,
            lambda: None,
        )
    assert tuple(str(item.id) for item in operation_registry.all()) == (
        "M01-01",
        "M01-02",
        "M01-03",
        "M02-02",
        "M03-01",
        "M03-03",
        "M04-01",
        "M04-02",
        "M05-01",
        "M05-05",
        "M08-01",
    )


def test_reduced_scope_contract() -> None:
    assert len(tuple(ModuleId)) == 10
    assert [MODULE_NAMES[module] for module in ModuleId] == [
        "Image Fundamentals",
        "Basic Adjustments",
        "Intensity Transformations",
        "Histogram Processing",
        "Blur, Filtering and Convolution",
        "Sharpening and Edge Enhancement",
        "Frequency-Domain Processing",
        "Noise Simulation",
        "Basic Segmentation",
        "Edge and Geometric Feature Detection",
    ]
    with pytest.raises(InputValidationError):
        OperationId("M11-01")
    assert operation_registry.get("M03-01").display_name == "Image Negative"
    assert operation_registry.get("M01-01").display_name == "Colour to Grayscale"
