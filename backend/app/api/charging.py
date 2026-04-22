"""Charging slot allocation endpoints"""
from datetime import datetime

from fastapi import APIRouter

from ..core.slot_allocator import EVProfile, PriorityTier
from ..models import (
    ChargingRequestRequest,
    SimulationRequest,
    SimulationResponse,
    SlotAllocationResponse,
)
from ..state import simulator

router = APIRouter()


def _predict_optimal_start_window() -> datetime:
    """Pick timestamp with lowest simple moving-average GSI from recent history."""
    points = simulator.get_history(limit=90)
    if not points:
        return datetime.now()

    window = 5
    best_index = 0
    best_avg = float("inf")

    for index in range(len(points)):
        start = max(0, index - window + 1)
        slice_scores = [float(p["gsi_score"]) for p in points[start : index + 1]]
        avg_score = sum(slice_scores) / len(slice_scores)
        if avg_score < best_avg:
            best_avg = avg_score
            best_index = index

    ts = points[best_index].get("timestamp")
    if not ts:
        return datetime.now()
    return datetime.fromisoformat(ts)


def _recommendation_for_gsi(gsi: float) -> str:
    if gsi <= 30:
        return "Charge now - green window"
    if gsi <= 55:
        return "Charge now - stable grid conditions"
    if gsi <= 75:
        return "Defer 20 min - grid stressed"
    return "Avoid charging now - consider V2G support"


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


@router.post("/simulate", response_model=SimulationResponse)
async def simulate_charging_slot(request: SimulationRequest):
    """
    Simulate manual EV request with richer prediction fields.
    Uses the same live slot allocator path as the request-slot API.
    """
    ev = EVProfile(
        vehicle_id=request.vehicle_id,
        soc_percent=request.soc_percent,
        target_soc_percent=request.target_soc_percent,
        departure_time=request.departure_time,
        user_priority=PriorityTier(request.user_priority),
        is_v2g_capable=request.is_v2g_capable,
    )

    gsi_at_request = simulator.level.gsi_score
    renewable_pct = simulator.metrics.renewable_penetration_pct

    allocation = simulator.slot_allocator.allocate_slot(
        ev=ev,
        current_gsi=gsi_at_request,
        available_renewable_pct=renewable_pct,
    )

    energy_kwh = max(0.0, (request.target_soc_percent - request.soc_percent) / 100.0 * 50.0)
    estimated_cost_inr = energy_kwh * 8.0
    carbon_offset_kg = (renewable_pct / 100.0) * energy_kwh * 0.7

    return SimulationResponse(
        vehicle_id=allocation.vehicle_id,
        slot_id=allocation.slot_id,
        status=allocation.status,
        power_level_kw=allocation.power_level_kw,
        estimated_wait_minutes=allocation.estimated_wait_minutes,
        estimated_charge_time_minutes=allocation.estimated_charge_time_minutes,
        reason=allocation.reason,
        allocated_power_kw=allocation.power_level_kw,
        estimated_cost_inr=round(estimated_cost_inr, 2),
        carbon_offset_kg=round(carbon_offset_kg, 3),
        gsi_at_request=round(gsi_at_request, 2),
        recommendation=_recommendation_for_gsi(gsi_at_request),
        optimal_start_window=_predict_optimal_start_window(),
        slot_status=allocation.status,
        location=request.location,
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

@router.post("/slots/escalate")
async def escalate_to_p0(payload: dict):
    """Escalate a specific vehicle to P0 Emergency priority"""
    vehicle_id = payload.get("vehicle_id")
    if not vehicle_id:
        return {"error": "vehicle_id required"}
        
    # Check active sessions
    for vid, sess in simulator.slot_allocator.active_sessions.items():
        if vid == vehicle_id:
            if "ev" in sess:
                sess["ev"].user_priority = PriorityTier.P0
            # Force immediate rebalance
            simulator.slot_allocator.rebalance_power(simulator.level.gsi_score)
            return {"status": "escalated", "vehicle_id": vehicle_id, "priority": 0}
            
    # Check queue
    for i, q_item in enumerate(simulator.slot_allocator.queue):
        if q_item[2].vehicle_id == vehicle_id:
            q_item[2].user_priority = PriorityTier.P0
            # Re-heapify queue
            import heapq
            new_q = []
            for item in simulator.slot_allocator.queue:
                priority = item[2].user_priority.value
                heapq.heappush(new_q, (priority, item[1], item[2]))
            simulator.slot_allocator.queue = new_q
            simulator.slot_allocator.process_queue(simulator.level.gsi_score)
            return {"status": "escalated_in_queue", "vehicle_id": vehicle_id, "priority": 0}
            
    return {"error": "Vehicle not found in active sessions or queue"}
