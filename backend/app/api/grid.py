"""Grid monitoring endpoints"""
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..models import GridMetricsRequest, GridStatusResponse
from ..state import simulator

router = APIRouter()

class SimulationControlRequest(BaseModel):
    paused: bool | None = None
    speed_multiplier: float | None = Field(default=None, ge=0.5, le=4.0)


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


@router.post("/inject-failure")
async def inject_transformer_failure():
    """Force transformer outage simulation for extreme emergency demo."""
    simulator.inject_transformer_failure()
    return {"injected": True, "event": "transformer_failure", **simulator.get_status()}


@router.post("/clear-failure")
async def clear_transformer_failure():
    """Clear transformer outage mode and resume normal scenario transitions."""
    simulator.clear_transformer_failure()
    return {"cleared": True, **simulator.get_status()}


@router.get("/forecast")
async def forecast_grid_stress(hours_ahead: int = 24):
    """Lightweight real-time forecast using moving-average + trend."""
    return simulator.get_forecast(hours_ahead=hours_ahead)


@router.get("/history")
async def get_grid_history(limit: int = 120):
    """Return recent time-series points for dashboard analytics charts."""
    return {
        "points": simulator.get_history(limit=limit),
        "count": min(max(limit, 0), 360),
    }


@router.get("/external-signals")
async def get_external_signals():
    """Return latest real-time external telemetry used by simulator."""
    return simulator.get_external_signals()


@router.post("/simulation-control")
async def simulation_control(request: SimulationControlRequest):
    """Pause/resume simulation or change speed multiplier."""
    return simulator.set_simulation_state(
        paused=request.paused,
        speed_multiplier=request.speed_multiplier,
    )
