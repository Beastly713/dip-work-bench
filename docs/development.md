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

C04 adds Qt-independent single-document state. Original remains immutable, previews do not alter
Current Result, and applied states use disk-backed lossless PNG undo/redo history capped at 25
entries. Temporary history is cleaned on normal shutdown, while abandoned marked sessions are
cleaned on a later launch. C05 will connect this state to the desktop workflow.

C05 provides the functional primary-image workflow: Open → Inspect → Zoom/Pan → Save → Reset →
Undo/Redo. PNG, JPEG, BMP, and TIFF files can be opened or dropped, while the status bar reports
image and pixel information. Sample images and academic operations remain unavailable. C06 adds
editing utilities and reusable ROI selection.

C06 adds non-destructive Crop, Resize, Rotate, and Flip/Mirror previews. Applying a preview creates
normal undoable history. Resize exposes aspect locking and interpolation, rotation offers Expanded
and Cropped canvas modes, and reusable rectangular ROI selection maps to full-resolution image
coordinates without changing Current Result. C07 introduces operation and artifact contracts.

C07 adds the PySide-free operation domain contracts: permanent identifiers, declarative inputs
and parameters, conditional validation, heterogeneous typed artifacts, explicit apply candidates,
and deterministic registry lookup/search. The production registry intentionally contains zero
operations. C08 adds execution and cancellation; C10 registers the first academic operation.

```bash
python scripts/verify_registry.py
```

For headless GUI validation on Ubuntu, run:

```bash
QT_QPA_PLATFORM=offscreen pytest tests/gui -q
```

Codex must not commit or push repository changes. Staging, branch changes, and pull-request
creation also remain user-controlled.
