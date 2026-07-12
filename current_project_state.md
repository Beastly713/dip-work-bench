# DIP Workbench Current Project State

Last updated from the local codebase on 2026-07-12.

This file is intended as a compact handoff for a new ChatGPT or Codex session. It summarizes where the implementation currently stands relative to the frozen 36-commit plan and the master project specification originally provided as:

- `/home/beastly713/Downloads/DIP-Workbench-36-Commit-Implementation-Plan.md`
- `/home/beastly713/Downloads/Project-details-latest.md`

## Repository Location

Use this as the project root:

```bash
/home/beastly713/ip-work/dip-work-bench
```

Important history note: earlier work accidentally treated `/home/beastly713/ip-work` as the root. That was corrected. The actual Python package, tests, scripts, docs, and Git repository state for DIP Workbench live under `dip-work-bench`.

Current branch and C12 implementation base:

```text
Branch: main
HEAD: 04c84f3 feat(ui): add comparison graph table matrix and tree views
Remote tracking: origin/main
```

The original C12 implementation is committed at `04c84f3`. The current working tree contains an uncommitted C12 correctness correction for identified comparison, graph rendering, export, and safe-data-state defects. Do not stage, commit, push, create branches, amend history, or rewrite history unless the user explicitly asks.

## Product Contract

DIP Workbench is a Python 3.11 and PySide6 desktop application for demonstrating syllabus-based digital image processing operations.

The frozen product direction from `Project-details-latest.md` is:

- Operation-centred, not experiment-centred.
- Single-window desktop GUI.
- Built for fast professor/evaluator demonstration.
- Uses 11 syllabus modules and exactly 67 user-visible academic tools.
- Library-first implementation using suitable image-processing libraries.
- Supports original-image and current-result processing without forcing sequential workflows.
- Provides operation-specific inputs, parameters, previews, result views, comparisons, metrics, overlays, tables, graphs, reports, and presentation views as appropriate.
- Does not introduce database, server, web frontend, authentication, plugin system, pipeline editor, or deep-learning scope.

The implementation plan controls sequencing only. The master project specification controls product, UI, operation, and architecture decisions.

## Current Commit-Plan Position

The codebase has completed through C12:

```text
C01  chore: scaffold repository and development infrastructure
C02  feat(ui): add the single-window application shell
C03  feat(core): add image assets colour conversion and file io
C04  feat(state): add document preview history and undo redo
C05  feat(ui): add the primary image document workflow
C05 correction  fix(ui): complete primary image workflow coverage
C06  feat(ui): add image transform utilities and region selection
C06 correction  fix(ui): harden transform utilities and region state
C07  feat(operations): add registry input parameter and result contracts
C08  feat(execution): add threaded operation execution
C09  feat(ui): add the generic operation workspace
C10  feat(m03): implement image negative end to end
C11  feat(ui): add navigation search inputs and parameter controls
C11 correction  fix(ui): harden optional inputs and navigation state
C12  feat(ui): add comparison graph table matrix and tree views
```

The next planned implementation commit is C13:

```text
feat(ui): add overlays interactions detail drawers and presenters
```

Do not begin C14 or any later academic module work when implementing C13.

## Registry State

Current registry verification:

```text
Registry valid: 11 modules, 1 operation.
```

Only one academic operation is currently implemented and registered:

```text
M03-01 Image Negative
```

The registry must not count placeholders or unfinished operations as implemented.

Future registry checkpoints from the 36-commit plan:

```text
After C10: 1 academic tool
After C17: 20 academic tools
After C22: 40 academic tools
After C25: 50 academic tools
After C30: 62 academic tools
After C32: 67 academic tools
```

## Implemented Capabilities

### C01-C02 Foundation and Shell

- Python package with `src/dip_workbench`.
- `python -m dip_workbench` application entry point.
- PySide6 `QApplication` startup.
- Dependency-injected application context.
- Logging, settings, temporary directory, and typed error foundations.
- Single `MainWindow` with menu bar, toolbar, navigation sidebar, central page stack, parameter region, and status bar.
- Controlled startup failure dialog.
- Window geometry and panel width persistence.

### C03 Image Foundation

- `ImageAsset` and image conversion helpers.
- RGB internal convention.
- Grayscale, binary mask, label map, and floating display-normalization support.
- OpenCV boundary conversion.
- Image loading and saving for PNG, JPEG, BMP, and TIFF.
- Unicode path support.
- Unsupported/corrupt image handling.

### C04 Document State

- Single-document state with immutable Original image.
- Current Result.
- Non-destructive active preview.
- Auxiliary input store.
- Per-operation session state.
- Lossless temporary PNG snapshots for undo/redo.
- History limit of 25 applied states.
- New primary image invalidates old state safely.

### C05 Primary Image Workflow

- Open primary image.
- Drag-and-drop image opening.
- Save current image.
- Image canvas based on `QGraphicsView`.
- Fit, actual size, zoom, and pan.
- Pixel and image inspector.
- Reset to Original.
- Undo and Redo.
- New-image confirmation and safe empty states.

### C06 Editing Utilities and ROI

- Crop.
- Resize with aspect-ratio handling and interpolation choices.
- Rotate with expanded or cropped canvas modes.
- Flip and mirror.
- Rectangular region selection with full-resolution coordinate mapping.
- Non-destructive utility previews.
- Applied utility transforms enter normal history.
- ROI can remain available without necessarily cropping the image.

### C07 Operation Contracts

- Permanent module and operation IDs.
- `OperationDefinition`.
- `InputSpec`.
- `ParameterSpec` and parameter schemas.
- Conditional parameter visibility/enabling.
- Typed artifacts and operation results.
- Apply candidates.
- Operation registry.
- Duplicate-ID and registry validation support.
- Search aliases.

### C08 Execution

- Shared `QThreadPool` execution.
- Preview and full-resolution task requests.
- Cancellation tokens.
- Progress callbacks.
- Typed success, failure, and cancellation outcomes.
- Debounced previews.
- Latest-preview-wins behavior.
- Stale-result protection.
- Reduced-resolution preview foundation.
- Full-resolution execution on Apply.

### C09 Generic Operation Workspace

- Operation header.
- Generic input strip.
- Original and Current Result input choices.
- Parameter panel host.
- Preview or Run action.
- Apply action.
- Reset Parameters.
- Result workspace host.
- Inline validation and failure states.
- Operation controller integrated with document state and execution manager.

### C10 M03-01 Image Negative

- M03-01 registered as the first academic operation.
- Supports grayscale and RGB images.
- Colour handling modes include luminance-only, per-channel, and grayscale-output behavior as implemented.
- Immediate non-destructive preview.
- Side-by-side input/result presentation.
- Collapsible transformation curve.
- Apply reruns at full resolution and creates one undoable history entry.
- Export, Undo, Redo, and document workflow integration.

### C11 Navigation and Configuration UI

- All eleven permanent syllabus modules shown in navigation and Home.
- Registry-backed operation availability.
- Accordion module navigation.
- Collapsed numbered module mode.
- Active module and operation styling.
- Operation search over IDs, names, descriptions, aliases, and module names.
- `Ctrl+K` focuses operation search and reveals the sidebar.
- Home module cards.
- Session-only recent operations.
- Auxiliary/reference image loading through input strip.
- Single-image, dual-image, reference, dataset, and interactive input summaries.
- Generated parameter editor for integers, floats, checkboxes, radio groups, dropdowns, ranges, numeric lists, advanced settings, dynamic conditions, and kernels.
- Valid parameter changes can refresh preview automatically.

### C11 Correction

- Optional inputs now validate correctly:
  - Missing required input fails.
  - Missing optional input succeeds even when `minimum_count` defaults to 1.
  - Optional multiple input with a minimum count is valid with zero items but enforces the minimum once any value is provided.
- Input-strip requirement text uses `InputSpec.required`, not `minimum_count`, to decide required versus optional wording.
- Navigation active state now reflects the real active academic operation across:
  - operation button,
  - module header,
  - collapsed module number button.
- Entering utility mode clears academic active-operation styling without clearing recent operations.
- Returning to M03-01 restores M03/M03-01 active indication.

### C12 Comparison, Visualization, and Export

- Shared PySide-free visualization contracts and adapters for graphs, histograms, tables, matrices, and trees.
- PyQtGraph 0.14.0 dependency added for analytical graph and heatmap rendering.
- Shared side-by-side comparison widget with permanent labels, synchronized zoom/pan, fit/100%/zoom controls, and panel maximization.
- Triple comparison widget infrastructure for three semantic images.
- Equal-dimension split comparison canvas with a genuine overlaid divider.
- Before/After comparison widget with side-by-side default, split mode, and scoped hold `B` to view Input behavior.
- M03-01 Image Negative now uses the shared comparison widget and shared transformation-curve graph.
- Displayed export target contract added to operation presenters and `ResultWorkspaceHost`.
- One injected `ExportService` owns artifact file writing.
- Displayed-result export supports images, graphs, tables, matrices, metrics, text, bitstreams, and trees.
- Raw label-map image export is rejected clearly until later explicit label-map display mapping exists.
- C12 correction fixes export suffix precedence, histogram CSV adaptation, hidden presenter export targets, RGB-to-grayscale split compatibility, split labels, true step graph rendering, graph PNG export scaling, owned-only view-transform disconnects, malformed-data inline states, and the deprecated table filter invalidation path.

## Not Yet Implemented

The following major plan areas are still pending:

- C13 overlays, interactive canvas modes, details drawer, and seven reusable presenter templates.
- C14-C17 modules 1-4.
- C18-C22 modules 5-8.
- C23-C25 module 9 segmentation.
- C26-C30 module 10 feature extraction and shape analysis.
- C31-C32 module 11 compression and quality analysis.
- C33 curated sample library and acceptance automation.
- C34 report collection and PDF export.
- C35 Presentation Mode, help, and final UI polish.
- C36 release hardening and packaging.

Specific features that must not be assumed complete:

- Additional operation-specific presenter templates beyond the C12 reusable widgets.
- Overlays, markers, seed tools, brushes, block selection, or contour/keypoint inspection.
- Report entry model or PDF export.
- Presentation Mode.
- Sample library.
- Any academic operation other than M03-01 Image Negative.

## Current Architecture Map

Key implementation areas:

```text
src/dip_workbench/application.py
src/dip_workbench/core/
src/dip_workbench/services/
src/dip_workbench/state/
src/dip_workbench/controllers/
src/dip_workbench/execution/
src/dip_workbench/operations/
src/dip_workbench/operations/m03/image_negative.py
src/dip_workbench/ui/
src/dip_workbench/ui/pages/
src/dip_workbench/ui/panels/
src/dip_workbench/ui/widgets/
src/dip_workbench/ui/operations/
```

Important tests:

```text
tests/unit/test_application.py
tests/unit/test_image_asset.py
tests/unit/test_image_io_service.py
tests/unit/test_document_store.py
tests/unit/test_document_controller.py
tests/unit/test_operation_controller.py
tests/unit/operations/
tests/unit/operations/test_visualization.py
tests/unit/services/test_export_service.py
tests/unit/execution/
tests/gui/test_main_window.py
tests/gui/test_primary_image_workflow.py
tests/gui/test_transform_workflow.py
tests/gui/test_operation_inputs.py
tests/gui/test_operation_navigation.py
tests/gui/test_image_negative_flow.py
```

## Development Commands

From the repository root:

```bash
cd /home/beastly713/ip-work/dip-work-bench
```

Use the existing virtual environment when present:

```bash
PATH="$PWD/.venv/bin:$PATH"
```

Standard checks:

```bash
ruff format --check .
ruff check .
mypy src
pytest -q
QT_QPA_PLATFORM=offscreen pytest tests/gui -q
python scripts/verify_registry.py
python scripts/check.py
```

Manual/offscreen launch check:

```bash
QT_QPA_PLATFORM=offscreen python -m dip_workbench
```

When running via the local venv in this environment, this form has been useful:

```bash
PATH="$PWD/.venv/bin:$PATH" QT_QPA_PLATFORM=offscreen python -m dip_workbench
```

For offscreen launch checks, DBus/offscreen plugin warnings can appear. The important result is that the application window initializes without an uncaught exception.

## Last Known Validation

After the C12 correction, the project had the following known-good validation state:

```text
python -m pip install -e ".[dev]"
python -c "import pyqtgraph; print(pyqtgraph.__version__)"
ruff format .
ruff format --check .
ruff check .
mypy src
python scripts/verify_registry.py
pytest tests/unit/operations/test_visualization.py -q
pytest tests/unit/services/test_export_service.py -q
pytest tests/unit/test_application.py -q
QT_QPA_PLATFORM=offscreen pytest tests/gui/test_comparison_views.py -q
QT_QPA_PLATFORM=offscreen pytest tests/gui/test_graph_widgets.py -q
QT_QPA_PLATFORM=offscreen pytest tests/gui/test_export_integration.py -q
QT_QPA_PLATFORM=offscreen pytest tests/gui/test_image_negative_flow.py -q
QT_QPA_PLATFORM=offscreen pytest tests/gui/test_main_window.py -q
pytest -q
QT_QPA_PLATFORM=offscreen pytest tests/gui -q
python scripts/check.py
python scripts/verify_environment.py
git diff --check
```

Known results at that point:

```text
PyQtGraph: 0.14.0
Registry valid: 11 modules, 1 operation.
Full pytest: 222 passed, 1 skipped.
GUI suite: 53 passed.
ruff check: pass.
mypy src: pass.
python scripts/check.py: pass.
python scripts/verify_environment.py: pass.
git diff --check: pass.
```

No `invalidateFilter()` deprecation warning was present in the focused or complete GUI runs.

## GitHub Action Status

The GitHub Actions quality workflow was intentionally paused earlier at the user's request. Do not re-enable or modify `.github/workflows/quality.yml` unless the user explicitly asks.

## Current Practical Guidance for the Next Chat

If continuing implementation, start by checking:

```bash
pwd
git status --short --branch
git log --oneline --decorate -12
python scripts/verify_registry.py
```

Then read the next packet from the user. If the next packet is C13, keep the scope to overlays, interaction modes, details drawer, and presenter templates. Do not implement new academic operations unless the packet explicitly moves into C14-C17.

If making changes, do not stage, commit, push, create branches, amend commits, or rewrite history unless the user explicitly asks. The implementation packets usually ask for code changes only and a concise report.

## Notes and Small Inconsistencies

- The project currently depends on NumPy, OpenCV headless, PySide6, and PyQtGraph. Later master-spec dependencies such as SciPy, scikit-image, scikit-learn, mahotas, and ReportLab are not yet all present in `pyproject.toml`.
- The production registry intentionally exposes only implemented academic operations. Showing all 11 module groups in the UI does not mean all 67 tools are registered.
