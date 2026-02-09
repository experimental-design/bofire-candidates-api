"""Test fixtures for the BoFire Candidates API tests.

Uses FastAPI TestClient to run tests without requiring a live uvicorn server.
Integration tests use a live server via the `live_client` fixture.
"""

import importlib
import os
import sys
import tempfile
from typing import Callable, Generator

import requests
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import fixture
from tinydb import TinyDB


# Add app directory to path so we can import the FastAPI app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

# Import modules dynamically after path is set up
_app_module = importlib.import_module("app")
_proposals_module = importlib.import_module("routers.proposals")

# Get the FastAPI app instance and db dependency
_app: FastAPI = _app_module.app  # type: ignore[attr-defined]
_get_db: Callable[[], Generator[TinyDB, None, None]] = _proposals_module.get_db  # type: ignore[attr-defined]


HEADERS = {"accept": "application/json", "Content-Type": "application/json"}


class Client:
    """Test client wrapper that provides a consistent interface for tests.

    Wraps FastAPI's TestClient to provide the same interface as the old
    requests-based client, allowing tests to remain unchanged.
    """

    def __init__(self, test_client: TestClient):
        self.test_client = test_client

    def get(self, path: str):
        """Send a GET request to the API.

        Args:
            path: The endpoint path to send the request to.

        Returns:
            The response from the API.
        """
        return self.test_client.get(path)

    def post(self, path: str, request_body: str):
        """Send a POST request to the API.

        Args:
            path: The endpoint path to send the request to.
            request_body: The JSON body of the request as a string.

        Returns:
            The response from the API.
        """
        return self.test_client.post(
            path,
            content=request_body,
            headers={"Content-Type": "application/json"},
        )


class LiveClient:
    """Client for integration tests that talks to a live server via requests.

    This is used for integration tests that require a running uvicorn server.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def get(self, path: str) -> requests.Response:
        """Send a GET request to the live API."""
        return requests.get(f"{self.base_url}{path}", headers=HEADERS)

    def post(self, path: str, request_body: str) -> requests.Response:
        """Send a POST request to the live API."""
        return requests.post(
            f"{self.base_url}{path}", data=request_body, headers=HEADERS
        )


@fixture
def test_db() -> Generator[TinyDB, None, None]:
    """Create a temporary database for test isolation.

    Yields:
        A TinyDB instance backed by a temporary file.
    """
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        db_path = f.name

    db = TinyDB(db_path, default=str)
    try:
        yield db
    finally:
        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)


@fixture
def client(test_db: TinyDB) -> Generator[Client, None, None]:
    """Create a test client with an isolated database.

    Args:
        test_db: The temporary database fixture.

    Yields:
        A Client instance wrapping FastAPI's TestClient.
    """

    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Don't close here; test_db fixture handles cleanup

    _app.dependency_overrides[_get_db] = override_get_db

    with TestClient(_app) as test_client:
        yield Client(test_client)

    _app.dependency_overrides.clear()


@fixture
def live_client() -> LiveClient:
    """Create a client for integration tests that talks to a live server.

    This fixture is used for integration tests that require a running
    uvicorn server on localhost:8000.

    Returns:
        A LiveClient instance for making requests to the live server.
    """
    base_url = os.getenv("CANDIDATES_URL", "http://localhost:8000")
    return LiveClient(base_url=base_url)
