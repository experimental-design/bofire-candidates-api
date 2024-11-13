from typing import Optional

from bofire.data_models.base import BaseModel
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from pydantic import Field, model_validator


class CandidateRequest(BaseModel):
    strategy_data: AnyStrategy
    n_candidates: int = Field(
        default=1, gt=0, description="Number of candidates to generate"
    )
    experiments: Optional[Experiments]
    pendings: Optional[Candidates]

    @model_validator(mode="after")
    def validate_experiments(self):
        if self.experiments is not None:
            self.strategy_data.domain.validate_experiments(self.experiments.to_pandas())
        if self.pendings is not None:
            self.strategy_data.domain.validate_candidates(
                self.pendings.to_pandas(), only_inputs=True
            )
        return self
