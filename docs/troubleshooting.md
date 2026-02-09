# Troubleshooting

Common issues and solutions for local development and CI.

## Local Development

### `uv sync` fails

**Symptom**: `uv sync` fails with dependency resolution errors.

**Solutions**:

1. Ensure Python >= 3.12 is installed:
   ```bash
   python --version
   ```

2. Clear uv cache and retry:
   ```bash
   uv cache clean
   uv sync --extra dev
   ```

3. Delete `.venv` and recreate:
   ```bash
   rm -rf .venv
   uv sync --extra dev
   ```

### Port 8000 already in use

**Symptom**: `uvicorn` fails with "Address already in use".

**Solutions**:

```bash
# Find and kill the process (Linux/macOS)
lsof -i :8000
kill -9 <PID>

# Windows PowerShell
Get-Process -Name python | Stop-Process -Force
```

Or use a different port:

```bash
uv run uvicorn --app-dir=app app:app --port 8001
```

### Integration tests fail with connection error

**Symptom**: Tests fail with "Could not connect to http://localhost:8000".

**Cause**: Server is not running.

**Solution**: Start the server before running integration tests:

```bash
# Terminal 1
uv run uvicorn --app-dir=app app:app --port 8000

# Terminal 2
uv run pytest -m integration -v
```

### Database state issues

**Symptom**: Tests fail due to stale data in `db.json`.

**Solution**: Delete the database file:

```bash
rm db.json
```

Unit tests use isolated temp databases automatically.

## CI Failures

### Lint failures

**Symptom**: `lint` job fails.

**Solution**: Run locally and fix issues:

```bash
uv run ruff check . --fix
uv run ruff format .
```

### Format check failures

**Symptom**: `format-check` job fails.

**Solution**: Format code locally:

```bash
uv run ruff format .
```

### Type check failures

**Symptom**: `typecheck` job fails with pyright errors.

**Solution**: Run locally to see errors:

```bash
uv run pyright
```

Fix type errors or add `# type: ignore` comments for false positives.

### Integration tests fail in CI

**Symptom**: `integration-tests` job fails but passes locally.

**Possible causes**:

1. **Server startup timing**: CI waits 15 seconds; may need more time
2. **Port conflicts**: Unlikely in CI, but check logs
3. **Database state**: Each CI run starts fresh

**Debug**: Check the CI logs for specific error messages.

### Docs build fails

**Symptom**: `docs` job fails with mkdocs errors.

**Solutions**:

1. Run locally to see errors:
   ```bash
   uv run mkdocs build --strict
   ```

2. Common issues:
   - Missing files referenced in `nav`
   - Broken internal links (use `--strict` to catch)
   - Invalid YAML in `mkdocs.yml`

## Getting Help

1. Check the [BoFire documentation](https://experimental-design.github.io/bofire/)
2. Open an issue on [GitHub](https://github.com/experimental-design/bofire-candidates-api/issues)
