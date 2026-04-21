"""Grid monitoring endpoints"""
from fastapi import APIRouter
from app.core.gsi_engine import GSIEngine, GridMetrics
from app.models import GridMetricsRequest, GridStatusResponse
from datetime import datetime

router = APIRouter()
gsi_engine = GSIEngine()


@router.post("/status", response_model=GridStatusResponse)
async def get_grid_status(request: GridMetricsRequest):
    """
    Get current grid stress status (GSI)
    
    Returns Grid Stress Index (0-100) with policy tier
    """
    metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=request.load_percentage,
        frequency_hz=request.frequency_hz,
        transformer_temp_pct=request.transformer_temp_pct,
        renewable_penetration_pct=request.renewable_penetration_pct
    )
    
    level = gsi_engine.compute_gsi(metrics)
    
    return GridStatusResponse(
        gsi_score=level.gsi_score,
        status=level.status,
        charging_policy=level.charging_policy,
        max_power_kw=level.max_power_kw,
        allow_new_connections=level.allow_new_connections,
        v2g_enabled=level.v2g_enabled
    )


@router.get("/forecast")
async def forecast_grid_stress(hours_ahead: int = 24):
    """
    Predict grid stress for next N hours
    (Placeholder for LSTM model integration)
    """
    return {
        "forecast_hours": hours_ahead,
        "status": "prediction_not_yet_available",
        "message": "LSTM model integration pending"
    }
