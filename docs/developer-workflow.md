# Developer Workflow

This page documents the standard development workflow, quality gates, and commands.

## Toolchain

| Tool | Purpose | Command |
|------|---------|---------|
| **uv** | Package/env management | `uv sync` |
| **ruff** | Linting + formatting | `uv run ruff check .` / `uv run ruff format .` |
| **pytest** | Testing | `uv run pytest` |
| **pyright** | Type checking | `uv run pyright` |
| **pre-commit** | Git hooks | `pre-commit run --all-files` |
| **mkdocs** | Documentation | `uv run mkdocs build` |

## Setup

Install all dev dependencies:

```bash
uv sync --extra dev
```

Install pre-commit hooks (optional but recommended):

```bash
uv run pre-commit install
```

## Quality Gates

Run all checks before committing:

```bash
# Lint
uv run ruff check .

# Format (apply changes)
uv run ruff format .

# Format (check only, for CI)
uv run ruff format --check .

# Tests (unit tests only, integration tests require live server)
uv run pytest -v

# Type check
uv run pyright

# Docs build
uv run mkdocs build
```

### One-liner for all checks

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest -v && uv run pyright && uv run mkdocs build
```

## Running Integration Tests

Integration tests require a live server. They are skipped by default.

1. Start the server:

    ```bash
    uv run uvicorn --app-dir=app app:app --port 8000
    ```

2. In another terminal, run integration tests:

    ```bash
    uv run pytest -m integration -v
    ```

## Pre-commit Hooks

The project uses pre-commit to enforce quality gates before commits. Hooks include:

- **ruff check** — linting
- **ruff format** — code formatting

To run manually:

```bash
uv run pre-commit run --all-files
```

## Adding Dependencies

Add a runtime dependency:

```bash
uv add <package>
```

Add a dev dependency:

```bash
uv add --group dev <package>
```

After adding dependencies, commit the updated `pyproject.toml` and `uv.lock`.

## Type Checking Notes

- Pyright is configured with `typeCheckingMode = "basic"` in `pyproject.toml`
- Future migration to [ty](https://github.com/astral-sh/ty) is planned (CI job name `typecheck` is stable for this)
