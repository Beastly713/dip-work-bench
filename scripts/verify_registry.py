"""Verify the academic operation registry."""

from dip_workbench.operations import ModuleId, OperationRegistryError, operation_registry


def main() -> int:
    try:
        report = operation_registry.verify(
            (
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
                "M06-01",
                "M06-02",
                "M06-03",
                "M06-04",
                "M06-05",
                "M06-06",
                "M08-01",
            )
        )
        if len(ModuleId) != 10:
            raise OperationRegistryError("Expected exactly ten modules.")
        if report.operation_count != 17:
            raise OperationRegistryError("Expected exactly seventeen production operations.")
    except OperationRegistryError as error:
        print(f"Registry invalid: {error}")
        return 1
    noun = "operation" if report.operation_count == 1 else "operations"
    print(f"Registry valid: {report.module_count} modules, {report.operation_count} {noun}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
