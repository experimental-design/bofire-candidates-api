# BoFire Candidates API

[![Test](https://github.com/experimental-design/bofire-candidates-api/workflows/Tests/badge.svg)](https://github.com/experimental-design/bofire-candidates-api/actions?query=workflow%3ATests)
[![Lint](https://github.com/experimental-design/bofire-candidates-api/workflows/Lint/badge.svg)](https://github.com/experimental-design/bofire-candidates-api/actions?query=workflow%3ALint)


An **experimental** FastAPI based application that can be used to generate candidates via http(s) using BoFire. It makes use of pydantic `data_models` in BoFire, which allows for an easy fastAPI integration including Swagger based documentation which can be found when visiting `/docs` of the running web application.

Candidates can be generated via two different ways, either directly at request which can lead to http timeouts or using an asynchronous worker based procedure.

## Usage

### Installation

To install the full functionality of the package, clone the package and run locally.

```
pip install bofire_candidates_api[optimization]
```

### Run
```bash
uvicorn --app-dir=app app:app --reload
```

If you also want to use the asynchronous worker based candidate generation, use the following snippet to start at least one worker:

```bash
python worker
```

### Direct Candidate Generation

In the following it is shown how to generate candidates in the direct way using a post request.

Before running this snippet, make sure to have started the app.

```python
import json

import requests
from bofire.benchmarks.api import Himmelblau
from bofire.data_models.dataframes.api import Candidates, Experiments
from bofire.data_models.strategies.api import (
    AlwaysTrueCondition,
    NumberOfExperimentsCondition,
    RandomStrategy,
    SoboStrategy,
    Step,
    StepwiseStrategy,
)

from bofire_candidates_api.data_models import CandidatesRequest


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
payload = CandidatesRequest(
    strategy_data=strategy_data,
    n_candidates=1,
    experiments=Experiments.from_pandas(experiments, bench.domain),
    pendings=None
)


URL = "http://127.0.0.1:8000"
HEADERS = {'accept': 'application/json', 'Content-Type': 'application/json'}

# request candidates
response = requests.post(url=f"{URL}/candidates/generate", data=payload.model_dump_json(), headers=HEADERS)

# convert response to a pandas dataframe
df_candidates = Candidates(**json.loads(response.content)).to_pandas()
```

### Worker Based Candidate Generation

The following snippet shows how to use the worker based candidate generation using the same payload as above. The API is storing all necessary information regarding the proposals in a [`TinyDB`](https://tinydb.readthedocs.io/en/latest/) database. **Note that concurrent worker access using multiple users has not been tested yet.**

Before running this snippet, make sure to have started a worker.

``` python
import time

# create the proposal in the database
response = requests.post(url=f"{URL}/proposals", json=payload.model_dump(), headers=HEADERS)
id = json.loads(response.content)["id"]

# poll the state of the proposal
def get_state(id:int):
    return requests.get(url=f"{URL}/proposals/{id}/state", headers=HEADERS).json()

state = get_state(id)

while state in ["CREATED", "CLAIMED"]:
    state = get_state(id)
    time.sleep(5)

# get the candidates when the worker is finished
if state=="FINISHED":
    response = requests.get(url=f"{URL}/proposals/{id}/candidates", headers=HEADERS)
    candidates = Candidates(**response.json()).to_pandas()
else:
    print(state) # candidate generation was not successful.
```
