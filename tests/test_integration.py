"""
Integration test: Full stack scenario
"""
import pytest
from datetime import datetime, timedelta
from app.core.gsi_engine import GSIEngine, GridMetrics
from app.core.slot_allocator import SlotAllocator, EVProfile, PriorityTier
from app.core.v2g_manager import V2GManager


@pytest.fixture
def system_components():
    """Initialize all system components"""
    return {
        "gsi_engine": GSIEngine(),
        "slot_allocator": SlotAllocator(station_capacity_kw=500, num_slots=10),
        "v2g_manager": V2GManager()
    }


def test_full_scenario_green_to_red(system_components):
    """
    Simulate full lifecycle:
    1. Green GSI: EV charges at full power
    2. Orange GSI: Power throttled
    3. Red GSI: V2G discharge activated
    """
    gsi_engine = system_components["gsi_engine"]
    slot_allocator = system_components["slot_allocator"]
    v2g_manager = system_components["v2g_manager"]
    
    # Phase 1: Green GSI
    green_metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=35,
        frequency_hz=50.0,
        transformer_temp_pct=40,
        renewable_penetration_pct=55
    )
    green_level = gsi_engine.compute_gsi(green_metrics)
    assert green_level.gsi_score <= 30
    assert green_level.max_power_kw == 150.0
    
    # EV1 arrives during green: gets 150 kW
    ev1 = EVProfile(
        vehicle_id="EV-1",
        soc_percent=20,
        target_soc_percent=80,
        departure_time=datetime.now() + timedelta(hours=2),
        user_priority=PriorityTier.P3_PREBOOKED_PUBLIC,
        is_v2g_capable=False
    )
    alloc1 = slot_allocator.allocate_slot(ev1, green_level.gsi_score, 55)
    assert alloc1.status == "assigned"
    assert alloc1.power_level_kw == 150.0
    
    # Phase 2: Orange GSI
    orange_metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=72,
        frequency_hz=49.9,
        transformer_temp_pct=78,
        renewable_penetration_pct=25
    )
    orange_level = gsi_engine.compute_gsi(orange_metrics)
    assert 55 < orange_level.gsi_score <= 75
    assert orange_level.max_power_kw == 50.0
    
    # EV2 arrives during orange: power throttled to 22 kW
    ev2 = EVProfile(
        vehicle_id="EV-2",
        soc_percent=15,
        target_soc_percent=80,
        departure_time=datetime.now() + timedelta(hours=1),
        user_priority=PriorityTier.P2_FLEET_COMMERCIAL,
        is_v2g_capable=False
    )
    alloc2 = slot_allocator.allocate_slot(ev2, orange_level.gsi_score, 25)
    # Might be queued if no capacity, but power would be throttled
    if alloc2.status == "assigned":
        assert alloc2.power_level_kw <= 22.0
    
    # Rebalance power during orange stress
    slot_allocator.rebalance_power(orange_level.gsi_score)
    # EV1 should see reduced power
    assert slot_allocator.active_sessions["EV-1"]["power_kw"] <= 22.0
    
    # Phase 3: Red GSI with V2G
    red_metrics = GridMetrics(
        timestamp=datetime.now(),
        load_percentage=92,
        frequency_hz=49.5,
        transformer_temp_pct=88,
        renewable_penetration_pct=8
    )
    red_level = gsi_engine.compute_gsi(red_metrics)
    assert red_level.gsi_score > 75
    assert red_level.v2g_enabled is True
    
    # V2G vehicle arrives during red
    v2g_ev = EVProfile(
        vehicle_id="EV-V2G-1",
        soc_percent=70,
        target_soc_percent=85,
        departure_time=datetime.now() + timedelta(hours=1.5),
        user_priority=PriorityTier.P4_WALK_IN_PUBLIC,
        is_v2g_capable=True
    )
    
    # Register for V2G
    v2g_registered = v2g_manager.register_v2g_vehicle("EV-V2G-1", 70, v2g_ev.departure_time)
    assert v2g_registered is True
    
    # During red GSI, should get V2G offer
    alloc_v2g = slot_allocator.allocate_slot(v2g_ev, red_level.gsi_score, 8)
    assert alloc_v2g.status == "v2g_offer"
    
    # Request V2G discharge
    discharge = v2g_manager.request_v2g_discharge("EV-V2G-1", red_level.gsi_score, 100)
    assert discharge is not None
    assert discharge > 0
    assert discharge <= v2g_manager.MAX_DISCHARGE_PER_VEHICLE
    
    # Check V2G status
    v2g_status = v2g_manager.get_status_report()
    assert v2g_status["registered_vehicles"] >= 1
    assert v2g_status["active_discharges"] >= 1
    assert v2g_status["current_v2g_capacity_kw"] > 0


def test_priority_ordering_under_stress(system_components):
    """Verify priority tier ordering under grid stress"""
    slot_allocator = system_components["slot_allocator"]
    
    # Create EVs of different priorities
    p0_ev = EVProfile(
        vehicle_id="EV-P0",
        soc_percent=5,
        target_soc_percent=80,
        departure_time=datetime.now() + timedelta(hours=1),
        user_priority=PriorityTier.P0_EMERGENCY,
        is_v2g_capable=False
    )
    
    p5_ev = EVProfile(
        vehicle_id="EV-P5",
        soc_percent=75,
        target_soc_percent=85,
        departure_time=datetime.now() + timedelta(hours=1),
        user_priority=PriorityTier.P5_OPPORTUNISTIC,
        is_v2g_capable=False
    )
    
    # Both request during critical stress (GSI 80)
    alloc_p0 = slot_allocator.allocate_slot(p0_ev, gsi=80, available_renewable_pct=5)
    alloc_p5 = slot_allocator.allocate_slot(p5_ev, gsi=80, available_renewable_pct=5)
    
    # P0 should be assigned or queued with priority
    # P5 should be queued or deferred
    assert alloc_p0.status in ["assigned", "queued"]
    assert alloc_p5.status == "queued"
