from typing import Optional

import bofire.strategies.api as strategies
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from fastapi import APIRouter, HTTPException

from routers.api_data_models import CandidatesRequest


router = APIRouter(prefix="", tags=["candidates"])


def generate_candidates(
    strategy_data: AnyStrategy,
    n_candidates: int,
    experiments: Optional[Experiments],
    pendings: Optional[Candidates],
    i_start: int = 0,
    n_restarts: int = 1,
) -> Candidates:
    """Generate candidates using the specified strategy.

    Args:
        strategy_data (AnyStrategy): BoFire strategy data.
        n_candidates (int): Number of candidates to generate.
        experiments (Optional[Experiments]): Experiments to provide to the strategy.
        pendings (Optional[Candidates]): Candidates that are pending to be executed.
        n_restarts_on_failure (int): Number of restarts for the strategy on failure.

    Returns:
        Candidates: The generated candidates.
    """
    strategy = strategies.map(strategy_data)

    if experiments is not None:
        strategy.tell(experiments.to_pandas())

    try:
        df_candidates = strategy.ask(n_candidates)
    except Exception as e:
        if str(e) == "Not enough experiments available to execute the strategy.":
            raise HTTPException(status_code=404, detail=str(e))
        if i_start < n_restarts:
            return generate_candidates(
                strategy_data=strategy_data,
                n_candidates=n_candidates,
                experiments=experiments,
                pendings=pendings,
                i_start=i_start + 1,
                n_restarts=n_restarts,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred. Details: {e}",
            )
    return Candidates.from_pandas(df_candidates, strategy_data.domain)


@router.post("/candidates/generate", response_model=Candidates)
def generate(
    candidate_request: CandidatesRequest,
) -> Candidates:
    """Generate candidates using the specified strategy.

    Args:
        candidate_request (CandidatesRequest): Request model for generating candidates.

    Returns:
        Candidates: The generated candidates.
    """
    return generate_candidates(
        strategy_data=candidate_request.strategy_data,
        n_candidates=candidate_request.n_candidates,
        experiments=candidate_request.experiments,
        pendings=candidate_request.pendings,
        n_restarts=candidate_request.n_restarts,
        i_start=0,
    )
