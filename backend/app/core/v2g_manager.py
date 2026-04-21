"""
Vehicle-to-Grid (V2G) Management
Handles V2G discharge requests during grid stress events
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List


@dataclass
class V2GParticipant:
    """V2G-capable vehicle profile"""
    vehicle_id: str
    soc_percent: float
    max_discharge_kw: float  # Typically 10 kW for residential safety
    departure_time: datetime
    compensation_requested: Optional[float] = None  # ₹ or credits
    status: str = "available"  # available, discharging, completed


class V2GManager:
    """Manages V2G discharge during critical grid stress"""
    
    # V2G payment model
    DISCHARGE_RATE_PER_KWH = 2.5  # ₹ or equivalent currency units
    MIN_SOC_FOR_DISCHARGE = 60  # Never discharge below 60% SoC
    MAX_DISCHARGE_PER_VEHICLE = 10.0  # kW, residential-safe limit
    MAX_TOTAL_V2G_CAPACITY = 1000.0  # kW, for 100-port station
    
    def __init__(self):
        self.participants: Dict[str, V2GParticipant] = {}
        self.active_discharge_sessions: Dict[str, float] = {}  # vehicle_id -> kW
        self.total_compensation_paid = 0.0
    
    def register_v2g_vehicle(self, vehicle_id: str, soc_pct: float, 
                            departure_time: datetime) -> bool:
        """Register a V2G-capable vehicle during charging session"""
        if soc_pct >= self.MIN_SOC_FOR_DISCHARGE:
            self.participants[vehicle_id] = V2GParticipant(
                vehicle_id=vehicle_id,
                soc_percent=soc_pct,
                max_discharge_kw=self.MAX_DISCHARGE_PER_VEHICLE,
                departure_time=departure_time,
                status="available"
            )
            return True
        return False
    
    def request_v2g_discharge(self, vehicle_id: str, gsi: float,
                             grid_deficit_kw: float) -> Optional[float]:
        """
        Request V2G discharge during critical GSI.
        Returns: discharge power in kW if accepted, None if declined.
        """
        if gsi <= 75 or vehicle_id not in self.participants:
            return None
        
        participant = self.participants[vehicle_id]
        
        # Safety checks
        if participant.soc_percent <= self.MIN_SOC_FOR_DISCHARGE:
            return None
        
        time_to_departure = (participant.departure_time - datetime.now()).total_seconds() / 60
        if time_to_departure < 15:  # Must have at least 15 min to discharge safely
            return None
        
        # Determine discharge power
        discharge_power = min(
            self.MAX_DISCHARGE_PER_VEHICLE,
            grid_deficit_kw / max(1, len([p for p in self.participants if p != participant]))
        )
        
        if discharge_power <= 0.5:  # Minimum viable discharge
            return None
        
        # Start discharge session
        self.active_discharge_sessions[vehicle_id] = discharge_power
        participant.status = "discharging"
        
        return discharge_power
    
    def calculate_v2g_compensation(self, vehicle_id: str, 
                                   discharged_kwh: float) -> float:
        """Calculate compensation for V2G participant"""
        return discharged_kwh * self.DISCHARGE_RATE_PER_KWH
    
    def stop_v2g_discharge(self, vehicle_id: str, 
                          actual_discharged_kwh: float) -> float:
        """Stop discharge and calculate compensation"""
        if vehicle_id in self.active_discharge_sessions:
            del self.active_discharge_sessions[vehicle_id]
        
        if vehicle_id in self.participants:
            participant = self.participants[vehicle_id]
            participant.status = "available"
            compensation = self.calculate_v2g_compensation(vehicle_id, actual_discharged_kwh)
            self.total_compensation_paid += compensation
            return compensation
        
        return 0.0
    
    def get_available_v2g_capacity(self) -> float:
        """Total V2G capacity currently being provided"""
        current_discharge = sum(self.active_discharge_sessions.values())
        return min(self.MAX_TOTAL_V2G_CAPACITY, current_discharge)
    
    def get_status_report(self) -> Dict:
        """Status of V2G program"""
        return {
            "registered_vehicles": len(self.participants),
            "active_discharges": len(self.active_discharge_sessions),
            "current_v2g_capacity_kw": self.get_available_v2g_capacity(),
            "total_compensation_paid": self.total_compensation_paid,
            "available_for_discharge": [
                v for v in self.participants.values() 
                if v.status == "available" and v.soc_percent >= self.MIN_SOC_FOR_DISCHARGE
            ]
        }
