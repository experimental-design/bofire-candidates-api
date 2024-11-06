import json

from tests.conftest import Client


def test_candidates_request_validation(client: Client):
    response = client.get(path="/versions")
    assert response.status_code == 200
    assert list(json.loads(response.content).keys()) == ["bofire"]
