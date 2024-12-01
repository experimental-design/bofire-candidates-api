import json

from bofire.benchmarks.api import Himmelblau
from bofire.data_models.candidates_api.api import Proposal, ProposalRequest
from bofire.data_models.dataframes.api import Candidates
from bofire.data_models.strategies.api import RandomStrategy

from tests.conftest import Client


def test_proposals(client: Client):
    bench = Himmelblau()
    candidates = bench.domain.inputs.sample(5)

    FAKE_ID = 9999

    pr = ProposalRequest(
        strategy_data=RandomStrategy(domain=bench.domain),
        n_candidates=5,
        experiments=None,
        pendings=None,
    )
    response = client.post(path="/proposals", request_body=pr.model_dump_json())
    assert response.status_code == 200
    proposal = Proposal(**json.loads(response.content))

    # get proposal back
    loaded_proposal = Proposal(
        **json.loads(client.get(path=f"/proposals/{proposal.id}").content)
    )
    # compare them
    assert proposal == loaded_proposal
    # check on error when ID does not exist
    response = client.get(path=f"/proposals/{FAKE_ID}")
    assert response.status_code == 404

    # get the status
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "CREATED"
    # check on error when ID does not exist
    response = client.get(path=f"/proposals/{FAKE_ID}/status")
    assert response.status_code == 404

    # claim the proposal
    response = json.loads(client.get(path="/proposals/claim").content)
    assert response[0] == proposal.id

    # get the status again
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "CLAIMED"

    # mark as failed
    client.post(
        path=f"/proposals/{proposal.id}/mark_failed",
        request_body=json.dumps({"msg": "error"}),
    )

    # get the status again
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FAILED"

    # mark wrong id as failed
    response = client.post(
        path=f"/proposals/{FAKE_ID}/mark_failed",
        request_body=json.dumps({"msg": "error"}),
    )
    assert response.status_code == 404

    # get candidates for the proposal
    response = client.get(path=f"/proposals/{proposal.id}/candidates")
    assert response.status_code == 404
    assert response.json()["detail"] == "Candidates not found"

    # mark as procesed
    response = client.post(
        path=f"/proposals/{proposal.id}/mark_processed",
        request_body=Candidates.from_pandas(candidates, bench.domain).model_dump_json(),
    )
    # get the status again
    status = json.loads(client.get(path=f"/proposals/{proposal.id}/state").content)
    assert status == "FINISHED"

    # mark wrong id as processed
    response = client.post(
        path=f"/proposals/{FAKE_ID}/mark_processed",
        request_body=Candidates.from_pandas(candidates, bench.domain).model_dump_json(),
    )
    assert response.status_code == 404

    # get the candidates
    loaded_candidates = Candidates(
        **json.loads(client.get(path=f"/proposals/{proposal.id}/candidates").content)
    ).to_pandas()
    assert len(loaded_candidates) == 5

    # get candidates from wrong id
    response = client.get(path=f"/proposals/{FAKE_ID}/candidates")
    assert response.status_code == 404
