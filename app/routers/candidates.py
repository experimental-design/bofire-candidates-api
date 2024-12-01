import bofire.strategies.api as strategies
from bofire.data_models.candidates_api.api import CandidateRequest
from bofire.data_models.dataframes.api import Candidates
from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="", tags=["candidates"])


def handle_ask_exceptions(e: Exception) -> None:
    """Handle exceptions raised by the strategy ask method.

    Args:
        e (Exception): Exception to handle.

    Raises:
        HTTPException: Status code 404 if not enough experiments are available to execute the strategy.
        HTTPException: Status code 500 if other server error occurs.
    """
    if str(e) == "Not enough experiments available to execute the strategy.":
        raise HTTPException(status_code=404, detail=str(e))
    else:
        raise HTTPException(
            status_code=500, detail=f"A server error occurred. Details: {e}"
        )


@router.post("/candidates/generate", response_model=Candidates)
def generate(
    candidate_request: CandidateRequest,
) -> Candidates:
    """Generate candidates using the specified strategy.

    Args:
        candidate_request (CandidateRequest): Request model for generating candidates.

    Returns:
        Candidates: The generated candidates.
    """
    strategy = strategies.map(candidate_request.strategy_data)

    if candidate_request.experiments is not None:
        strategy.tell(candidate_request.experiments.to_pandas())

    try:
        df_candidates = strategy.ask(candidate_request.n_candidates)
    except ValueError as e:
        handle_ask_exceptions(e)
        pass

    return Candidates.from_pandas(df_candidates, candidate_request.strategy_data.domain)
