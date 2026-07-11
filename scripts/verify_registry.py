"""Verify the academic operation registry."""

from dip_workbench.operations import ModuleId, OperationRegistryError, operation_registry


def main() -> int:
    try:
        report = operation_registry.verify()
        if len(ModuleId) != 11:
            raise OperationRegistryError("Expected exactly eleven modules.")
    except OperationRegistryError as error:
        print(f"Registry invalid: {error}")
        return 1
    print(f"Registry valid: {report.module_count} modules, {report.operation_count} operations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
