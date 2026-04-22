# GridCharge: Grid Stress-Aware EV Charging System

🚀 **Next-Gen Smart Charging** | 3D Visualization | Real-Time Optimization | Automated V2G

---

## 🎯 What This Does

A complete smart charging system designed to stabilize the power grid while meeting EV user needs:
- ✅ **Dynamic Grid Stress Index (GSI)**: Real-time 0-100 score based on load, frequency, temperature, and renewables.
- ✅ **6-Tier Priority Allocation**: Intelligent slot assignment (Emergency → Opportunistic).
- ✅ **Adaptive Throttling**: Smooth power transitions (150kW → 3.7kW) to prevent grid blackouts.
- ✅ **Automated V2G (Vehicle-to-Grid)**: Fully automated discharge during Red GSI (>75) with real-time compensation accumulation.
- ✅ **3D Interactive Dashboard**: Live visual feedback of the grid "core" and charging sessions.
- ✅ **Stateful Simulator**: Built-in background simulation of EV fleets and grid scenarios.

---

## 🏗️ Project Architecture

```
Astroid_destroyrs/
├── backend/                    # FastAPI High-Performance Backend
│   ├── app/
│   │   ├── core/              # Optimization Algorithms (GSI, SAE, V2G)
│   │   ├── api/               # Real-time REST Endpoints
│   │   └── state.py           # Stateful Background Simulator
├── frontend/                   # React + Three.js Dashboard
│   ├── src/
│   │   ├── App.js             # Main UI Logic
│   │   └── index.css          # Premium Glassmorphic Design
├── docker/                     # Containerization
│   ├── Dockerfile.api         # Python 3.11-slim
│   └── Dockerfile.frontend    # Node.js 20 + Vite
└── docker-compose.yml          # Full-Stack Orchestration
```

---

## ⚡ Quick Start

### 1. Launch the Stack
```bash
docker compose up --build
```

### 2. Access the System
- **Dashboard**: [http://localhost:3000](http://localhost:3000)
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧠 Core Intelligence

### GSI Engine (Grid Stress Index)
The system computes a weighted index to determine charging policy:
`GSI = 0.40×(Load%) + 0.30×(Freq Dev) + 0.20×(Transformer Temp) - 0.10×(Renewable%)`

| GSI Range | Status | Power Policy |
|-----------|--------|--------------|
| 0–30     | 🟢 Green | Unrestricted Fast Charging (150kW) |
| 31–55    | 🟡 Yellow | Standard Charging (22kW) |
| 56–75    | 🟠 Orange | Throttled Charging (7.4kW) |
| 76–100   | 🔴 Red | V2G Active; Emergency Only (3.7kW) |

### SAE (Slot Allocation Engine)
Prioritizes vehicles based on tier, SoC urgency, and renewable availability:
- **P0 Emergency**: Never deferred; priority access.
- **P1 Critical**: SoC < 10%; prioritized recovery.
- **P2-P4 Public/Fleet**: Balanced based on departure time.
- **P5 Opportunistic**: Flexible; chargers only when GSI is Green.

### V2G (Vehicle-to-Grid) Discharge
- **Automation**: Triggers automatically when GSI > 75.
- **Eligibility**: SoC > 60% and >15 min to departure.
- **Reward**: ₹2.5/kWh accumulated in real-time on the dashboard.

---

## 📊 Dashboard Features

- **3D Grid Core**: Interactive visualization that reacts to grid stress (turns red/vibrates under load).
- **Live Metric Bars**: Real-time tracking of Frequency, Temperature, and Renewable mix.
- **Manual Stress Injection**: Test system resilience by triggering "Peak Stress" or "Transformer Failure" buttons.
- **Session Tracking**: Monitor every EV's power level and priority status live.

---

## 🏆 Innovation Highlights

1. **Power Recovery Logic**: Unlike basic systems, GridCharge allows power to "ramp back up" to fast-charging once grid stress subsides.
2. **Automated Queueing**: Advanced heapq-based queueing ensures high-priority vehicles jump to the front of the line.
3. **Glassmorphic UI**: Premium, dark-mode dashboard designed for industrial NOC (Network Operations Center) environments.
4. **Resilient Scaling**: Built with a singleton state pattern in Python, ready for horizontal scaling behind a load balancer.

---

## 🧪 Development & Testing

Run backend logic tests:
```bash
pytest backend/tests/ -v
```

---

**Built for the Future of Energy.** 🔋🌍
