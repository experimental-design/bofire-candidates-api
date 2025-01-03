import datetime

import pytest
from bofire.benchmarks.api import DTLZ2, Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import MoboStrategy, SoboStrategy

from app.models.candidates import CandidateRequest
from app.models.proposals import Proposal, ProposalRequest, StateEnum


@pytest.mark.parametrize("data_model", [CandidateRequest, ProposalRequest])
def test_invalid_experiments(data_model):
    bench = Himmelblau()
    bench2 = DTLZ2(dim=6)
    experiments2 = bench2.f(bench2.domain.inputs.sample(15), return_complete=True)
    with pytest.raises(ValueError):
        data_model(
            strategy_data=SoboStrategy(domain=bench.domain),
            n_candidates=1,
            experiments=Experiments.from_pandas(experiments2, bench2.domain),
            pendings=None,
        )


@pytest.mark.parametrize("data_model", [CandidateRequest, ProposalRequest])
def test_invalid_pendings(data_model):
    bench = Himmelblau()
    bench2 = DTLZ2(dim=6)
    candidates = bench.domain.inputs.sample(15)
    with pytest.raises(ValueError):
        data_model(
            strategy_data=MoboStrategy(domain=bench2.domain),
            n_candidates=1,
            experiments=None,
            pendings=Candidates.from_pandas(candidates, bench.domain),
        )


def test_invalid_candidates():
    bench = Himmelblau()
    bench2 = DTLZ2(dim=6)
    candidates = bench.domain.inputs.sample(5)
    with pytest.raises(ValueError):
        Proposal(
            strategy_data=MoboStrategy(domain=bench2.domain),
            n_candidates=5,
            experiments=None,
            pendings=None,
            state=StateEnum.CREATED,
            created_at=datetime.datetime.now(),
            last_updated_at=datetime.datetime.now(),
            candidates=Candidates.from_pandas(candidates, bench.domain),
        )


def test_invalid_number_of_candidates():
    bench = Himmelblau()
    candidates = bench.domain.inputs.sample(5)
    with pytest.raises(ValueError, match="Number of candidates"):
        Proposal(
            strategy_data=SoboStrategy(domain=bench.domain),
            n_candidates=1,
            experiments=None,
            pendings=None,
            state=StateEnum.CREATED,
            created_at=datetime.datetime.now(),
            last_updated_at=datetime.datetime.now(),
            candidates=Candidates.from_pandas(candidates, bench.domain),
        )
