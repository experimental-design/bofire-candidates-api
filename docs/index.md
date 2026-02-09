# Getting Started

BoFire Candidates API is a FastAPI-based service for generating optimization candidates using [BoFire](https://github.com/experimental-design/bofire).

## Prerequisites

- **Python**: >= 3.12
- **uv**: Package and environment manager ([install guide](https://docs.astral.sh/uv/getting-started/installation/))

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/experimental-design/bofire-candidates-api.git
cd bofire-candidates-api
uv sync --extra dev
```

## Running the Server

Start the FastAPI server:

```bash
uv run uvicorn --app-dir=app app:app --port 8000
```

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger UI.

## Running the Worker (Optional)

For asynchronous candidate generation, start a worker in a separate terminal:

```bash
uv run python -m worker
```

## Quick Test

Verify the installation by running the test suite:

```bash
uv run pytest -v
```

Expected output:

```
tests/test_candidates.py::test_candidates_missing_experiments PASSED
tests/test_candidates.py::test_candidates_generate PASSED
tests/test_models.py::test_invalid_experiments[CandidatesRequest] PASSED
...
8 passed, 2 deselected
```

## Next Steps

- [Developer Workflow](developer-workflow.md) — linting, formatting, testing, type checking
- [Architecture](architecture.md) — module structure and extension points
- [Troubleshooting](troubleshooting.md) — common issues and solutions
