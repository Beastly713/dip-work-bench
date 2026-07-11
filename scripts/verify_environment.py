"""Verify the C01 development environment."""

import sys
from importlib import import_module
from pathlib import Path


def main() -> int:
    """Check interpreter and installed package details."""
    if sys.version_info[:2] != (3, 11):
        print(f"error: Python 3.11.x is required; found {sys.version.split()[0]}", file=sys.stderr)
        return 1
    try:
        pyside = import_module("PySide6")
        package = import_module("dip_workbench")
    except ImportError as error:
        print(f"error: required import failed: {error}", file=sys.stderr)
        return 1
    if package.__version__ != "0.1.0":
        print(f"error: expected package version 0.1.0; found {package.__version__}")
        return 1
    package_path = Path(package.__file__).resolve()
    expected_source = Path(__file__).resolve().parents[1] / "src" / "dip_workbench"
    if expected_source not in package_path.parents:
        print(f"error: package is not loaded from the source tree: {package_path}", file=sys.stderr)
        return 1
    print(f"Python: {sys.version.split()[0]}")
    print(f"DIP Workbench: {package.__version__}")
    print(f"Package path: {package_path}")
    print(f"PySide6: {pyside.__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
