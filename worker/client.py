import json
from typing import Dict, Optional, Tuple

import requests
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from pydantic import BaseModel, TypeAdapter, model_validator


class Client(BaseModel):
    url: str = "http://localhost:8000"

    @model_validator(mode="after")
    def validate_url(self):
        try:
            self.get_version()
        except Exception:
            raise ValueError(f"Could not connect to {self.url}.")
        return self

    @property
    def headers(self):
        return {"accept": "application/json", "Content-Type": "application/json"}

    def get(self, path: str) -> requests.Response:
        return requests.get(f"{self.url}{path}", headers=self.headers)

    def post(self, path: str, request_body: Dict) -> requests.Response:
        return requests.post(
            f"{self.url}{path}", json=request_body, headers=self.headers
        )

    def get_version(self) -> str:
        response = self.get("/versions")
        return response.json()

    def claim_proposal(
        self,
    ) -> Optional[
        Tuple[int, int, AnyStrategy, Optional[Experiments], Optional[Candidates]]
    ]:
        response = self.get(
            "/proposals/claim",
        )
        if response.status_code == 404:
            return None
        loaded_response = json.loads(response.content)

        return (
            loaded_response[0],  # id
            TypeAdapter(AnyStrategy).validate_python(
                loaded_response[1]
            ),  # strategy_data
            loaded_response[2],  # n_candidates
            Experiments(**loaded_response[3])  # experiments
            if loaded_response[3] is not None
            else None,
            Candidates(**loaded_response[4])  # pendings
            if loaded_response[4] is not None
            else None,
        )

    def mark_processed(self, proposal_id: int, candidates: Candidates):
        response = self.post(
            f"/proposals/{proposal_id}/mark_processed",
            request_body=candidates.model_dump(),
        )
        return response.json()

    def mark_failed(self, proposal_id: int, error_message: str):
        response = self.post(
            f"/proposals/{proposal_id}/mark_failed", request_body={"msg": error_message}
        )
        return response.json()
