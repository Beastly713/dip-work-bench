"""Deterministic operation registration, lookup, and search."""

from collections.abc import Iterable
from dataclasses import dataclass

from dip_workbench.core import DIPWorkbenchError
from dip_workbench.operations.definitions import OperationDefinition
from dip_workbench.operations.identifiers import ModuleId, OperationId, parse_operation_id


class OperationRegistryError(DIPWorkbenchError):
    pass


@dataclass(frozen=True, slots=True)
class RegistryVerificationReport:
    module_count: int
    operation_count: int


class OperationRegistry:
    def __init__(self, definitions: Iterable[OperationDefinition] = ()) -> None:
        self._definitions: dict[OperationId, OperationDefinition] = {}
        for definition in definitions:
            self.register(definition)

    def register(self, definition: OperationDefinition) -> None:
        if not isinstance(definition, OperationDefinition):
            raise OperationRegistryError("Only operation definitions can be registered.")
        if definition.id in self._definitions:
            raise OperationRegistryError(f"Duplicate operation ID: {definition.id}.")
        self._definitions[definition.id] = definition

    def get(self, operation_id: str | OperationId) -> OperationDefinition:
        parsed = parse_operation_id(operation_id)
        try:
            return self._definitions[parsed]
        except KeyError as error:
            raise OperationRegistryError(f"Unknown operation ID: {parsed}.") from error

    def try_get(self, operation_id: str | OperationId) -> OperationDefinition | None:
        try:
            return self.get(operation_id)
        except (OperationRegistryError, DIPWorkbenchError):
            return None

    def all(self) -> tuple[OperationDefinition, ...]:
        return tuple(sorted(self._definitions.values(), key=lambda item: item.id.value))

    def by_module(self, module_id: ModuleId) -> tuple[OperationDefinition, ...]:
        return tuple(item for item in self.all() if item.module_id is module_id)

    def search(self, query: str) -> tuple[OperationDefinition, ...]:
        term = query.strip().casefold()
        if not term:
            return self.all()
        ranked = []
        for item in self.all():
            fields = [
                item.id.value.casefold(),
                item.display_name.casefold(),
                item.short_description.casefold(),
                *(alias.casefold() for alias in item.search_aliases),
            ]
            matches = [
                0 if field == term else 1 if field.startswith(term) else 2
                for field in fields
                if term in field
            ]
            if matches:
                ranked.append((min(matches), item.id.value, item))
        return tuple(item for _, _, item in sorted(ranked, key=lambda value: (value[0], value[1])))

    def create_executor(self, operation_id: str | OperationId) -> object:
        return self.get(operation_id).executor_factory()

    def create_presenter(self, operation_id: str | OperationId) -> object:
        return self.get(operation_id).presenter_factory()

    def sample_recommendation(self, operation_id: str | OperationId) -> str | None:
        return self.get(operation_id).sample_id

    def verify(
        self, expected_operation_ids: Iterable[str | OperationId] = ()
    ) -> RegistryVerificationReport:
        missing = [
            str(parse_operation_id(value))
            for value in expected_operation_ids
            if self.try_get(value) is None
        ]
        if missing:
            raise OperationRegistryError(f"Missing expected operations: {', '.join(missing)}.")
        return RegistryVerificationReport(len(ModuleId), len(self._definitions))


operation_registry = OperationRegistry()
