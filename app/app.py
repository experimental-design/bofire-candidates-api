from fastapi import FastAPI
from routers.candidates import router as candidates_router
from routers.proposals import router as proposals_router
from routers.versions import router as versions_router
from starlette.responses import RedirectResponse


app = FastAPI(title="BoFire Candidates API", version="0.1.0", root_path="/")


@app.get("/", include_in_schema=False)
async def redirect():
    return RedirectResponse(url="/docs")


app.include_router(candidates_router)
app.include_router(versions_router)
app.include_router(proposals_router)
