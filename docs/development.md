# Development Guide

Run commands from the repository root.

## Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Launch

```bash
python -m dip_workbench
dip-workbench
```

For headless smoke checks:

```bash
QT_QPA_PLATFORM=offscreen python -m dip_workbench
```

## Focused Validation

```bash
ruff format --check .
ruff check .
mypy src
python scripts/verify_registry.py
```

Run focused unit and GUI tests for the area changed. Use the full suite for structural changes:

```bash
pytest -q
QT_QPA_PLATFORM=offscreen pytest tests/gui -q
```

## Operation Testing Policy

For each future operation commit, normally add:

- one algorithm correctness or invariant test;
- one validation or edge-case test when the operation needs it;
- one focused GUI workflow smoke test when the operation has meaningful UI;
- manual testing in the running application.

Avoid broad parameter matrices and tests of trivial getters, static labels, or framework plumbing.
