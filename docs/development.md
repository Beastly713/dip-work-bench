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

In C01 these entry points perform a headless infrastructure bootstrap: they configure metadata,
logging, settings, and a temporary session, then cleanly release resources and exit. They do not
create a Qt application or window. The graphical application shell begins in C02.

Codex must not commit or push repository changes. Staging, branch changes, and pull-request
creation also remain user-controlled.
