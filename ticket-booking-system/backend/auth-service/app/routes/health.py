# Importing APIRouter class from fastapi
from fastapi import APIRouter, HTTPException
from app.utils.config import settings

router = APIRouter()


# decorator tells FastAPI when someone makes the request call the function immediately below it.


@router.get("/test-error")
async def test_error():
    if not settings.debug:
        raise HTTPException(status_code=404, detail="Not Found")

    raise RuntimeError("Temporary test exception")


# @router.get("/health")
# def health():
#     return {
#         "status": "UP",
#         "service" : "Auth-Service",
#         "database" : "Connected"
#     }
