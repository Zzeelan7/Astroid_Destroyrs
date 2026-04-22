"""
Global application state and background grid simulator.
Single source of truth for grid metrics, slot allocator, and V2G manager.
"""
import asyncio
import math
import random
from datetime import datetime, timedelta

from .core.gsi_engine import GSIEngine, GridMetrics
from .core.slot_allocator import SlotAllocator, EVProfile, PriorityTier
from .core.v2g_manager import V2GManager

# ── Realistic EV fleet pool for auto-simulation ─────────────────────────────
_VEHICLE_PREFIXES = ["TAXI", "FLEET", "PUB", "AMB", "DLV", "PRIV"]
_AUTO_EV_INTERVAL = 12   # seconds between auto arrivals (when slots available)


class GridSimulator:
    """
    Simulates realistic grid stress scenarios over time.
    Runs as an asyncio background task.
    """

    # Scenario lifecycle (steps @ 3-second ticks)
    _SCENARIO_DURATIONS = {
        "normal":          (18, 30),   # stay normal 18-30 ticks
        "building_stress": (8,  14),
        "peak_stress":     (5,  10),
        "recovery":        (8,  14),
    }

    def __init__(self):
        self.gsi_engine    = GSIEngine()
        self.slot_allocator = SlotAllocator(station_capacity_kw=1000.0, num_slots=50)
        self.v2g_manager   = V2GManager()

        self._tick           = 0
        self._scenario       = "normal"
        self._scenario_ticks = 0
        self._scenario_limit = random.randint(*self._SCENARIO_DURATIONS["normal"])
        self._auto_ev_tick   = 0

        # Seed with a sensible initial state
        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=32.0,
            frequency_hz=50.0,
            transformer_temp_pct=38.0,
            renewable_penetration_pct=58.0,
        )
        self.level = self.gsi_engine.compute_gsi(self.metrics)

    # ── Background loop ──────────────────────────────────────────────────────

    async def run(self):
        """Main simulation coroutine — called from FastAPI lifespan."""
        while True:
            await asyncio.sleep(3)
            self._step_grid()

    async def run_auto_ev(self):
        """Periodically simulate realistic EV arrivals."""
        while True:
            await asyncio.sleep(_AUTO_EV_INTERVAL)
            self._maybe_add_ev()

    # ── Grid step ────────────────────────────────────────────────────────────

    def _step_grid(self):
        self._tick += 1
        self._scenario_ticks += 1

        # Advance scenario state machine
        if self._scenario_ticks >= self._scenario_limit:
            self._advance_scenario()

        t = self._tick * 0.08

        if self._scenario == "normal":
            load = 25 + 20 * abs(math.sin(t))       + random.gauss(0, 2.5)
            freq = 50.0                               + random.gauss(0, 0.04)
            temp = 30 + 14 * abs(math.sin(t * 0.6)) + random.gauss(0, 1.5)
            ren  = 42 + 32 * abs(math.sin(t * 0.3)) + random.gauss(0, 4)

        elif self._scenario == "building_stress":
            p    = min(1.0, self._scenario_ticks / self._scenario_limit)
            load = 28  + p * 52  + random.gauss(0, 2)
            freq = 50.0 - p * 0.35 + random.gauss(0, 0.06)
            temp = 32  + p * 48  + random.gauss(0, 2)
            ren  = 42  - p * 28  + random.gauss(0, 3)

        elif self._scenario == "peak_stress":
            load = 84 + random.gauss(0, 3)
            freq = 49.52 + random.gauss(0, 0.07)
            temp = 80 + random.gauss(0, 3)
            ren  = 10 + random.gauss(0, 2)

        else:  # recovery
            p    = min(1.0, self._scenario_ticks / self._scenario_limit)
            load = 86  - p * 55  + random.gauss(0, 3)
            freq = 49.52 + p * 0.48 + random.gauss(0, 0.05)
            temp = 82  - p * 46  + random.gauss(0, 2)
            ren  = 8   + p * 44  + random.gauss(0, 3)

        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=         max(8,  min(98, load)),
            frequency_hz=            max(49.0, min(51.0, freq)),
            transformer_temp_pct=    max(12, min(98, temp)),
            renewable_penetration_pct=max(3,  min(95, ren)),
        )
        self.level = self.gsi_engine.compute_gsi(self.metrics)

        # Rebalance power on existing sessions when GSI changes
        self.slot_allocator.rebalance_power(self.level.gsi_score)

        # Auto-register V2G-capable vehicles during stress
        if self.level.v2g_enabled:
            for vid, sess in list(self.slot_allocator.active_sessions.items()):
                ev = sess.get("ev")
                if ev and ev.is_v2g_capable and ev.soc_percent >= 62:
                    self.v2g_manager.register_v2g_vehicle(
                        vid, ev.soc_percent, ev.departure_time
                    )

        # Periodic departure processing
        if self._tick % 4 == 0:
            self.slot_allocator.process_departures()

    def _advance_scenario(self):
        transitions = {
            "normal":          ("building_stress", 0.15),
            "building_stress": ("peak_stress",     0.85),
            "peak_stress":     ("recovery",        0.70),
            "recovery":        ("normal",          1.00),
        }
        next_scenario, prob = transitions[self._scenario]
        if random.random() < prob:
            self._scenario = next_scenario
        else:
            # Stay in current scenario a bit longer
            pass
        self._scenario_ticks = 0
        self._scenario_limit = random.randint(*self._SCENARIO_DURATIONS[self._scenario])

    # ── Auto EV simulation ───────────────────────────────────────────────────

    def _maybe_add_ev(self):
        """Add a realistic EV arrival if there's capacity."""
        available_slots = self.slot_allocator.num_slots - len(self.slot_allocator.active_sessions)
        if available_slots <= 0:
            return
        # Fewer arrivals during high stress
        arrival_prob = 0.9 if self.level.gsi_score <= 55 else 0.4
        if random.random() > arrival_prob:
            return

        prefix = random.choice(_VEHICLE_PREFIXES)
        vid    = f"{prefix}-{random.randint(1000, 9999)}"

        # Priority depends on vehicle type
        priority_map = {
            "AMB":  PriorityTier.P0_EMERGENCY,
            "FLEET": PriorityTier.P2_FLEET_COMMERCIAL,
            "TAXI": PriorityTier.P2_FLEET_COMMERCIAL,
            "DLV":  PriorityTier.P3_PREBOOKED_PUBLIC,
            "PUB":  PriorityTier.P3_PREBOOKED_PUBLIC,
            "PRIV": PriorityTier.P4_WALK_IN_PUBLIC,
        }
        priority  = priority_map.get(prefix, PriorityTier.P4_WALK_IN_PUBLIC)
        soc       = random.randint(8, 65)
        target    = min(100, soc + random.randint(25, 60))
        v2g_cap   = random.random() < 0.25
        depart_h  = random.uniform(0.5, 3.0)
        departure = datetime.now() + timedelta(hours=depart_h)

        ev = EVProfile(
            vehicle_id=vid,
            soc_percent=soc,
            target_soc_percent=target,
            departure_time=departure,
            user_priority=priority,
            is_v2g_capable=v2g_cap,
        )
        self.slot_allocator.allocate_slot(
            ev,
            current_gsi=self.level.gsi_score,
            available_renewable_pct=self.metrics.renewable_penetration_pct,
        )

    # ── Manual controls ──────────────────────────────────────────────────────

    def inject_stress(self):
        """Immediately jump to peak stress scenario."""
        self._scenario       = "peak_stress"
        self._scenario_ticks = 0
        self._scenario_limit = random.randint(*self._SCENARIO_DURATIONS["peak_stress"])

        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=          90 + random.gauss(0, 2),
            frequency_hz=             49.45 + random.gauss(0, 0.06),
            transformer_temp_pct=     86 + random.gauss(0, 2),
            renewable_penetration_pct=7  + random.gauss(0, 1.5),
        )
        self.level = self.gsi_engine.compute_gsi(self.metrics)
        self.slot_allocator.rebalance_power(self.level.gsi_score)

    # ── Status serialization ─────────────────────────────────────────────────

    def get_status(self) -> dict:
        return {
            "gsi_score":                 round(self.level.gsi_score, 2),
            "status":                    self.level.status,
            "charging_policy":           self.level.charging_policy,
            "max_power_kw":              self.level.max_power_kw,
            "allow_new_connections":     self.level.allow_new_connections,
            "v2g_enabled":              self.level.v2g_enabled,
            # Raw metrics (for frontend bars)
            "load_percentage":           round(self.metrics.load_percentage, 1),
            "frequency_hz":              round(self.metrics.frequency_hz, 3),
            "transformer_temp_pct":      round(self.metrics.transformer_temp_pct, 1),
            "renewable_penetration_pct": round(self.metrics.renewable_penetration_pct, 1),
            "scenario":                  self._scenario,
        }


# ── Module-level singleton ────────────────────────────────────────────────────
simulator = GridSimulator()
