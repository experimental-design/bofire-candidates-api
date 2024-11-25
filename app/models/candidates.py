from typing import Optional

from bofire.data_models.base import BaseModel
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import AnyStrategy
from pydantic import Field, model_validator


class CandidateRequest(BaseModel):
    """Request model for generating candidates."""
    strategy_data: AnyStrategy = Field(
        description="BoFire strategy data"
    )
    n_candidates: int = Field(
        default=1, gt=0, description="Number of candidates to generate"
    )
    experiments: Optional[Experiments] = Field(
        default=None, description="Experiments to provide to the strategy"
    )
    pendings: Optional[Candidates] = Field(
        default=None, description="Candidates that are pending to be executed"
    )

    @model_validator(mode="after")
    def validate_experiments(self):
        """Validate experiments and pendings against the strategy domain.

        Returns:
            CandidateRequest: The validated request
        """
        if self.experiments is not None:
            self.strategy_data.domain.validate_experiments(
                self.experiments.to_pandas()
            )
        if self.pendings is not None:
            self.strategy_data.domain.validate_candidates(
                self.pendings.to_pandas(), only_inputs=True
            )
        return self
