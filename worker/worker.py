import logging
import multiprocessing as mp
import time

import bofire.strategies.api as strategies
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from client import Client
from pydantic import BaseModel


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
                        logging.info(f"Proposal {proposal_id} processed successfully")
                        self.client.mark_processed(proposal_id, candidates=candidates)
                        break
        except Exception as e:
            logging.error(f"Error processing proposal {proposal_id}: {e}")
            self.client.mark_failed(proposal_id, error_message=str(e))
