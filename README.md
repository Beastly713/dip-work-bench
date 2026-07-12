# DIP Workbench

DIP Workbench is an interactive desktop application for demonstrating, comparing, and
documenting syllabus-based digital image-processing operations.

The current implementation is complete through C12. It includes the single-window PySide6 shell,
canonical image/document state, utility transforms, the generic operation workspace, M03-01 Image
Negative, operation navigation and parameter controls, and the shared comparison, graph, table,
matrix, tree, metrics, and displayed-result export layer.

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

Both commands launch the PySide6 desktop shell with the primary-image workflow, utility
transforms, and the registered M03-01 Image Negative academic operation.

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

## Operation contracts

C07 introduces permanent module and operation IDs plus declarative input, parameter, typed
artifact, result, apply-candidate, definition, and registry contracts. Parameters support
conditions and custom validators, while results may contain heterogeneous artifacts. The
production registry is intentionally empty in C07. C08 adds execution and cancellation, and C10
registers the first academic operation.

## Threaded execution

C08 adds shared `QThreadPool` execution with typed progress, success, failure, and cancellation
outcomes. Preview requests debounce for 200 ms by default and use latest-preview-wins semantics;
preview inputs may be reduced in resolution, while Apply always receives full-resolution inputs.
Cancellation is cooperative. C09 connects this infrastructure to the generic workspace.

## Generic operation workspace

C09 connects the operation contracts and threaded execution to a reusable academic workspace.
Inputs appear before parameters, with explicit Original and Current Result source choices.
Preview or Run is non-destructive; Apply reruns at full resolution and creates one history entry.
Input, parameter, and execution failures remain inline in the workspace. The production registry
supports custom editors and presenters; C11 adds complete navigation and generated parameter
controls.

## Image Negative

C10 registers M03-01 Image Negative as the first academic operation. It supports Luminance only,
Each RGB channel, and Grayscale output colour handling for RGB and grayscale images. Preview is
non-destructive and presents the exact input beside the negative with a collapsible input–output
mapping curve. Apply reruns at full resolution and creates one undoable history entry; Undo, Redo,
and image export use the existing document workflow. The production registry checkpoint is one
academic tool. The rest of Module 3 is not implemented; C11 adds complete navigation and generic
parameter controls.

## Operation navigation and configuration

C11 exposes all eleven permanent syllabus modules in the navigation sidebar and on Home while
keeping unregistered tools unavailable. Registry-backed search matches IDs, names, descriptions,
aliases, and module names; `Ctrl+K` reveals the sidebar and focuses search. Accordion and compact
module-number modes, active-tool styling, module cards, and session-only recent operations provide
consistent entry points. Generic auxiliary image inputs can be loaded, replaced, cleared, and
validated without conversion or resizing. Standard parameter schemas now generate typed controls,
including ranges, choices, lists, advanced settings, dynamic conditions, and editable kernels.
Valid immediate or debounced changes can refresh Preview automatically. The registry remains at
one academic operation, M03-01; C12 adds the general comparison and graph/table/matrix/tree result
system.

## Comparison, visualization, and export

C12 adds reusable result-view infrastructure for future operations. Shared components now provide
side-by-side comparison, triple comparison, equal-dimension split comparison, hold `B` to view
Input, synchronized zoom and normalized pan, and in-workspace panel maximization. PyQtGraph backs
general graphs, histograms, and transformation curves. Reusable widgets also cover data tables,
metrics, matrix table/heatmap views, and hierarchical trees.

Displayed-result export is now artifact-based through one injected `ExportService`. Supported
exports are images as PNG, JPEG, BMP, or TIFF; graphs as PNG or CSV; tables and matrices as CSV;
and metrics, text, bitstreams, and trees as TXT. Raw label maps still require a later explicit
display mapping before image export. No histogram, tree-producing, compression, or additional
academic operation is registered yet. The registry remains one academic operation. C13 will add
overlays, interaction modes, the details drawer, and final presenter templates.

## Architecture principles

The project uses a Python 3.11 `src` layout, explicit dependency injection, typed application
errors, and small service boundaries. Shared services are composed at startup rather than held in
mutable module-level singletons. The architecture remains library-first and will grow in the
sequenced implementation commits.

See [docs/development.md](docs/development.md) for the complete development command reference.
