import json

from tests.conftest import Client


def test_versions(client: Client):
    response = client.get(path="/versions")
    assert response.status_code == 200
    assert sorted(json.loads(response.content).keys()) == sorted(
        ["bofire", "bofire_candidates_api"]
    )
