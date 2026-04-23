from __future__ import annotations

"""
Global application state and background grid simulator.
Single source of truth for grid metrics, slot allocator, and V2G manager.
"""
import asyncio
import math
import random
from collections import deque
from datetime import datetime, timedelta
from typing import Optional

import httpx

from .core.gsi_engine import GSIEngine, GridMetrics
from .core.slot_allocator import SlotAllocator, EVProfile, PriorityTier
from .core.v2g_manager import V2GManager

# ── Realistic EV fleet pool for auto-simulation ─────────────────────────────
_VEHICLE_PREFIXES = ["TAXI", "FLEET", "PUB", "AMB", "DLV", "PRIV"]
_AUTO_EV_INTERVAL = 12   # seconds between auto arrivals (when slots available)
_BASE_TICK_SECONDS = 3.0
_EXTERNAL_FEED_INTERVAL = 45
_HISTORY_MAX_POINTS = 360


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
        self._paused         = False
        self._speed_multiplier = 1.0
        self._history        = deque(maxlen=_HISTORY_MAX_POINTS)
        self._fault_active   = False
        self._external_signals = {
            "source": "open-meteo",
            "updated_at": None,
            "temperature_c": None,
            "wind_speed_kmh": None,
            "cloud_cover_pct": None,
            "renewable_bias": 0.0,
            "load_bias": 0.0,
            "online": False,
        }
        self._carbon_saved_kg = 0.0

        # Seed with a sensible initial state
        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=32.0,
            frequency_hz=50.0,
            transformer_temp_pct=38.0,
            renewable_penetration_pct=58.0,
        )
        self.level = self.gsi_engine.compute_gsi(self.metrics)
        self._record_history_point()

    # ── Background loop ──────────────────────────────────────────────────────

    async def run(self):
        """Main simulation coroutine — called from FastAPI lifespan."""
        while True:
            await asyncio.sleep(_BASE_TICK_SECONDS / max(0.5, self._speed_multiplier))
            if self._paused:
                continue
            self._step_grid()

    async def run_auto_ev(self):
        """Periodically simulate realistic EV arrivals."""
        while True:
            await asyncio.sleep(_AUTO_EV_INTERVAL)
            if self._paused:
                continue
            self._maybe_add_ev()

    async def run_external_feed(self):
        """Periodically ingest public telemetry for more realistic dynamics."""
        while True:
            await asyncio.sleep(_EXTERNAL_FEED_INTERVAL)
            await self._refresh_external_signals()

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

        # Blend in external weather-derived bias to simulate real-world shifts.
        load += self._external_signals.get("load_bias", 0.0)
        ren += self._external_signals.get("renewable_bias", 0.0)

        if self._fault_active:
            # Fault mode emulates transformer damage and renewable drop.
            load += 10
            temp += 12
            ren -= 18
            freq -= 0.18

        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=         max(8,  min(98, load)),
            frequency_hz=            max(49.0, min(51.0, freq)),
            transformer_temp_pct=    max(12, min(98, temp)),
            renewable_penetration_pct=max(3,  min(95, ren)),
        )
        old_level = getattr(self, "level", None)
        self.level = self.gsi_engine.compute_gsi(self.metrics)
        
        if old_level and old_level.status != self.level.status:
            try:
                from .api.ws import manager
                asyncio.create_task(manager.broadcast({
                    "type": "GSI_THRESHOLD_CROSSED",
                    "old_status": old_level.status,
                    "new_status": self.level.status,
                    "gsi_score": self.level.gsi_score
                }))
            except ImportError:
                pass
                
        self._update_carbon_saved()
        self._record_history_point()

        # Rebalance power on existing sessions when GSI changes
        self.slot_allocator.rebalance_power(self.level.gsi_score)

        # Auto-register and trigger V2G-capable vehicles during stress
        if self.level.v2g_enabled or self.level.gsi_score > 75:
            for vid, sess in list(self.slot_allocator.active_sessions.items()):
                ev = sess.get("ev")
                if ev and ev.is_v2g_capable and ev.soc_percent >= 30:
                    # Register if not already in participants
                    if vid not in self.v2g_manager.participants:
                        self.v2g_manager.register_v2g_vehicle(
                            vid, ev.soc_percent, ev.departure_time
                        )
                    
                    # Trigger discharge if GSI is Red (> 75)
                    if self.level.gsi_score > 75:
                        if vid not in self.v2g_manager.active_discharge_sessions:
                            # Estimate deficit based on load overflow (simplified)
                            deficit = max(20.0, (self.metrics.load_percentage - 80) * 10)
                            self.v2g_manager.request_v2g_discharge(vid, self.level.gsi_score, deficit)
                        
                        # Live compensation: add small amount per tick based on discharge power
                        # (simplified: 10kW * 3s / 3600 = 0.0083 kWh; 0.0083 * 2.5 = 0.02 INR)
                        power = self.v2g_manager.active_discharge_sessions.get(vid, 0.0)
                        kwh_this_tick = (power * _BASE_TICK_SECONDS / 3600.0) * self._speed_multiplier
                        self.v2g_manager.add_compensation(vid, kwh_this_tick * self.v2g_manager.DISCHARGE_RATE_PER_KWH)
                        
                        try:
                            from .api.ws import manager
                            participant = self.v2g_manager.participants[vid]
                            asyncio.create_task(manager.broadcast({
                                "type": "V2G_EARNINGS_UPDATE",
                                "session_id": vid,
                                "energy_discharged_kwh": participant.compensation_earned_inr / self.v2g_manager.DISCHARGE_RATE_PER_KWH,
                                "compensation_inr": participant.compensation_earned_inr,
                                "total_paid": self.v2g_manager.total_compensation_paid
                            }))
                        except ImportError:
                            pass
        
        # Stop V2G discharge if stress subsides
        if self.level.gsi_score < 60:
            for vid in list(self.v2g_manager.active_discharge_sessions.keys()):
                # For demo, we just stop it and pay out (discharged 0.5 kWh per tick approx)
                self.v2g_manager.stop_v2g_discharge(vid, discharged_kwh=0.5)

        # Periodic departure and queue processing
        if self._tick % 4 == 0:
            self.slot_allocator.process_departures(self.level.gsi_score)
        elif len(self.slot_allocator.active_sessions) < self.slot_allocator.num_slots:
            # Try to fill slots from queue even if no departures this tick
            self.slot_allocator.process_queue(self.level.gsi_score)

        self._flush_db()

    def _flush_db(self):
        from .db.database import SessionLocal
        from .db.models import V2GSession
        
        for vid, participant in list(self.v2g_manager.participants.items()):
            db = SessionLocal()
            try:
                # Wrap each participant's DB write in its own try/except/commit block (BUG-B5)
                db_session = db.query(V2GSession).filter(V2GSession.vehicle_id == vid).first()
                if not db_session:
                    db_session = V2GSession(id=f"{vid}-v2g", vehicle_id=vid)
                    db.add(db_session)
                
                db_session.status = participant.status
                db_session.compensation_earned_inr = participant.compensation_earned_inr
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"DB Flush Error for vehicle {vid}: {e}")
            finally:
                db.close()

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

    async def _refresh_external_signals(self):
        """Fetch weather signals and map them into load/renewable bias."""
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude=28.6139&longitude=77.2090"
            "&current=temperature_2m,wind_speed_10m,cloud_cover"
        )
        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.get(url)
                res.raise_for_status()
                data = res.json().get("current", {})

            temp = float(data.get("temperature_2m", 30.0))
            wind = float(data.get("wind_speed_10m", 10.0))
            cloud = float(data.get("cloud_cover", 45.0))
            solar_factor = max(0.15, 1 - (cloud / 100))
            renewable_bias = (solar_factor - 0.5) * 20 + (wind - 10) * 0.35
            load_bias = max(0.0, temp - 28.0) * 0.65

            self._external_signals.update({
                "updated_at": datetime.now().isoformat(),
                "temperature_c": round(temp, 2),
                "wind_speed_kmh": round(wind, 2),
                "cloud_cover_pct": round(cloud, 2),
                "renewable_bias": round(renewable_bias, 2),
                "load_bias": round(load_bias, 2),
                "online": True,
            })
        except Exception:
            self._external_signals.update({
                "updated_at": datetime.now().isoformat(),
                "online": False,
            })

    def _record_history_point(self):
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "gsi_score": round(self.level.gsi_score, 2),
            "load_percentage": round(self.metrics.load_percentage, 1),
            "renewable_penetration_pct": round(self.metrics.renewable_penetration_pct, 1),
            "transformer_temp_pct": round(self.metrics.transformer_temp_pct, 1),
            "frequency_hz": round(self.metrics.frequency_hz, 3),
            "scenario": self._scenario,
            "active_sessions": len(self.slot_allocator.active_sessions),
            "queued_sessions": len(self.slot_allocator.queue),
            "carbon_saved_kg": round(self._carbon_saved_kg, 2),
            "fault_active": self._fault_active,
        })

    def _update_carbon_saved(self):
        total_power_kw = sum(
            sess.get("power_kw", 0.0) for sess in self.slot_allocator.active_sessions.values()
        )
        renewable_factor = max(0.0, min(1.0, self.metrics.renewable_penetration_pct / 100.0))
        hours_per_tick = (_BASE_TICK_SECONDS / 3600.0) * self._speed_multiplier
        # Simple estimate: each renewable kWh offsets ~0.7 kgCO2.
        renewable_kwh = total_power_kw * renewable_factor * hours_per_tick
        self._carbon_saved_kg += renewable_kwh * 0.7

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

    def inject_transformer_failure(self):
        """Simulate severe local transformer outage."""
        self._fault_active = True
        self._scenario = "peak_stress"
        self._scenario_ticks = 0
        self._scenario_limit = random.randint(*self._SCENARIO_DURATIONS["peak_stress"])
        self.metrics = GridMetrics(
            timestamp=datetime.now(),
            load_percentage=95 + random.gauss(0, 1.5),
            frequency_hz=49.3 + random.gauss(0, 0.05),
            transformer_temp_pct=96 + random.gauss(0, 1.0),
            renewable_penetration_pct=4 + random.gauss(0, 1.0),
        )
        self.level = self.gsi_engine.compute_gsi(self.metrics)
        self.slot_allocator.rebalance_power(self.level.gsi_score)

    def clear_transformer_failure(self):
        self._fault_active = False

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
            "fault_active":              self._fault_active,
            "speed_multiplier":          self._speed_multiplier,
            "paused":                    self._paused,
            "carbon_saved_kg":           round(self._carbon_saved_kg, 2),
        }

    def get_history(self, limit: int = 120) -> list[dict]:
        if limit <= 0:
            return []
        return list(self._history)[-min(limit, _HISTORY_MAX_POINTS):]

    def get_external_signals(self) -> dict:
        return dict(self._external_signals)

    def set_simulation_state(self, paused: Optional[bool] = None, speed_multiplier: Optional[float] = None) -> dict:
        if paused is not None:
            self._paused = paused
        if speed_multiplier is not None:
            self._speed_multiplier = max(0.5, min(4.0, speed_multiplier))
        return {
            "paused": self._paused,
            "speed_multiplier": self._speed_multiplier,
        }

    def get_forecast(self, hours_ahead: int = 24) -> dict:
        points = list(self._history)[-60:]
        if len(points) < 6:
            return {
                "forecast_hours": hours_ahead,
                "status": "insufficient_history",
                "predicted_peak_gsi": round(self.level.gsi_score, 2),
                "predicted_average_gsi": round(self.level.gsi_score, 2),
            }

        recent = [p["gsi_score"] for p in points]
        moving_avg = sum(recent[-12:]) / min(12, len(recent))
        deltas = [recent[i] - recent[i - 1] for i in range(1, len(recent))]
        trend = sum(deltas[-10:]) / min(10, len(deltas))
        projected_peak = max(0.0, min(100.0, moving_avg + trend * 6))
        return {
            "forecast_hours": hours_ahead,
            "status": "ok",
            "method": "moving_average_plus_trend",
            "predicted_peak_gsi": round(projected_peak, 2),
            "predicted_average_gsi": round(moving_avg, 2),
            "trend_per_tick": round(trend, 3),
        }


# ── Module-level singleton ────────────────────────────────────────────────────
simulator = GridSimulator()
