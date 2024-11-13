import datetime
from enum import Enum
from typing import Optional

from bofire.data_models.base import BaseModel
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from pydantic import Field, model_validator


class ProposalRequest(BaseModel):
    strategy_data: AnyStrategy
    n_candidates: int = Field(
        default=1, gt=0, description="Number of candidates to generate"
    )
    experiments: Optional[Experiments] = None
    pendings: Optional[Candidates] = None

    @model_validator(mode="after")
    def validate_experiments(self):
        if self.experiments is not None:
            self.strategy_data.domain.validate_experiments(self.experiments.to_pandas())
        if self.pendings is not None:
            raise ValueError("Pendings must be None for proposals.")
            self.strategy_data.domain.validate_candidates(
                self.pendings.to_pandas(), only_inputs=True
            )
        return self


class StateEnum(str, Enum):
    CREATED = "CREATED"
    CLAIMED = "CLAIMED"
    FAILED = "FAILED"
    FINISHED = "FINISHED"


class Proposal(ProposalRequest):
    id: Optional[int] = None
    candidates: Optional[Candidates] = None
    created_at: datetime.datetime
    last_updated_at: datetime.datetime
    state: StateEnum
    error_message: Optional[str] = None

    @model_validator(mode="after")
    def validate_candidates(self):
        if self.candidates is not None:
            self.strategy_data.domain.validate_candidates(
                self.candidates.to_pandas(), only_inputs=True
            )
        if len(self.candidates.rows) != self.n_candidates:
            raise ValueError(
                f"Number of candidates ({len(self.candidates)}) does not match n_candidates ({self.n_candidates})."
            )
        return self
