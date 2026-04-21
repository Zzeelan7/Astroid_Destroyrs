"""Health check endpoints"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """Service health status"""
    return {
        "status": "🟢 Healthy",
        "service": "GridCharge API",
        "version": "1.0.0"
    }
