from typing import Optional

import bofire.strategies.api as strategies
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from fastapi import APIRouter, HTTPException

from bofire_candidates_api.api_data_models import CandidatesRequest


router = APIRouter(prefix="", tags=["candidates"])


def generate_candidates(
    candidate_request: CandidatesRequest,
    i_start: int = 0,
) -> Candidates:
    """Generate candidates using the specified strategy.

    Args:
        candidate_request (CandidatesRequest): Request model for generating candidates.
        i_start (int, optional): The current restart index. Defaults to 0.

    Returns:
        Candidates: The generated candidates.
    """
    strategy = strategies.map(candidate_request.strategy_data)

    if candidate_request.experiments is not None:
        strategy.tell(candidate_request.experiments.to_pandas())

    try:
        df_candidates = strategy.ask(candidate_request.n_candidates)
    except Exception as e:
        if str(e) == "Not enough experiments available to execute the strategy.":
            raise HTTPException(status_code=404, detail=str(e))
        if i_start < candidate_request.n_restarts:
            return generate_candidates(
                candidate_request=candidate_request,
                i_start=i_start + 1,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"An error occurred. Details: {e}",
            )
    return Candidates.from_pandas(df_candidates, candidate_request.strategy_data.domain)


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
        candidate_request=candidate_request,
        i_start=0,
    )
