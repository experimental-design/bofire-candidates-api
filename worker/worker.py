import json
import logging
import multiprocessing as mp
import time
from typing import Dict, Optional, Tuple

import bofire.strategies.api as strategies
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
        Tuple[int, AnyStrategy, int, Optional[Experiments], Optional[Candidates]]
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


class Worker(BaseModel):
    client: Client
    job_check_interval: float
    round: int = 0

    def sleep(self, sleep_time_sec: float, msg: str = ""):
        logging.debug(f"Sleeping for {sleep_time_sec} second(s) ({msg})")
        time.sleep(sleep_time_sec)

    def work(self):
        while True:
            self.work_round()

    @staticmethod
    def process_proposal(
        id: int,
        strategy_data: AnyStrategy,
        n_candidates: int,
        experiments: Experiments,
        pendings: Candidates,
        conn_obj: "mp.connection.Connection",
    ):
        try:
            strategy = strategies.map(strategy_data)
            if experiments is not None:
                strategy.tell(experiments.to_pandas())
            df_candidates = strategy.ask(n_candidates)
            msg = Candidates.from_pandas(df_candidates, strategy_data.domain)
        except Exception as e:
            msg = Exception(str(e))
        finally:
            conn_obj.send(msg)

    def work_round(self):
        logging.debug(f"Starting round {self.round}")
        self.round += 1
        proposal = self.client.claim_proposal()
        if proposal is None:
            logging.debug("No proposal to work on")
            self.sleep(self.job_check_interval, msg="No proposal to work on.")
            return

        proposal_id, strategy_data, n_candidates, experiments, pendings = proposal
        logging.info(f"Claimed proposal {proposal_id}")

        try:
            receiver, sender = mp.Pipe(False)
            proc = mp.Process(
                target=self.process_proposal,
                args=(
                    proposal_id,
                    strategy_data,
                    n_candidates,
                    experiments,
                    pendings,
                    sender,
                ),
            )
            proc.start()

            while True:
                if receiver.poll(timeout=self.job_check_interval):
                    candidates = receiver.recv()
                    if isinstance(candidates, Exception):
                        raise candidates
                    else:
                        self.client.mark_processed(proposal_id, candidates=candidates)
                        logging.info(f"Proposal {proposal_id} processed successfully")
                        break
        except Exception as e:
            logging.error(f"Error processing proposal {proposal_id}: {e}")
            self.client.mark_failed(proposal_id, error_message=str(e))
