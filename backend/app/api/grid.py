"""Grid monitoring endpoints"""
from fastapi import APIRouter

from ..models import GridMetricsRequest, GridStatusResponse
from ..state import simulator

router = APIRouter()


@router.get("/status", response_model=GridStatusResponse)
async def get_current_grid_status():
    """
    Return the *current* live grid state driven by the background simulator.
    The frontend polls this — no input required.
    """
    return simulator.get_status()


@router.post("/status", response_model=GridStatusResponse)
async def set_grid_status(request: GridMetricsRequest):
    """
    Manually override grid metrics (used by demo script / Swagger testing).
    Updates the simulator state immediately.
    """
    from ..core.gsi_engine import GridMetrics
    from datetime import datetime

    simulator.metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=request.load_percentage,
        frequency_hz=request.frequency_hz,
        transformer_temp_pct=request.transformer_temp_pct,
        renewable_penetration_pct=request.renewable_penetration_pct,
    )
    simulator.level = simulator.gsi_engine.compute_gsi(simulator.metrics)
    simulator.slot_allocator.rebalance_power(simulator.level.gsi_score)
    return simulator.get_status()


@router.post("/inject-stress")
async def inject_stress_event():
    """
    Immediately push the simulator into peak-stress scenario.
    Used by the dashboard 'Inject Stress Event' button.
    """
    simulator.inject_stress()
    return {"injected": True, **simulator.get_status()}


@router.get("/forecast")
async def forecast_grid_stress(hours_ahead: int = 24):
    """Placeholder for LSTM-based GSI prediction."""
    return {
        "forecast_hours": hours_ahead,
        "status": "prediction_not_yet_available",
        "message": "LSTM model integration pending",
    }
