from bofire.data_models.dataframes.api import Candidates
from fastapi import APIRouter

from bofire_candidates_api.data_models import CandidatesRequest
from bofire_candidates_api.generate import generate_candidates


router = APIRouter(prefix="/candidates", tags=["candidates"])


@router.post("/generate", response_model=Candidates)
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
