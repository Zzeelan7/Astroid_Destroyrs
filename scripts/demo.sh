#!/bin/bash
# demo.sh - Quick judge walkthrough script

echo "🚀 GridCharge Demo: 2-Minute Judge Walkthrough"
echo "=============================================="
echo ""

API_URL="http://localhost:8000"

# 1. Check API health
echo "1️⃣  API Health Check..."
curl -s $API_URL/api/health/ | jq .
echo ""
sleep 1

# 2. Get initial grid status (green)
echo "2️⃣  Grid Status: Normal Conditions (Green)"
curl -s -X POST $API_URL/api/grid/status \
  -H "Content-Type: application/json" \
  -d '{
    "load_percentage": 35,
    "frequency_hz": 50.0,
    "transformer_temp_pct": 40,
    "renewable_penetration_pct": 55
  }' | jq .
echo ""
sleep 2

# 3. Request charging slot (green GSI)
echo "3️⃣  EV Arrives: Request Charging Slot (Green GSI)"
curl -s -X POST $API_URL/api/charging/request-slot \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "EV-DEMO-001",
    "soc_percent": 25,
    "target_soc_percent": 80,
    "departure_time": "2026-04-21T20:00:00",
    "user_priority": 3,
    "is_v2g_capable": false
  }' | jq .
echo ""
sleep 2

# 4. Simulate HIGH LOAD event
echo "4️⃣  GRID EVENT: High Load (Orange GSI)"
curl -s -X POST $API_URL/api/grid/status \
  -H "Content-Type: application/json" \
  -d '{
    "load_percentage": 72,
    "frequency_hz": 49.9,
    "transformer_temp_pct": 78,
    "renewable_penetration_pct": 25
  }' | jq .
echo ""
sleep 2

# 5. Request slot during orange
echo "5️⃣  EV Arrives During Orange GSI: Power Throttled"
curl -s -X POST $API_URL/api/charging/request-slot \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "EV-DEMO-002",
    "soc_percent": 15,
    "target_soc_percent": 80,
    "departure_time": "2026-04-21T20:15:00",
    "user_priority": 2,
    "is_v2g_capable": false
  }' | jq .
echo ""
sleep 2

# 6. Simulate CRITICAL event
echo "6️⃣  GRID EVENT: Critical Stress (Red GSI + V2G)"
curl -s -X POST $API_URL/api/grid/status \
  -H "Content-Type: application/json" \
  -d '{
    "load_percentage": 92,
    "frequency_hz": 49.5,
    "transformer_temp_pct": 88,
    "renewable_penetration_pct": 8
  }' | jq .
echo ""
sleep 2

# 7. Request slot during critical (V2G offer)
echo "7️⃣  V2G-Capable EV During Critical: V2G Discharge Offered"
curl -s -X POST $API_URL/api/charging/request-slot \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "EV-V2G-001",
    "soc_percent": 72,
    "target_soc_percent": 85,
    "departure_time": "2026-04-21T21:00:00",
    "user_priority": 4,
    "is_v2g_capable": true
  }' | jq .
echo ""
sleep 2

# 8. Active sessions
echo "8️⃣  View Active Sessions"
curl -s $API_URL/api/charging/active-sessions | jq .
echo ""

# 9. V2G status
echo "9️⃣  V2G Program Status"
curl -s $API_URL/api/v2g/status | jq .
echo ""

echo "✅ Demo Complete! Open http://localhost:3000 to see the dashboard"
