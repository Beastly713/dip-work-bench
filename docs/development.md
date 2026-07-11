# Development guide

Run every command in this guide from the repository root.

## Environment and installation

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## Quality commands

```bash
ruff format .
ruff check .
mypy src
pytest -q
```

To inspect test coverage without enforcing a threshold:

```bash
pytest --cov=dip_workbench --cov-report=term-missing
```

The combined, non-mutating quality gate and environment verification are:

```bash
python scripts/check.py
python scripts/verify_environment.py
```

## Running the package

```bash
python -m dip_workbench
dip-workbench
```

These entry points configure the shared infrastructure and launch the C02 PySide6 desktop shell.
The application context is released after the Qt event loop exits. C02 contains structural pages
and panels only; image and operation workflows begin in later commits.

C03 defines immutable canonical RGB, grayscale, binary, and label-map image assets plus separate
floating intermediates. RGB is the sole internal three-channel order; BGR is confined to OpenCV
conversion helpers. `ImageIOService` supports PNG, JPEG, BMP, and TIFF but is intentionally not
wired to the desktop shell. C05 will add that user workflow.

For headless GUI validation on Ubuntu, run:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/gui -q
```

Codex must not commit or push repository changes. Staging, branch changes, and pull-request
creation also remain user-controlled.
