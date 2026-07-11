# DIP Workbench

DIP Workbench is an interactive desktop application for demonstrating, comparing, and
documenting syllabus-based digital image-processing operations.

The current implementation is the C01 infrastructure foundation. It provides the installable
package, shared infrastructure services, developer tooling, tests, and CI. The graphical shell
begins in C02; no image operations or usable desktop workbench are present yet.

## Development setup

Python 3.11 on Ubuntu is required.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Run the local quality gate from the repository root:

```bash
ruff format --check .
ruff check .
mypy src
pytest -q
```

## Entry points

```bash
python -m dip_workbench
dip-workbench
```

At C01, both commands initialize the dependency-injected infrastructure composition and exit
successfully without creating a GUI or opening a window.

## Architecture principles

The project uses a Python 3.11 `src` layout, explicit dependency injection, typed application
errors, and small service boundaries. Shared services are composed at startup rather than held in
mutable module-level singletons. The architecture remains library-first and will grow in the
sequenced implementation commits.

See [docs/development.md](docs/development.md) for the complete development command reference.
