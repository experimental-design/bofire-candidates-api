# CI Overview

This page documents the GitHub Actions CI workflow and how to troubleshoot failures.

## Workflow Structure

The CI is defined in `.github/workflows/ci.yaml` and runs on every push/PR to `main`.

### Jobs

| Job | Description | Matrix |
|-----|-------------|--------|
| `lint` | Runs `uv run ruff check .` | Python 3.12 |
| `format-check` | Runs `uv run ruff format --check .` | Python 3.12 |
| `typecheck` | Runs `uv run pyright` | Python 3.12 |
| `unit-tests` | Runs `uv run pytest -v` (no server) | Python 3.12, 3.13 |
| `integration-tests` | Starts server + runs `uv run pytest -m integration -v` | Python 3.12, 3.13 |
| `docs` | Runs `uv run mkdocs build --strict` (conditional) | Python 3.12 |

### Caching

All jobs use `astral-sh/setup-uv` with caching enabled:

```yaml
- uses: astral-sh/setup-uv@v2
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
```

Cache is invalidated when `uv.lock` changes.

## Reproducing CI Locally

Run the same commands CI runs:

```bash
# Lint
uv run ruff check .

# Format check
uv run ruff format --check .

# Type check
uv run pyright

# Unit tests
uv run pytest -v

# Integration tests (requires server running)
uv run uvicorn --app-dir=app app:app --port 8000 &
sleep 5
uv run pytest -m integration -v

# Docs
uv run mkdocs build --strict
```

## Adding New CI Jobs

1. Edit `.github/workflows/ci.yaml`
2. Follow the existing pattern (checkout → setup-python → setup-uv → uv sync → run command)
3. Keep jobs focused (one responsibility per job)

## CI Best Practices

- **Keep jobs independent**: Each job should be self-contained
- **Use matrix for Python versions**: Only for test jobs, not lint/format
- **Cache dependencies**: Use `cache-dependency-glob: "uv.lock"` for fast restores
- **Fail fast**: Default behavior; disable with `fail-fast: false` if needed

## Workflow Triggers

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

Runs on:

- Pushes to `main`
- Pull requests targeting `main`
