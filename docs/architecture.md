# Architecture

This page describes the module structure, boundaries, and extension points.

## Overview

```
bofire-candidates-api/
├── app/                          # FastAPI application (HTTP layer)
│   ├── app.py                    # FastAPI app entry point
│   └── routers/
│       ├── candidates.py         # /candidates endpoints
│       └── proposals.py          # /proposals endpoints (async workflow)
├── bofire_candidates_api/        # Core library (domain logic)
│   ├── data_models.py            # Pydantic models (CandidatesRequest, CandidatesProposal)
│   ├── generate.py               # Candidate generation logic
│   └── worker.py                 # Worker client and background processor
├── worker/                       # Worker entry point
│   └── __main__.py               # `python -m worker` entry
├── tests/                        # Test suite
└── docs/                         # Documentation (MkDocs)
```

## Module Boundaries

### `bofire_candidates_api/` (Core)

Pure domain logic, no HTTP/IO concerns:

| Module | Responsibility |
|--------|---------------|
| `data_models.py` | Pydantic models for requests and proposals |
| `generate.py` | Candidate generation using BoFire strategies |
| `worker.py` | `Worker` class (polls proposals) + `Client` class (HTTP client) |

### `app/` (HTTP Layer)

FastAPI application and routers:

| Module | Responsibility |
|--------|---------------|
| `app.py` | FastAPI app, health check, version endpoint |
| `routers/candidates.py` | `/candidates/generate` — synchronous generation |
| `routers/proposals.py` | `/proposals` — async workflow with TinyDB persistence |

## Data Flow

### Synchronous Generation

```
Client → POST /candidates/generate → candidates.py → generate.py → Response
```

### Asynchronous Generation (Worker-based)

```
Client → POST /proposals → proposals.py → TinyDB (state: CREATED)
                                              ↓
Worker → polls /proposals/claim → generate.py → TinyDB (state: FINISHED/FAILED)
                                              ↓
Client → GET /proposals/{id}/candidates → Response
```

## Key Data Models

### `CandidatesRequest`

Request payload for candidate generation:

```python
class CandidatesRequest(BaseModel):
    strategy_data: AnyStrategy      # BoFire strategy data model
    n_candidates: int               # Number of candidates to generate
    experiments: Optional[Experiments]  # Prior experiments
    pendings: Optional[Candidates]  # Pending candidates
    n_restarts: int                 # Retry count on failure
```

### `CandidatesProposal`

Stored proposal with state tracking:

```python
class CandidatesProposal(CandidatesRequest):
    id: Optional[int]
    state: ProposalStateEnum        # CREATED, CLAIMED, FINISHED, FAILED
    candidates: Optional[Candidates]
    error_message: Optional[str]
    created_at: datetime
    claimed_at: Optional[datetime]
    finished_at: Optional[datetime]
```

## Extension Points

### Adding a New Endpoint

1. Create a new router in `app/routers/`
2. Include it in `app/app.py` via `app.include_router()`

### Adding a New Strategy Type

BoFire strategies are defined in `bofire.data_models.strategies.api`. The API accepts any `AnyStrategy` via `strategy_data`.

### Custom Persistence

The current implementation uses TinyDB (`db.json`). To switch to a different database:

1. Modify `routers/proposals.py` — replace `get_db()` dependency
2. Update the `test_db` fixture in `tests/conftest.py`

## Dependencies

| Dependency | Purpose |
|------------|---------|
| `bofire` | Bayesian optimization framework |
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `tinydb` | Lightweight JSON database |
| `pydantic` | Data validation (via BoFire) |
