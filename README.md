# DIP Workbench

DIP Workbench is an interactive desktop application for demonstrating, comparing, and
documenting syllabus-based digital image-processing operations.

The current implementation includes the C02 single-window desktop shell alongside the C01
infrastructure foundation. Image loading, image operations, and document state are not available
yet.

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

Both commands launch the PySide6 desktop shell. The initial Home page and structural navigation,
parameter, report-builder, and operation-workspace placeholders contain no image-processing
behavior yet.

## Architecture principles

The project uses a Python 3.11 `src` layout, explicit dependency injection, typed application
errors, and small service boundaries. Shared services are composed at startup rather than held in
mutable module-level singletons. The architecture remains library-first and will grow in the
sequenced implementation commits.

See [docs/development.md](docs/development.md) for the complete development command reference.
