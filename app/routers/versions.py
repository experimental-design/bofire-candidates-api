import bofire
from fastapi import APIRouter


router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("", response_model=dict[str, str])
def get_versions() -> dict[str, str]:
    return {"bofire": bofire.__version__}
