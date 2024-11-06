import bofire.strategies.api as strategies
from bofire.data_models.dataframes.api import Candidates
from fastapi import APIRouter, HTTPException
from models.candidates import CandidateRequest


router = APIRouter(prefix="", tags=["candidates"])


@router.post("/candidates/generate", response_model=Candidates)
def generate(
    candidate_request: CandidateRequest,
) -> Candidates:
    strategy = strategies.map(candidate_request.strategy_data)
    if candidate_request.experiments is not None:
        strategy.tell(candidate_request.experiments.to_pandas())
    try:
        df_candidates = strategy.ask(candidate_request.n_candidates)
    except ValueError as e:
        if str(e) == "Not enough experiments available to execute the strategy.":
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(
                status_code=500, detail=f"A server error occurred. Details: {e}"
            )
    return Candidates.from_pandas(df_candidates, candidate_request.strategy_data.domain)
