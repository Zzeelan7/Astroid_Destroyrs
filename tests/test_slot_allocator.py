"""Unit tests for Slot Allocator"""
import pytest
from datetime import datetime, timedelta
from app.core.slot_allocator import SlotAllocator, EVProfile, PriorityTier


@pytest.fixture
def allocator():
    return SlotAllocator(station_capacity_kw=500, num_slots=10)


def test_allocate_slot_green_gsi(allocator):
    """Test slot allocation under normal conditions"""
    ev = EVProfile(
        vehicle_id="EV-001",
        soc_percent=30,
        target_soc_percent=80,
        departure_time=datetime.now() + timedelta(hours=2),
        user_priority=PriorityTier.P3_PREBOOKED_PUBLIC,
        is_v2g_capable=False
    )
    
    result = allocator.allocate_slot(ev, current_gsi=25, available_renewable_pct=40)
    
    assert result.status == "assigned"
    assert result.power_level_kw > 0
    assert result.estimated_wait_minutes == 0


def test_allocate_slot_critical_gsi_not_priority(allocator):
    """Test that non-priority vehicles are queued during critical GSI"""
    ev = EVProfile(
        vehicle_id="EV-002",
        soc_percent=50,
        target_soc_percent=90,
        departure_time=datetime.now() + timedelta(hours=1),
        user_priority=PriorityTier.P4_WALK_IN_PUBLIC,
        is_v2g_capable=False
    )
    
    result = allocator.allocate_slot(ev, current_gsi=85, available_renewable_pct=10)
    
    assert result.status == "queued"
    assert result.power_level_kw == 0


def test_allocate_slot_critical_gsi_v2g_capable(allocator):
    """Test V2G offer during critical GSI for capable vehicles"""
    ev = EVProfile(
        vehicle_id="EV-003",
        soc_percent=75,
        target_soc_percent=90,
        departure_time=datetime.now() + timedelta(hours=1),
        user_priority=PriorityTier.P4_WALK_IN_PUBLIC,
        is_v2g_capable=True
    )
    
    result = allocator.allocate_slot(ev, current_gsi=85, available_renewable_pct=10)
    
    assert result.status == "v2g_offer"


def test_power_throttling_by_gsi(allocator):
    """Test adaptive power throttling as GSI increases"""
    ev = EVProfile(
        vehicle_id="EV-004",
        soc_percent=20,
        target_soc_percent=80,
        departure_time=datetime.now() + timedelta(hours=2),
        user_priority=PriorityTier.P2_FLEET_COMMERCIAL,
        is_v2g_capable=False
    )
    
    # Green GSI
    result_green = allocator.allocate_slot(ev, current_gsi=20, available_renewable_pct=50)
    power_green = result_green.power_level_kw
    
    # Reset allocator
    allocator = SlotAllocator(station_capacity_kw=500, num_slots=10)
    
    # Orange GSI (same vehicle, lower power expected)
    result_orange = allocator.allocate_slot(ev, current_gsi=65, available_renewable_pct=30)
    power_orange = result_orange.power_level_kw
    
    assert power_green >= power_orange
