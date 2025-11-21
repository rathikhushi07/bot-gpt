"""
Operations controller
Equivalent to OperationController.java
"""
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


@router.get("/ping")
async def ping():
    """Ping endpoint"""
    return {"message": "pong"}



