"""Verify the academic operation registry."""

from dip_workbench.operations import ModuleId, OperationRegistryError, operation_registry


def main() -> int:
    try:
        report = operation_registry.verify(("M03-01",))
        if len(ModuleId) != 10:
            raise OperationRegistryError("Expected exactly ten modules.")
        if report.operation_count != 1:
            raise OperationRegistryError("Expected exactly one production operation.")
    except OperationRegistryError as error:
        print(f"Registry invalid: {error}")
        return 1
    noun = "operation" if report.operation_count == 1 else "operations"
    print(f"Registry valid: {report.module_count} modules, {report.operation_count} {noun}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
