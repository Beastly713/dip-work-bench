# DIP Workbench

DIP Workbench is an interactive desktop application for demonstrating, comparing, and
documenting syllabus-based digital image-processing operations.

The current implementation includes the C02 single-window desktop shell and the C03 canonical
image and file-I/O foundation. Image operations and document state are not available yet.

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

## Image foundation

Canonical three-channel images use RGB internally. OpenCV's BGR ordering is isolated to explicit
conversion and file-I/O boundaries. The file service supports PNG, JPEG, BMP, and TIFF, including
Unicode paths and explicit alpha compositing. The desktop actions are not connected to image
loading yet; C05 will connect this service to the primary-image workflow.

## Document state foundation

C04 adds a single-document state store with an immutable Original, independent Current Result,
and non-destructive previews. Applied states use lossless temporary PNG snapshots for undo and
redo, limited to the newest 25 applied states. This state is not connected to the GUI yet; C05
will provide the primary image workflow and canvas.

## Primary image workflow

C05 connects the desktop shell to document state. Users can open or drop PNG, JPEG, BMP, and TIFF
images, inspect image and pixel information, fit or view at actual size, zoom and pan, save Current
Result, and use reset/undo/redo. The manual flow is: Open → Inspect → Zoom/Pan → Save → Reset →
Undo/Redo. Sample images and academic operations remain unavailable; C06 adds editing utilities
and reusable ROI selection.

## Editing utilities and regions

C06 adds Crop, Resize, Rotate, and Flip/Mirror with non-destructive previews and explicit Apply.
Applied transforms enter normal undoable history. Resize supports aspect locking and explicit
interpolation; rotation supports Expanded and Cropped canvases. Rectangular ROI selection uses
full-resolution coordinates and can be retained without cropping. Academic operations remain
unavailable; C07 introduces operation and artifact contracts.

## Architecture principles

The project uses a Python 3.11 `src` layout, explicit dependency injection, typed application
errors, and small service boundaries. Shared services are composed at startup rather than held in
mutable module-level singletons. The architecture remains library-first and will grow in the
sequenced implementation commits.

See [docs/development.md](docs/development.md) for the complete development command reference.
