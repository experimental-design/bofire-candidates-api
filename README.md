# BoFire Candidates API

[![Test](https://github.com/experimental-design/bofire-candidates-api/workflows/Tests/badge.svg)](https://github.com/experimental-design/bofire-candidates-api/actions?query=workflow%3ATests)
[![Lint](https://github.com/experimental-design/bofire-candidates-api/workflows/Lint/badge.svg)](https://github.com/experimental-design/bofire-candidates-api/actions?query=workflow%3ALint)


An **experimental** FastAPI based application that can be used to generate candidates via https using BoFire. It makes use of the pydantic `data_models` in BoFire, which allows for an easy fastAPI integration include full Swagger documentation which can be found when visiting `/docs` of the running web application.

Currently candidates are generated directly at request which can lead to http timeouts and other problems. Future versions should include an asynchronous worker based scenario for generating candidates.

## Usage

The following snippet shows how to use the candidates API via Pythons `request` module.

```python
import json
from typing import Optional

import requests
from bofire.benchmarks.api import Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import (
    AlwaysTrueCondition,
    AnyStrategy,
    NumberOfExperimentsCondition,
    RandomStrategy,
    SoboStrategy,
    Step,
    StepwiseStrategy,
)
from pydantic import BaseModel


class CandidateRequest(BaseModel):
    strategy_data: AnyStrategy
    n_candidates: int
    experiments: Optional[Experiments]
    pendings: Optional[Candidates]

# generate experimental data from the Himmelblau benchmark
bench = Himmelblau()
experiments = bench.f(bench.domain.inputs.sample(10), return_complete=True)

# setup the strategy for which candidates should be generated
strategy_data = StepwiseStrategy(
    domain=bench.domain,
    steps=[
        Step(
            condition=NumberOfExperimentsCondition(
                n_experiments=10
            ),
            strategy_data=RandomStrategy(domain=bench.domain)
        ),
        Step(
            condition=AlwaysTrueCondition(),
            strategy_data=SoboStrategy(domain=bench.domain)
        )
    ]
)

# create the payload
payload = CandidateRequest(
    strategy_data=strategy_data,
    n_candidates=1,
    experiments=Experiments.from_pandas(experiments, bench.domain),
    pendings=None
)


URL = "http://127.0.0.1:8000/candidates"
HEADERS = {'accept': 'application/json', 'Content-Type': 'application/json'}

# request candidates
response = requests.post(url=f"{URL}/generate", data=payload.model_dump_json(), headers=HEADERS)

# convert response to a pandas dataframe
df_candidates =Candidates(**json.loads(response.content)).to_pandas()

```


## Installation

Use the following command to set and run the API locally as well as run the unit tests.

### Setup

```bash
pip install -r requirements.txt
```


### Run
```bash
uvicorn --app-dir app:app --reload
```

### Run unit tests

```bash
pytest
```
