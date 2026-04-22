"""API models (request/response schemas)"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GridMetricsRequest(BaseModel):
    """Grid telemetry input"""
    load_percentage: float = Field(..., ge=0, le=100)
    frequency_hz: float = Field(...)
    transformer_temp_pct: float = Field(..., ge=0, le=100)
    renewable_penetration_pct: float = Field(..., ge=0, le=100)


class GridStatusResponse(BaseModel):
    """Grid status output"""
    gsi_score: float
    status: str
    charging_policy: str
    max_power_kw: float
    allow_new_connections: bool
    v2g_enabled: bool
    # Raw sensor metrics (populated by simulator)
    load_percentage: Optional[float] = None
    frequency_hz: Optional[float] = None
    transformer_temp_pct: Optional[float] = None
    renewable_penetration_pct: Optional[float] = None
    scenario: Optional[str] = None
    fault_active: Optional[bool] = None
    speed_multiplier: Optional[float] = None
    paused: Optional[bool] = None
    carbon_saved_kg: Optional[float] = None


class ChargingRequestRequest(BaseModel):
    """EV charging request"""
    vehicle_id: str
    soc_percent: float = Field(..., ge=0, le=100)
    target_soc_percent: float = Field(..., ge=0, le=100)
    departure_time: datetime
    user_priority: int = Field(..., ge=0, le=5)
    is_v2g_capable: bool = False


class SimulationLocation(BaseModel):
    """Vehicle location payload for simulation."""
    lat: float
    lng: float
    name: str


class SimulationRequest(BaseModel):
    """Manual EV simulation request."""
    vehicle_id: str
    soc_percent: float = Field(..., ge=0, le=100)
    target_soc_percent: float = Field(..., ge=0, le=100)
    departure_time: datetime
    user_priority: int = Field(..., ge=0, le=5)
    is_v2g_capable: bool = False
    location: SimulationLocation


class SlotAllocationResponse(BaseModel):
    """Slot allocation result"""
    vehicle_id: str
    slot_id: Optional[str]
    status: str
    power_level_kw: float
    estimated_wait_minutes: int
    estimated_charge_time_minutes: int
    reason: str


class SimulationResponse(SlotAllocationResponse):
    """Simulation prediction payload with allocation details."""
    allocated_power_kw: float
    estimated_cost_inr: float
    carbon_offset_kg: float
    gsi_at_request: float
    recommendation: str
    optimal_start_window: datetime
    slot_status: str
    location: SimulationLocation


class V2GOfferRequest(BaseModel):
    """V2G discharge offer"""
    vehicle_id: str
    soc_percent: float
    departure_time: datetime


class V2GStatusResponse(BaseModel):
    """V2G program status"""
    registered_vehicles: int
    active_discharges: int
    current_v2g_capacity_kw: float
    total_compensation_paid: float
