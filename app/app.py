import os
import sys

# This is a workaround to ensure that the module can be imported correctly
# Add the directory containing your module to sys.path
sys.path.append(os.path.abspath(os.path.dirname(os.path.realpath(__file__))))

import bofire
from fastapi import FastAPI
from routers.candidates import router as candidates_router
from routers.proposals import router as proposals_router
from starlette.responses import RedirectResponse


APP_VERSION = "0.0.1"

app = FastAPI(title="BoFire Candidates API", version=APP_VERSION, root_path="/")


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse(url="/docs")


app.include_router(candidates_router)
app.include_router(proposals_router)


@app.get("/versions", response_model=dict[str, str])
def get_versions() -> dict[str, str]:
    return {"bofire_candidates_api": APP_VERSION, "bofire": bofire.__version__}
