from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


@router.get("/ping")
async def ping():
    return {"message": "pong"}



