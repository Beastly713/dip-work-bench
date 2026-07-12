import pytest

from dip_workbench.core import InputValidationError
from dip_workbench.operations import (
    ApplyPolicy,
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
        (),
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
    assert tuple(str(item.id) for item in operation_registry.all()) == ("M03-01",)
