"""Run the local quality gate without modifying the repository."""

import subprocess
import sys
from pathlib import Path

COMMANDS = (
    (sys.executable, "-m", "ruff", "format", "--check", "."),
    (sys.executable, "-m", "ruff", "check", "."),
    (sys.executable, "-m", "mypy", "src"),
    (sys.executable, "scripts/verify_registry.py"),
)


def main() -> int:
    """Run each quality command in order and return its first failure status."""
    repository_root = Path(__file__).resolve().parents[1]
    if not (repository_root / "pyproject.toml").is_file():
        print("error: repository pyproject.toml was not found", file=sys.stderr)
        return 2
    for command in COMMANDS:
        print(f"$ {' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=repository_root, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
