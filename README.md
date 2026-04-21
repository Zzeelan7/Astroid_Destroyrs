# GridCharge: Grid Stress-Aware EV Charging Slot Allocation

🚀 **Hackathon-Ready MVP** | Production Docker Setup | Real Optimization Algorithms

---

## 🎯 What This Does

A complete smart charging system that:
- ✅ Computes **real-time Grid Stress Index (GSI)** on 0-100 scale
- ✅ Allocates charging slots using **6-tier priority** (emergency → opportunistic)
- ✅ **Throttles power dynamically** as grid stress increases (150kW → 3.7kW)
- ✅ Enables **V2G discharge** during critical grid events (Red GSI > 75)
- ✅ **Optimizes for renewable energy** (cheaper charging during green windows)
- ✅ **One-command Docker Compose** deployment

---

## 🏗️ Project Structure

```
Astroid_destroyrs/
├── backend/                    # FastAPI microservice
│   ├── app/
│   │   ├── core/              # Domain logic (GSI, slot allocator, V2G)
│   │   ├── api/               # REST endpoints
│   │   ├── models/            # Pydantic schemas
│   │   └── main.py            # FastAPI app
│   └── requirements.txt
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── App.jsx            # Main component
│   │   └── index.css          # Tailwind styles
│   └── package.json
├── simulator/                  # EV simulator + grid stress events
│   ├── simulator.py           # Demo scenario generator
│   └── requirements.txt
├── tests/                      # Unit tests
│   ├── test_gsi_engine.py     # GSI algorithm tests
│   ├── test_slot_allocator.py # Slot logic tests
│   └── test_v2g_manager.py    # V2G discharge tests
├── docker/                     # Dockerfiles
│   ├── Dockerfile.api
│   ├── Dockerfile.frontend
│   ├── Dockerfile.simulator
│   └── mosquitto.conf
├── scripts/                    # Demo & test scripts
│   ├── demo.sh                # Judge walkthrough
│   └── run-tests.sh           # Test runner
└── docker-compose.yml          # Full stack orchestration
```

---

## ⚡ Quick Start (Judge Demo)

### 1. Start the Stack

```bash
cd C:\Users\zzeel\OneDrive\Desktop\Astroid_destroyrs
docker compose up --build
```

This spins up:
- **FastAPI** backend on http://localhost:8000
- **React** frontend on http://localhost:3000
- **PostgreSQL** database
- **Redis** cache
- **MQTT** broker (for IoT sensors)
- **EV Simulator** (optional)

### 2. Open Browser

```
Frontend Dashboard: http://localhost:3000
API Swagger Docs:  http://localhost:8000/docs
```

### 3. Run 2-Minute Judge Demo

```bash
bash scripts/demo.sh
```

This script:
1. Tests API health
2. Simulates **Green GSI** → EV gets 150 kW
3. Triggers **Orange GSI** → Power throttled to 22 kW
4. Triggers **Red GSI** → V2G discharge offer activated
5. Shows active sessions and V2G status

---

## 🧠 Core Algorithms

### GSI Engine (Grid Stress Index)

```python
GSI = 0.40×(Load%) + 0.30×(Freq Dev Index) 
    + 0.20×(Transformer Temp%) - 0.10×(Renewable%)
```

**Policy Tiers:**
| GSI Range | Status | Policy |
|-----------|--------|--------|
| 0–30     | 🟢 Green | All slots open; 150 kW DC fast |
| 31–55    | 🟡 Yellow | Throttle to 80% power (22 kW) |
| 56–75    | 🟠 Orange | Priority-only slots; 7 kW |
| 76–100   | 🔴 Red | P0/P1 only; V2G activated; 3.7 kW |

### Slot Allocation (Priority-Based)

**Priority Tiers (P0 = Emergency → P5 = Opportunistic):**
- **P0**: Ambulances/fire → Never deferred
- **P1**: Battery critical (<10% SoC) → Max 5 min deferral
- **P2**: Fleet/taxis → Max 15 min deferral
- **P3**: Pre-booked public → Max 20 min deferral
- **P4**: Walk-in public → Max 45 min deferral
- **P5**: Opportunity charge (>70% SoC) → Fully flexible

**Score = `0.3×(1/SoC) + 0.4×(Tier Weight) + 0.2×(Wait Impact) - 0.1×(GSI Penalty)`**

### V2G Discharge (Grid Stress Relief)

- **Triggered when:** GSI > 75 (Red)
- **Source:** Vehicles with SoC > 60% and >15 min to departure
- **Power:** Up to 10 kW per vehicle (residential-safe)
- **Compensation:** ₹2.5/kWh or charging credits
- **Aggregate Capacity:** ~1 MW at 100-port station

---

## 🧪 Tests

Run the full test suite:

```bash
pytest tests/ -v --cov=app
```

Covers:
- ✅ GSI score calculation for all 4 tiers
- ✅ Renewable energy impact on GSI
- ✅ Slot allocation priority ordering
- ✅ Power throttling by GSI level
- ✅ V2G discharge eligibility & compensation

---

## 📊 API Endpoints

### Grid Monitoring
```
POST /api/grid/status → Get current GSI
GET  /api/grid/forecast → Predict next 24h stress
```

### Charging Management
```
POST /api/charging/request-slot → Allocate slot to EV
GET  /api/charging/active-sessions → View all active charges
POST /api/charging/rebalance → Trigger power rebalancing
```

### V2G Program
```
POST /api/v2g/register → Register V2G vehicle
POST /api/v2g/request-discharge → Request discharge during crisis
GET  /api/v2g/status → V2G program metrics
```

### Health & Info
```
GET  /api/health/ → Service status
GET  / → API root
GET  /docs → OpenAPI/Swagger documentation
```

---

## 🎬 Judge Walkthrough Flow

**Total Time: 2 minutes**

| Time | Action | Expected Result |
|------|--------|-----------------|
| 0:00 | API health check | ✅ Service online |
| 0:15 | Grid Green; EV arrives | ✅ Slot assigned; 150 kW |
| 0:30 | Grid transitions Orange | ⚠️ Power throttled to 22 kW |
| 1:00 | Grid Critical (Red) | 🔴 V2G offer activated |
| 1:15 | Show active sessions | 📊 Real-time queue visible |
| 1:30 | Show V2G status | 💰 Compensation & capacity |
| 2:00 | Demo complete | 🚀 All features demonstrated |

---

## 🏆 What Impresses Judges

1. **Real Algorithm:** GSI isn't hand-waved; it's a proper weighted formula with 4 tiers
2. **Priority System:** 6-tier slot allocation with hard constraints & deferrals
3. **V2G Integration:** Actually offers discharge during grid stress, calculates compensation
4. **Renewable Optimization:** GSI includes renewable % (negative weight = lower stress)
5. **Adaptive Throttling:** Power gracefully reduces (150→22→7→3.7 kW), never sudden cuts
6. **Docker Ready:** One command deploys everything; judges can run it locally
7. **Tests Included:** Proves algorithms work correctly under edge cases
8. **Scalable Design:** 3-layer architecture (cloud AI + edge controller + physical) hints at production readiness

---

## 🚀 Next Steps (Post-Hackathon)

1. **LSTM Forecasting:** Train on real utility data to predict GSI 24-48h ahead
2. **Kubernetes Deployment:** Scale to 1000+ charging stations
3. **Real OCPP Integration:** Connect to actual EV charging networks
4. **Mobile App:** Native iOS/Android for real-time slot reservations
5. **Dashboard Analytics:** Revenue by time-of-day, carbon savings, V2G metrics
6. **Cloud Storage:** PostgreSQL → Managed RDS + Time-series DB for grid telemetry

---

## 📝 License & Contact

Built for hackathon. Production deployment requires utility partnerships & regulatory compliance.

---

**🎯 TL;DR for Judges:**
- ✅ Fully functional smart charging system
- ✅ Real optimization algorithms (not toy code)
- ✅ Docker Compose = instant local demo
- ✅ 2-minute walkthrough shows all features
- ✅ Unit tests prove correctness
- ✅ Hackathon submission ready

**Deploy:** `docker compose up --build`
**Demo:** `bash scripts/demo.sh`
**Dashboard:** http://localhost:3000
