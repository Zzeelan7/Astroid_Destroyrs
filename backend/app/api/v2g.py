"""Vehicle-to-Grid endpoints"""
from fastapi import APIRouter
from app.core.v2g_manager import V2GManager
from app.models import V2GOfferRequest, V2GStatusResponse
from datetime import datetime

router = APIRouter()
v2g_manager = V2GManager()


@router.post("/register")
async def register_v2g_vehicle(request: V2GOfferRequest):
    """Register a V2G-capable vehicle"""
    success = v2g_manager.register_v2g_vehicle(
        vehicle_id=request.vehicle_id,
        soc_pct=request.soc_percent,
        departure_time=request.departure_time
    )
    
    return {
        "vehicle_id": request.vehicle_id,
        "registered": success,
        "message": "V2G-capable vehicle registered" if success else "SoC too low for V2G"
    }


@router.post("/request-discharge")
async def request_v2g_discharge(vehicle_id: str, gsi: float, grid_deficit_kw: float):
    """Request V2G discharge during grid stress"""
    discharge_power = v2g_manager.request_v2g_discharge(
        vehicle_id=vehicle_id,
        gsi=gsi,
        grid_deficit_kw=grid_deficit_kw
    )
    
    return {
        "vehicle_id": vehicle_id,
        "discharge_power_kw": discharge_power,
        "accepted": discharge_power is not None,
        "message": f"V2G discharge requested at {discharge_power} kW" if discharge_power else "V2G request rejected"
    }


@router.get("/status", response_model=V2GStatusResponse)
async def get_v2g_status():
    """Get V2G program status"""
    status = v2g_manager.get_status_report()
    
    return V2GStatusResponse(
        registered_vehicles=status["registered_vehicles"],
        active_discharges=status["active_discharges"],
        current_v2g_capacity_kw=status["current_v2g_capacity_kw"],
        total_compensation_paid=status["total_compensation_paid"]
    )
