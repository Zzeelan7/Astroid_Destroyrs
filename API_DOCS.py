"""
API Documentation & Examples
"""

ENDPOINTS = {
    "Grid": {
        "GET /api/grid/status": {
            "description": "Get current grid stress level (GSI)",
            "request": {
                "load_percentage": 65,
                "frequency_hz": 50.1,
                "transformer_temp_pct": 65,
                "renewable_penetration_pct": 35
            },
            "response": {
                "gsi_score": 54.2,
                "status": "🟡 Yellow (Moderate Stress)",
                "charging_policy": "Limit new connections; throttle to 80% power",
                "max_power_kw": 120.0,
                "allow_new_connections": True,
                "v2g_enabled": False
            }
        }
    },
    "Charging": {
        "POST /api/charging/request-slot": {
            "description": "Request a charging slot for an EV",
            "request": {
                "vehicle_id": "EV-001",
                "soc_percent": 25,
                "target_soc_percent": 80,
                "departure_time": "2026-04-21T20:00:00",
                "user_priority": 3,
                "is_v2g_capable": False
            },
            "response": {
                "vehicle_id": "EV-001",
                "slot_id": "slot_1",
                "status": "assigned",
                "power_level_kw": 150.0,
                "estimated_wait_minutes": 0,
                "estimated_charge_time_minutes": 23,
                "reason": "Slot assigned with grid-aware throttling"
            }
        },
        "GET /api/charging/active-sessions": {
            "description": "View all active charging sessions",
            "response": {
                "total_active": 8,
                "queued": 3,
                "sessions": [
                    {
                        "vehicle_id": "EV-001",
                        "power_kw": 22.0,
                        "time_active_minutes": 15
                    }
                ]
            }
        }
    },
    "V2G": {
        "POST /api/v2g/register": {
            "description": "Register a V2G-capable vehicle",
            "request": {
                "vehicle_id": "EV-V2G-001",
                "soc_percent": 75,
                "departure_time": "2026-04-21T21:00:00"
            },
            "response": {
                "vehicle_id": "EV-V2G-001",
                "registered": True,
                "message": "V2G-capable vehicle registered"
            }
        },
        "GET /api/v2g/status": {
            "description": "Get V2G program metrics",
            "response": {
                "registered_vehicles": 12,
                "active_discharges": 3,
                "current_v2g_capacity_kw": 30.0,
                "total_compensation_paid": 450.0
            }
        }
    }
}

# cURL Examples for Demo
DEMO_CURL_COMMANDS = """
# 1. Check API health
curl http://localhost:8000/api/health/

# 2. Get grid status (Green GSI)
curl -X POST http://localhost:8000/api/grid/status \\
  -H "Content-Type: application/json" \\
  -d '{
    "load_percentage": 35,
    "frequency_hz": 50.0,
    "transformer_temp_pct": 40,
    "renewable_penetration_pct": 55
  }'

# 3. Request charging slot
curl -X POST http://localhost:8000/api/charging/request-slot \\
  -H "Content-Type: application/json" \\
  -d '{
    "vehicle_id": "EV-DEMO-001",
    "soc_percent": 25,
    "target_soc_percent": 80,
    "departure_time": "2026-04-21T20:00:00",
    "user_priority": 3,
    "is_v2g_capable": false
  }'

# 4. Trigger high grid stress (Orange GSI)
curl -X POST http://localhost:8000/api/grid/status \\
  -H "Content-Type: application/json" \\
  -d '{
    "load_percentage": 72,
    "frequency_hz": 49.9,
    "transformer_temp_pct": 78,
    "renewable_penetration_pct": 25
  }'

# 5. Trigger critical grid stress (Red GSI + V2G)
curl -X POST http://localhost:8000/api/grid/status \\
  -H "Content-Type: application/json" \\
  -d '{
    "load_percentage": 92,
    "frequency_hz": 49.5,
    "transformer_temp_pct": 88,
    "renewable_penetration_pct": 8
  }'

# 6. Get V2G status
curl http://localhost:8000/api/v2g/status

# 7. Get active sessions
curl http://localhost:8000/api/charging/active-sessions
"""
