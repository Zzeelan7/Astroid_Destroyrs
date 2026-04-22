import requests
import random
import time
from datetime import datetime, timedelta

API_URL = "http://localhost:8000"

def seed_data():
    print("Seeding GridCharge with 10 vehicles...")
    
    for i in range(1, 11):
        soc = random.randint(10, 60)
        target = min(100, soc + random.randint(30, 50))
        dep_time = datetime.now() + timedelta(minutes=random.randint(60, 240))
        
        payload = {
            "vehicle_id": f"EV-SEED-{1000 + i}",
            "soc_percent": soc,
            "target_soc_percent": target,
            "departure_time": dep_time.isoformat(),
            "user_priority": random.randint(1, 5), # P1 to P5
            "is_v2g_capable": random.choice([True, False, True]) # 66% capable
        }
        
        try:
            res = requests.post(f"{API_URL}/api/charging/request-slot", json=payload)
            if res.status_code == 200:
                print(f"Seeded {payload['vehicle_id']} -> Priority: P{payload['user_priority']} V2G: {payload['is_v2g_capable']}")
            else:
                print(f"Failed to seed {payload['vehicle_id']}: {res.text}")
        except Exception as e:
            print(f"Error seeding {payload['vehicle_id']}: {e}")
            
        time.sleep(0.5)

if __name__ == "__main__":
    seed_data()
