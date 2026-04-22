"""Vehicle-to-Grid endpoints"""
from fastapi import APIRouter

from ..models import V2GOfferRequest, V2GStatusResponse
from ..state import simulator

router = APIRouter()


@router.post("/register")
async def register_v2g_vehicle(request: V2GOfferRequest):
    """Register a V2G-capable vehicle for potential grid discharge."""
    success = simulator.v2g_manager.register_v2g_vehicle(
        vehicle_id=request.vehicle_id,
        soc_pct=request.soc_percent,
        departure_time=request.departure_time,
    )
    return {
        "vehicle_id": request.vehicle_id,
        "registered": success,
        "message": "V2G-capable vehicle registered" if success else "SoC too low for V2G",
    }


@router.post("/request-discharge")
async def request_v2g_discharge(vehicle_id: str, grid_deficit_kw: float = 50.0):
    """
    Request V2G discharge for a registered vehicle.
    Only honours the request when current GSI > 75.
    """
    gsi = simulator.level.gsi_score
    discharge_power = simulator.v2g_manager.request_v2g_discharge(
        vehicle_id=vehicle_id,
        gsi=gsi,
        grid_deficit_kw=grid_deficit_kw,
    )
    return {
        "vehicle_id": vehicle_id,
        "discharge_power_kw": discharge_power,
        "accepted": discharge_power is not None,
        "current_gsi": gsi,
        "message": (
            f"V2G discharge accepted at {discharge_power:.1f} kW"
            if discharge_power
            else "V2G request rejected (GSI too low or vehicle ineligible)"
        ),
    }


@router.get("/status", response_model=V2GStatusResponse)
async def get_v2g_status():
    """Return live V2G program metrics."""
    status = simulator.v2g_manager.get_status_report()
    return V2GStatusResponse(
        registered_vehicles=status["registered_vehicles"],
        active_discharges=status["active_discharges"],
        current_v2g_capacity_kw=status["current_v2g_capacity_kw"],
        total_compensation_paid=status["total_compensation_paid"],
    )
