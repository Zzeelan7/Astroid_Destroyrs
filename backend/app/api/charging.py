"""Charging slot allocation endpoints"""
from fastapi import APIRouter
from app.core.slot_allocator import SlotAllocator, EVProfile, PriorityTier
from app.models import ChargingRequestRequest, SlotAllocationResponse
from datetime import datetime

router = APIRouter()
slot_allocator = SlotAllocator()

# Mock current GSI (in production, read from Redis/DB)
mock_current_gsi = 35.0


@router.post("/request-slot", response_model=SlotAllocationResponse)
async def request_charging_slot(request: ChargingRequestRequest):
    """
    Request a charging slot for an EV.
    
    Returns slot allocation with power level and wait time.
    """
    ev = EVProfile(
        vehicle_id=request.vehicle_id,
        soc_percent=request.soc_percent,
        target_soc_percent=request.target_soc_percent,
        departure_time=request.departure_time,
        user_priority=PriorityTier(request.user_priority),
        is_v2g_capable=request.is_v2g_capable
    )
    
    allocation = slot_allocator.allocate_slot(
        ev=ev,
        current_gsi=mock_current_gsi,
        available_renewable_pct=45.0
    )
    
    return SlotAllocationResponse(
        vehicle_id=allocation.vehicle_id,
        slot_id=allocation.slot_id,
        status=allocation.status,
        power_level_kw=allocation.power_level_kw,
        estimated_wait_minutes=allocation.estimated_wait_minutes,
        estimated_charge_time_minutes=allocation.estimated_charge_time_minutes,
        reason=allocation.reason
    )


@router.get("/active-sessions")
async def get_active_sessions():
    """Get list of active charging sessions"""
    return {
        "total_active": len(slot_allocator.active_sessions),
        "queued": len(slot_allocator.queue),
        "sessions": [
            {
                "vehicle_id": vid,
                "power_kw": session.get("power_kw", 0),
                "time_active_minutes": int(
                    (datetime.now() - session.get("start_time", datetime.now())).total_seconds() / 60
                )
            }
            for vid, session in slot_allocator.active_sessions.items()
        ]
    }


@router.post("/rebalance")
async def trigger_rebalance(gsi: float = 50.0):
    """Manually trigger power rebalancing"""
    slot_allocator.rebalance_power(gsi)
    return {
        "status": "rebalance_triggered",
        "gsi": gsi,
        "active_sessions": len(slot_allocator.active_sessions)
    }
