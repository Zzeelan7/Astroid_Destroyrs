"""Unit tests for V2G Manager"""
import pytest
from datetime import datetime, timedelta
from app.core.v2g_manager import V2GManager


@pytest.fixture
def v2g_manager():
    return V2GManager()


def test_register_v2g_vehicle_valid(v2g_manager):
    """Test registering a V2G-capable vehicle"""
    vehicle_id = "EV-V2G-001"
    soc = 75.0
    departure = datetime.now() + timedelta(hours=2)
    
    success = v2g_manager.register_v2g_vehicle(vehicle_id, soc, departure)
    
    assert success is True
    assert vehicle_id in v2g_manager.participants


def test_register_v2g_vehicle_soc_too_low(v2g_manager):
    """Test rejecting registration for low SoC"""
    vehicle_id = "EV-V2G-002"
    soc = 40.0  # Below MIN_SOC_FOR_DISCHARGE (60%)
    departure = datetime.now() + timedelta(hours=2)
    
    success = v2g_manager.register_v2g_vehicle(vehicle_id, soc, departure)
    
    assert success is False
    assert vehicle_id not in v2g_manager.participants


def test_request_v2g_discharge_critical_gsi(v2g_manager):
    """Test V2G discharge request during critical GSI"""
    vehicle_id = "EV-V2G-003"
    soc = 75.0
    departure = datetime.now() + timedelta(hours=2)
    
    v2g_manager.register_v2g_vehicle(vehicle_id, soc, departure)
    
    discharge_power = v2g_manager.request_v2g_discharge(
        vehicle_id, gsi=85.0, grid_deficit_kw=100.0
    )
    
    assert discharge_power is not None
    assert discharge_power > 0
    assert discharge_power <= v2g_manager.MAX_DISCHARGE_PER_VEHICLE


def test_request_v2g_discharge_low_gsi(v2g_manager):
    """Test V2G not offered during low GSI"""
    vehicle_id = "EV-V2G-004"
    soc = 75.0
    departure = datetime.now() + timedelta(hours=2)
    
    v2g_manager.register_v2g_vehicle(vehicle_id, soc, departure)
    
    discharge_power = v2g_manager.request_v2g_discharge(
        vehicle_id, gsi=40.0, grid_deficit_kw=100.0
    )
    
    assert discharge_power is None


def test_v2g_compensation_calculation(v2g_manager):
    """Test V2G compensation calculation"""
    discharged_kwh = 5.0
    compensation = v2g_manager.calculate_v2g_compensation("EV-TEST", discharged_kwh)
    
    assert compensation == discharged_kwh * v2g_manager.DISCHARGE_RATE_PER_KWH
