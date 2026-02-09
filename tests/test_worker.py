"""Integration tests for the Worker and WorkerClient classes.

These tests require a live uvicorn server running on localhost:8000.
They are marked as integration tests and skipped by default.

To run these tests:
    1. Start the server: uv run uvicorn --app-dir=app app:app --port 8000
    2. Run with integration marker: uv run pytest -m integration
"""

import json

import pytest
from bofire.benchmarks.api import Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy

from bofire_candidates_api.data_models import CandidatesProposal, CandidatesRequest
from bofire_candidates_api.worker import Client as WorkerClient
from bofire_candidates_api.worker import Worker
from tests.conftest import LiveClient


@pytest.mark.integration
def test_client(live_client: LiveClient):
    bench = Himmelblau()
    candidates = bench.domain.inputs.sample(5)

    pr = CandidatesRequest(
        strategy_data=RandomStrategy(domain=bench.domain),
        n_candidates=5,
        experiments=None,
        pendings=None,
    )

    with pytest.raises(ValueError, match="Could not connect to http://localhost:8001."):
        WorkerClient(url="http://localhost:8001")

    worker_client = WorkerClient(url="http://localhost:8000")

    # test claim proposal
    live_client.post(path="/proposals", request_body=pr.model_dump_json())
    proposal = worker_client.claim_proposal()
    assert proposal is not None, "Expected a proposal to be claimed"
    assert proposal.id is not None, "Claimed proposal must have an ID"
    assert proposal.n_candidates == 5
    assert isinstance(proposal.strategy_data, RandomStrategy)
    assert proposal.experiments is None
    assert proposal.pendings is None

    # test mark failed
    worker_client.mark_failed(proposal_id=proposal.id, error_message="error")
    status = json.loads(live_client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FAILED"

    # test mark processed
    worker_client.mark_processed(
        proposal_id=proposal.id,
        candidates=Candidates.from_pandas(candidates, bench.domain),
    )
    status = json.loads(live_client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FINISHED"


@pytest.mark.integration
def test_worker(live_client: LiveClient):
    bench = Himmelblau()

    # successful random sampling proposal
    pr = CandidatesRequest(
        strategy_data=RandomStrategy(domain=bench.domain),
        n_candidates=5,
        experiments=None,
        pendings=None,
    )

    response = live_client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker = Worker(client=WorkerClient(), job_check_interval=2)

    worker.work_round()
    status = json.loads(live_client.get(path=f"/proposals/{id}/state").content)
    assert status == "FINISHED"
    candidates = Candidates(
        **json.loads(live_client.get(path=f"/proposals/{id}/candidates").content)
    )
    assert len(candidates.rows) == 5

    # failing sobo
    pr = CandidatesRequest(
        strategy_data=SoboStrategy(domain=bench.domain),
        n_candidates=1,
        experiments=None,
        pendings=None,
    )
    response = live_client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker.work_round()
    status = json.loads(live_client.get(path=f"/proposals/{id}/state").content)
    assert status == "FAILED"
    proposal = CandidatesProposal(
        **json.loads(live_client.get(path=f"/proposals/{id}").content)
    )
    assert (
        proposal.error_message
        == "404: Not enough experiments available to execute the strategy."
    )

    # successful sobo
    experiments = Experiments.from_pandas(
        bench.f(bench.domain.inputs.sample(5), return_complete=True), bench.domain
    )
    pr = CandidatesRequest(
        strategy_data=SoboStrategy(domain=bench.domain),
        n_candidates=1,
        experiments=experiments,
        pendings=None,
    )
    response = live_client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker.work_round()
    status = json.loads(live_client.get(path=f"/proposals/{id}/state").content)
    assert status == "FINISHED"
    candidates = Candidates(
        **json.loads(live_client.get(path=f"/proposals/{id}/candidates").content)
    )
    assert len(candidates.rows) == 1
