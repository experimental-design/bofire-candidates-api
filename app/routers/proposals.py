import datetime
from typing import Annotated, List, Optional, Tuple

from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from fastapi import APIRouter, Depends, HTTPException
from tinydb import Query, TinyDB

from app.models.proposals import Proposal, ProposalRequest, StateEnum


DBPATH = "db.json"

db = None


async def get_db():
    """Get the database connection.

    Yields:
        TinyDB: The database connection.
    """
    # todo: handle chaching
    db = TinyDB(DBPATH, default=str)
    try:
        yield db
    finally:
        db.close()


router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.post("", response_model=Proposal)
def create_proposal(
    proposal_request: ProposalRequest,
    db: Annotated[str, Depends(get_db)],  # type: ignore
) -> Proposal:
    """Creates a proposal for candidates.

    Args:
        proposal_request (ProposalRequest): The original request for the proposal.
        db (Annotated[str, Depends): The database to store the proposal.

    Returns:
        Proposal: The created proposal.
    """
    proposal_request_data = proposal_request.model_dump()
    proposal = Proposal(**proposal_request_data)

    id = db.insert(proposal.model_dump())
    proposal.id = id
    return proposal


@router.get(
    "/claim",
    response_model=Tuple[
        int, AnyStrategy, int, Optional[Experiments], Optional[Candidates]
    ],
)
def claim_proposal(  # works
    db: Annotated[str, Depends(get_db)],  # type: ignore
) -> Tuple[int, AnyStrategy, int, Optional[Experiments], Optional[Candidates]]:
    dict_proposal = db.search(Query().state == StateEnum.CREATED)
    if len(dict_proposal) == 0:
        raise HTTPException(status_code=404, detail="No proposals to claim")
    proposal = Proposal(**dict_proposal[0])
    db.update(
        {"state": StateEnum.CLAIMED, "last_updated_at": datetime.datetime.now()},
        doc_ids=[dict_proposal[0].doc_id],
    )
    # TODO: id is wrong
    return (
        dict_proposal[0].doc_id,
        proposal.strategy_data,
        proposal.n_candidates,
        proposal.experiments,
        proposal.pendings,
    )


@router.get("/{proposal_id}", response_model=Proposal)
def get_proposal(proposal_id: int, db: Annotated[str, Depends(get_db)]) -> Proposal:  # type: ignore
    dict_proposal = db.get(doc_id=proposal_id)
    if dict_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = Proposal(**dict_proposal)
    proposal.id = dict_proposal.doc_id
    return proposal


@router.get("/{proposal_id}/candidates", response_model=Candidates)
def get_candidates(proposal_id: int, db: Annotated[str, Depends(get_db)]) -> Candidates:  # type: ignore
    dict_proposal = db.get(doc_id=proposal_id)
    if dict_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = Proposal(**dict_proposal)
    if proposal.candidates is None:
        raise HTTPException(status_code=404, detail="Candidates not found")
    return proposal.candidates


@router.post("/{proposal_id}/mark_processed", response_model=StateEnum)
def mark_processed(
    proposal_id: int,
    candidates: Candidates,
    db: Annotated[str, Depends(get_db)],  # type: ignore
) -> StateEnum:
    dict_proposal = db.get(doc_id=proposal_id)
    if dict_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = Proposal(**dict_proposal)
    if len(candidates.rows) != proposal.n_candidates:
        raise HTTPException(
            status_code=404,
            detail=f"Expected {proposal.n_candidates} candidates, got {len(candidates.rows)}",
        )
    proposal.candidates = candidates
    proposal.last_updated_at = datetime.datetime.now()
    proposal.state = StateEnum.FINISHED
    db.update(proposal.model_dump(), doc_ids=[proposal_id])
    return proposal.state


@router.post("/{proposal_id}/mark_failed", response_model=StateEnum)
def mark_failed(
    proposal_id: int,
    error_message: dict[str, str],
    db: Annotated[str, Depends(get_db)],  # type: ignore
) -> StateEnum:
    dict_proposal = db.get(doc_id=proposal_id)
    if dict_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = Proposal(**dict_proposal)
    proposal.last_updated_at = datetime.datetime.now()
    proposal.state = StateEnum.FAILED
    proposal.error_message = error_message["msg"]
    db.update(proposal.model_dump(), doc_ids=[proposal_id])
    return proposal.state


@router.get("/{proposal_id}/state", response_model=StateEnum)  # works
def get_state(proposal_id: int, db: Annotated[str, Depends(get_db)]) -> StateEnum:  # type: ignore
    dict_proposal = db.get(doc_id=proposal_id)
    if dict_proposal is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal = Proposal(**dict_proposal)
    return proposal.state


@router.get("", response_model=List[Proposal])
def get_proposals(db: Annotated[str, Depends(get_db)]) -> List[Proposal]:  # type: ignore
    return [Proposal(**{**d, **{"id": d.doc_id}}) for d in db.all()]
