"""
Slot Allocation Engine (SAE)
Assigns EV charging slots using multi-objective optimization:
- Minimize user wait time
- Minimize grid stress contribution
- Maximize renewable energy utilization
"""
from enum import IntEnum
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import heapq


class PriorityTier(IntEnum):
    """EV priority tiers (lower number = higher priority)"""
    P0_EMERGENCY = 0  # Ambulance, police, fire — never deferred
    P1_CRITICAL_LOW_BATTERY = 1  # SoC < 10% — max 5 min defer
    P2_FLEET_COMMERCIAL = 2  # Taxis, delivery — max 15 min defer
    P3_PREBOOKED_PUBLIC = 3  # App reservation — max 20 min defer
    P4_WALK_IN_PUBLIC = 4  # No reservation — max 45 min defer
    P5_OPPORTUNISTIC = 5  # SoC > 70%, no rush — fully flexible


class ChargingLevel:
    """Adaptive power throttling levels (kW)"""
    FLOOR = 3.7    # 3.7 kW AC floor, never go below
    LEVEL_1 = 3.7  # 3.7 kW standard
    LEVEL_2 = 7.4  # 7.4 kW AC
    LEVEL_3 = 22.0 # 22 kW 3-phase AC
    LEVEL_4 = 150.0 # 150 kW DC fast


@dataclass
class EVProfile:
    """Electric vehicle charging request profile"""
    vehicle_id: str
    soc_percent: float  # State of charge
    target_soc_percent: float
    departure_time: datetime
    user_priority: PriorityTier
    is_v2g_capable: bool = False
    estimated_departure_confidence: float = 0.85  # How confident is departure time


@dataclass
class SlotAllocation:
    """Result of slot assignment"""
    vehicle_id: str
    slot_id: Optional[str]
    status: str  # "assigned", "queued", "deferred", "v2g_offer"
    power_level_kw: float
    estimated_wait_minutes: int
    estimated_charge_time_minutes: int
    reason: str


class SlotAllocator:
    """Priority-based slot allocation engine"""
    
    # Deferral time limits per tier (minutes)
    DEFERRAL_LIMITS = {
        PriorityTier.P0_EMERGENCY: 0,
        PriorityTier.P1_CRITICAL_LOW_BATTERY: 5,
        PriorityTier.P2_FLEET_COMMERCIAL: 15,
        PriorityTier.P3_PREBOOKED_PUBLIC: 20,
        PriorityTier.P4_WALK_IN_PUBLIC: 45,
        PriorityTier.P5_OPPORTUNISTIC: 999,  # Fully flexible
    }
    
    def __init__(self, station_capacity_kw: float = 1000.0, num_slots: int = 50):
        self.station_capacity_kw = station_capacity_kw
        self.num_slots = num_slots
        self.active_sessions: Dict[str, Dict] = {}  # vehicle_id -> session data
        self.queue: List[tuple] = []  # Priority queue
        self.v2g_participants: Dict[str, float] = {}  # vehicle_id -> available_kw
    
    def allocate_slot(self, ev: EVProfile, current_gsi: float, 
                     available_renewable_pct: float = 0) -> SlotAllocation:
        """
        Main allocation logic with priority scoring.
        
        Args:
            ev: EV charging profile
            current_gsi: Current Grid Stress Index (0-100)
            available_renewable_pct: % of available power from renewables
            
        Returns:
            SlotAllocation result
        """
        # Step 1: Hard rejection in critical GSI
        if current_gsi > 75:  # Red GSI
            if ev.user_priority not in [PriorityTier.P0_EMERGENCY, PriorityTier.P1_CRITICAL_LOW_BATTERY]:
                # Offer V2G instead
                if ev.is_v2g_capable and ev.soc_percent > 60:
                    return SlotAllocation(
                        vehicle_id=ev.vehicle_id,
                        slot_id="v2g_offer",
                        status="v2g_offer",
                        power_level_kw=10.0,
                        estimated_wait_minutes=0,
                        estimated_charge_time_minutes=0,
                        reason="Grid critical; V2G discharge compensation offered"
                    )
                else:
                    return SlotAllocation(
                        vehicle_id=ev.vehicle_id,
                        slot_id=None,
                        status="queued",
                        power_level_kw=0,
                        estimated_wait_minutes=999,
                        estimated_charge_time_minutes=0,
                        reason="Grid critical stress; queued for later"
                    )
        
        # Step 2: Compute priority score
        priority_score = self._compute_priority_score(
            ev, current_gsi, available_renewable_pct
        )
        
        # Step 3: Check available slots and power
        available_slots = self.num_slots - len(self.active_sessions)
        current_load_kw = sum(s.get("power_kw", 0) for s in self.active_sessions.values())
        available_power_kw = self.station_capacity_kw - current_load_kw
        
        if available_slots > 0 and available_power_kw >= ChargingLevel.FLOOR:
            # Allocate immediately
            power_level = self._compute_power_level(current_gsi, available_power_kw)
            slot_id = f"slot_{len(self.active_sessions) + 1}"
            
            self.active_sessions[ev.vehicle_id] = {
                "power_kw": power_level,
                "start_time": datetime.now(),
                "ev": ev,
            }
            
            charge_time = self._estimate_charge_time(
                ev.soc_percent, ev.target_soc_percent, power_level
            )
            
            return SlotAllocation(
                vehicle_id=ev.vehicle_id,
                slot_id=slot_id,
                status="assigned",
                power_level_kw=power_level,
                estimated_wait_minutes=0,
                estimated_charge_time_minutes=charge_time,
                reason="Slot assigned with grid-aware throttling"
            )
        else:
            # Queue
            estimated_wait = self._estimate_queue_wait(ev.user_priority)
            
            heapq.heappush(self.queue, (priority_score, ev.vehicle_id, ev))
            
            return SlotAllocation(
                vehicle_id=ev.vehicle_id,
                slot_id=None,
                status="queued",
                power_level_kw=0,
                estimated_wait_minutes=estimated_wait,
                estimated_charge_time_minutes=0,
                reason=f"Queued; estimated wait {estimated_wait} min"
            )
    
    def _compute_priority_score(self, ev: EVProfile, gsi: float, 
                                renewable_pct: float) -> float:
        """
        Multi-objective scoring:
        - Lower SoC → higher priority (more urgent)
        - Higher tier weight
        - Renewable boost if available
        - GSI penalty for non-essential tiers
        """
        # Inverse SoC: lower battery = higher urgency
        soc_score = (100 - ev.soc_percent) / 100  # 0-1 scale
        
        # Tier weight
        tier_score = (5 - ev.user_priority) / 5  # P0 = 1.0, P5 = 0.0
        
        # Renewable bonus
        renewable_bonus = renewable_pct / 100 if renewable_pct > 60 else 0
        
        # GSI penalty for non-urgent tiers
        gsi_penalty = 0
        if gsi > 55 and ev.user_priority >= PriorityTier.P3_PREBOOKED_PUBLIC:
            gsi_penalty = (gsi - 55) / 100
        
        combined_score = (soc_score * 0.3 + tier_score * 0.4 + 
                         renewable_bonus * 0.2 - gsi_penalty * 0.1)
        
        return combined_score
    
    def _compute_power_level(self, gsi: float, available_power: float) -> float:
        """Adaptive throttling: reduce power as GSI increases"""
        if gsi <= 30:
            return min(available_power, ChargingLevel.LEVEL_4)  # 150 kW (100%)
        elif gsi <= 50:
            return min(available_power, ChargingLevel.LEVEL_4 * 0.5)  # 75 kW (50%)
        elif gsi <= 75:
            return min(available_power, ChargingLevel.LEVEL_2)  # 7.4 kW
        else:
            return ChargingLevel.FLOOR  # 3.7 kW
    
    def _estimate_charge_time(self, soc_from: float, soc_to: float, 
                              power_kw: float) -> int:
        """Rough estimate (assumes 50 kWh battery, simplified curve)"""
        battery_capacity_kwh = 50
        energy_needed_kwh = (soc_to - soc_from) / 100 * battery_capacity_kwh
        hours = energy_needed_kwh / power_kw if power_kw > 0 else 999
        return max(1, int(hours * 60))  # Convert to minutes, min 1 min
    
    def _estimate_queue_wait(self, priority: PriorityTier) -> int:
        """Heuristic queue wait time based on tier"""
        base_wait = len(self.queue) * 3  # 3 min per queued vehicle
        
        if priority == PriorityTier.P0_EMERGENCY:
            return 0
        elif priority == PriorityTier.P1_CRITICAL_LOW_BATTERY:
            return min(5, base_wait)
        else:
            return base_wait
    
    def rebalance_power(self, gsi: float) -> None:
        """
        Periodic re-optimization: if GSI changes, adjust power levels for all sessions.
        Allows both throttling down (stress increase) and ramping up (stress decrease).
        """
        import asyncio
        try:
            from ..api.ws import manager
        except ImportError:
            manager = None

        for vehicle_id, session in list(self.active_sessions.items()):
            old_power = session.get("power_kw", 0)
            new_power = self._compute_power_level(gsi, self.station_capacity_kw)
            
            # Update power level to reflect current grid conditions
            session["power_kw"] = new_power
            
            if manager and old_power == ChargingLevel.FLOOR and new_power > old_power:
                asyncio.create_task(manager.broadcast({
                    "type": "POWER_RAMP",
                    "session_id": vehicle_id,
                    "new_power_kw": new_power
                }))
    
    def process_departures(self, current_gsi: float) -> List[str]:
        """Check for vehicles that should depart; free up slots and pull from queue."""
        now = datetime.now()
        departed = []
        
        for vehicle_id, session in list(self.active_sessions.items()):
            ev = session["ev"]
            time_remaining = (ev.departure_time - now).total_seconds() / 60
            
            # If departure time reached, free slot
            if time_remaining <= 0:
                self.active_sessions.pop(vehicle_id, None)
                departed.append(vehicle_id)
        
        # After freeing slots, try to fill them from the queue
        if departed or len(self.active_sessions) < self.num_slots:
            self.process_queue(current_gsi)
            
        return departed

    def process_queue(self, current_gsi: float) -> int:
        """Attempt to move vehicles from priority queue to active slots."""
        processed = 0
        while self.queue and len(self.active_sessions) < self.num_slots:
            # Check available power
            current_load = sum(s.get("power_kw", 0) for s in self.active_sessions.values())
            available_power = self.station_capacity_kw - current_load
            
            if available_power < ChargingLevel.FLOOR:
                break
                
            # Pop highest priority (lowest score in heapq)
            score, vid, ev = heapq.heappop(self.queue)
            
            # Double check if already active (shouldn't happen with heapq usually)
            if vid in self.active_sessions:
                continue
                
            power = self._compute_power_level(current_gsi, available_power)
            self.active_sessions[vid] = {
                "power_kw": power,
                "start_time": datetime.now(),
                "ev": ev,
            }
            processed += 1
            
        return processed
