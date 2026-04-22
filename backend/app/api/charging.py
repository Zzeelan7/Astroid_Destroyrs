"""Charging slot allocation endpoints"""
from datetime import datetime

from fastapi import APIRouter

from ..core.slot_allocator import EVProfile, PriorityTier
from ..models import ChargingRequestRequest, SlotAllocationResponse
from ..state import simulator

router = APIRouter()


@router.post("/request-slot", response_model=SlotAllocationResponse)
async def request_charging_slot(request: ChargingRequestRequest):
    """
    Request a charging slot for an EV.
    Uses the live GSI from the background simulator for throttling decisions.
    """
    ev = EVProfile(
        vehicle_id=request.vehicle_id,
        soc_percent=request.soc_percent,
        target_soc_percent=request.target_soc_percent,
        departure_time=request.departure_time,
        user_priority=PriorityTier(request.user_priority),
        is_v2g_capable=request.is_v2g_capable,
    )

    allocation = simulator.slot_allocator.allocate_slot(
        ev=ev,
        current_gsi=simulator.level.gsi_score,
        available_renewable_pct=simulator.metrics.renewable_penetration_pct,
    )

    return SlotAllocationResponse(
        vehicle_id=allocation.vehicle_id,
        slot_id=allocation.slot_id,
        status=allocation.status,
        power_level_kw=allocation.power_level_kw,
        estimated_wait_minutes=allocation.estimated_wait_minutes,
        estimated_charge_time_minutes=allocation.estimated_charge_time_minutes,
        reason=allocation.reason,
    )


@router.get("/active-sessions")
async def get_active_sessions():
    """Get all active charging sessions from the shared allocator."""
    return {
        "total_active": len(simulator.slot_allocator.active_sessions),
        "queued": len(simulator.slot_allocator.queue),
        "sessions": [
            {
                "vehicle_id": vid,
                "power_kw": session.get("power_kw", 0),
                "time_active_minutes": int(
                    (datetime.now() - session.get("start_time", datetime.now())).total_seconds() / 60
                ),
                "is_v2g": (session.get("ev", None) and session["ev"].is_v2g_capable) or False,
            }
            for vid, session in simulator.slot_allocator.active_sessions.items()
        ],
    }


@router.post("/rebalance")
async def trigger_rebalance():
    """Manually trigger power rebalancing at the current GSI."""
    gsi = simulator.level.gsi_score
    simulator.slot_allocator.rebalance_power(gsi)
    return {
        "status": "rebalanced",
        "gsi": gsi,
        "active_sessions": len(simulator.slot_allocator.active_sessions),
    }
