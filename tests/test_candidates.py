import json
from typing import Optional

from bofire.benchmarks.api import DTLZ2, Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import (
    AlwaysTrueCondition,
    AnyStrategy,
    NumberOfExperimentsCondition,
    RandomStrategy,
    SoboStrategy,
    Step,
    StepwiseStrategy,
)
from pydantic import BaseModel, Field

from tests.conftest import Client


class CandidateRequest(BaseModel):
    strategy_data: AnyStrategy
    n_candidates: int = Field(
        default=1, gt=0, description="Number of candidates to generate"
    )
    experiments: Optional[Experiments]
    pendings: Optional[Candidates]


bench = Himmelblau()
bench2 = DTLZ2(dim=6)
experiments = bench.f(bench.domain.inputs.sample(15), return_complete=True)
experiments2 = bench2.f(bench2.domain.inputs.sample(15), return_complete=True)

strategy_data = StepwiseStrategy(
    domain=bench.domain,
    steps=[
        Step(
            condition=NumberOfExperimentsCondition(n_experiments=10),
            strategy_data=RandomStrategy(domain=bench.domain),
        ),
        Step(
            condition=AlwaysTrueCondition(),
            strategy_data=SoboStrategy(domain=bench.domain),
        ),
    ],
)


def test_candidates_request_validation(client: Client):
    cr = CandidateRequest(
        strategy_data=strategy_data,
        n_candidates=1,
        experiments=Experiments.from_pandas(experiments2, bench2.domain),
        pendings=None,
    )

    response = client.post(
        path="/candidates/generate", request_body=cr.model_dump_json()
    )
    assert response.status_code == 422
    assert (
        json.loads(response.content)["detail"][0]["msg"]
        == "Value error, no col for input feature `y`"
    )


def test_candidates_missing_experiments(client: Client):
    cr = CandidateRequest(
        strategy_data=SoboStrategy(domain=bench.domain),
        n_candidates=1,
        experiments=None,
        pendings=None,
    )
    response = client.post(
        path="/candidates/generate", request_body=cr.model_dump_json()
    )
    assert response.status_code == 404
    assert (
        json.loads(response.content)["detail"]
        == "Not enough experiments available to execute the strategy."
    )


def test_candidates_generate(client: Client):
    cr = CandidateRequest(
        strategy_data=strategy_data,
        n_candidates=2,
        experiments=None,
        pendings=None,
    )
    response = client.post(
        path="/candidates/generate", request_body=cr.model_dump_json()
    )
    df_candidates = Candidates(**json.loads(response.content)).to_pandas()
    assert df_candidates.shape[0] == 2
    assert df_candidates.shape[1] == 2
    assert sorted(df_candidates.columns.tolist()) == sorted(
        bench.domain.inputs.get_keys()
    )

    cr = CandidateRequest(
        strategy_data=strategy_data,
        n_candidates=1,
        experiments=Experiments.from_pandas(experiments, bench.domain),
        pendings=None,
    )
    response = client.post(
        path="/candidates/generate", request_body=cr.model_dump_json()
    )
    df_candidates = Candidates(**json.loads(response.content)).to_pandas()
    assert df_candidates.shape[0] == 1
    assert df_candidates.shape[1] == 5
    assert sorted(df_candidates.columns.tolist()) == sorted(
        bench.domain.candidate_column_names
    )
