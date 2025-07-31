import json

import pytest
from bofire.benchmarks.api import Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import RandomStrategy, SoboStrategy

from bofire_candidates_api.api_data_models import CandidatesProposal, CandidatesRequest
from tests.conftest import Client
from worker.worker import Client as WorkerClient
from worker.worker import Worker


def test_client(client: Client):
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
    client.post(path="/proposals", request_body=pr.model_dump_json())
    proposal = worker_client.claim_proposal()
    assert proposal.n_candidates == 5
    assert isinstance(proposal.strategy_data, RandomStrategy)
    assert proposal.experiments is None
    assert proposal.pendings is None

    # test mark failed
    worker_client.mark_failed(proposal_id=proposal.id, error_message="error")
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FAILED"

    # test mark processed
    worker_client.mark_processed(
        proposal_id=proposal.id,
        candidates=Candidates.from_pandas(candidates, bench.domain),
    )
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FINISHED"


def test_worker(client: Client):
    bench = Himmelblau()

    # successful random sampling proposal
    pr = CandidatesRequest(
        strategy_data=RandomStrategy(domain=bench.domain),
        n_candidates=5,
        experiments=None,
        pendings=None,
    )

    response = client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker = Worker(client=WorkerClient(), job_check_interval=2)

    worker.work_round()
    status = json.loads(client.get(path=f"/proposals/{id}/state").content)
    assert status == "FINISHED"
    candidates = Candidates(
        **json.loads(client.get(path=f"/proposals/{id}/candidates").content)
    )
    assert len(candidates.rows) == 5

    # failing sobo
    pr = CandidatesRequest(
        strategy_data=SoboStrategy(domain=bench.domain),
        n_candidates=1,
        experiments=None,
        pendings=None,
    )
    response = client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker.work_round()
    status = json.loads(client.get(path=f"/proposals/{id}/state").content)
    assert status == "FAILED"
    proposal = CandidatesProposal(
        **json.loads(client.get(path=f"/proposals/{id}").content)
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
    response = client.post(path="/proposals", request_body=pr.model_dump_json())
    id = CandidatesProposal(**json.loads(response.content)).id

    worker.work_round()
    status = json.loads(client.get(path=f"/proposals/{id}/state").content)
    assert status == "FINISHED"
    candidates = Candidates(
        **json.loads(client.get(path=f"/proposals/{id}/candidates").content)
    )
    assert len(candidates.rows) == 1
