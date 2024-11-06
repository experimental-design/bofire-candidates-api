import os

import requests
from pytest import fixture


HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


class Client:
    def __init__(self, base_url: str, requests=requests):
        self.base_url = base_url
        self.requests = requests

    def get(self, path: str) -> requests.Response:
        return self.requests.get(f"{self.base_url}{path}", headers=HEADERS)

    def post(self, path: str, request_body: str) -> requests.Response:
        return self.requests.post(
            f"{self.base_url}{path}", data=request_body, headers=HEADERS
        )


@fixture
def client() -> Client:
    return Client(base_url=os.getenv("CANDIDATES_URL", "http://localhost:8000"))
