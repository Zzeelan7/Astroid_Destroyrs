"""
EV Simulator for Demo/Testing
Generates realistic charging requests and grid stress events
"""
import asyncio
import random
from datetime import datetime, timedelta
import httpx
from typing import List

API_URL = "http://localhost:8000"


class EVSimulator:
    """Simulates EV charging requests"""
    
    VEHICLE_IDS = [f"EV-{i:04d}" for i in range(100, 110)]
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def simulate_ev_arrival(self):
        """Simulate a random EV arrival"""
        vehicle_id = random.choice(self.VEHICLE_IDS)
        soc = random.randint(10, 95)
        target_soc = min(100, soc + random.randint(20, 50))
        departure_time = datetime.now() + timedelta(minutes=random.randint(30, 240))
        priority = random.randint(2, 4)  # P2-P4 (medium priority)
        is_v2g = random.choice([True, False])
        
        try:
            response = await self.client.post(
                f"{API_URL}/api/charging/request-slot",
                json={
                    "vehicle_id": vehicle_id,
                    "soc_percent": soc,
                    "target_soc_percent": target_soc,
                    "departure_time": departure_time.isoformat(),
                    "user_priority": priority,
                    "is_v2g_capable": is_v2g
                }
            )
            result = response.json()
            print(f"✅ {vehicle_id} | SoC: {soc}% → {target_soc}% | "
                  f"Status: {result['status']} | Power: {result['power_level_kw']} kW")
            return result
        except Exception as e:
            print(f"❌ Error simulating EV {vehicle_id}: {e}")
            return None
    
    async def simulate_grid_stress_event(self, event_type: str):
        """Simulate a grid stress event"""
        if event_type == "high_load":
            metrics = {
                "load_percentage": 85.0,
                "frequency_hz": 49.8,
                "transformer_temp_pct": 78.0,
                "renewable_penetration_pct": 25.0
            }
            description = "🟠 HIGH LOAD EVENT - Transformer temp spike"
        elif event_type == "critical":
            metrics = {
                "load_percentage": 95.0,
                "frequency_hz": 49.5,
                "transformer_temp_pct": 88.0,
                "renewable_penetration_pct": 10.0
            }
            description = "🔴 CRITICAL GRID STRESS - V2G activated"
        else:  # normal
            metrics = {
                "load_percentage": random.randint(30, 60),
                "frequency_hz": 50.0 + (random.random() - 0.5) * 0.1,
                "transformer_temp_pct": random.randint(30, 50),
                "renewable_penetration_pct": random.randint(20, 70)
            }
            description = "🟢 NORMAL CONDITIONS"
        
        try:
            response = await self.client.post(
                f"{API_URL}/api/grid/status",
                json=metrics
            )
            result = response.json()
            print(f"\n{description}")
            print(f"  GSI: {result['gsi_score']:.1f} | {result['status']}")
            print(f"  Policy: {result['charging_policy']}")
            return result
        except Exception as e:
            print(f"❌ Error in grid event: {e}")
            return None
    
    async def run_demo_scenario(self, duration_seconds: int = 120):
        """Run a complete demo scenario"""
        print(f"\n🚀 Starting {duration_seconds}s demo scenario...")
        
        events = [
            ("normal", 0),
            ("simulate_ev", 5),
            ("simulate_ev", 10),
            ("simulate_ev", 15),
            ("high_load", 30),
            ("simulate_ev", 35),
            ("simulate_ev", 40),
            ("critical", 60),
            ("simulate_ev", 65),
            ("simulate_ev", 70),
            ("normal", 90),
            ("simulate_ev", 100),
        ]
        
        start = datetime.now()
        
        for event_type, trigger_time in events:
            if trigger_time > duration_seconds:
                break
            
            # Wait until trigger time
            while (datetime.now() - start).total_seconds() < trigger_time:
                await asyncio.sleep(0.5)
            
            if event_type == "simulate_ev":
                await self.simulate_ev_arrival()
            else:
                await self.simulate_grid_stress_event(event_type)
        
        print(f"\n✅ Demo scenario complete!")
        await self.client.aclose()


async def main():
    simulator = EVSimulator()
    await simulator.run_demo_scenario(duration_seconds=120)


if __name__ == "__main__":
    asyncio.run(main())
