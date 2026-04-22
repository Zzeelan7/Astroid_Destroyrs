# Project Report: GridCharge Smart EV Charging System

## 1. Project Overview
GridCharge is a state-of-the-art, grid-stress-aware EV charging orchestration platform. It solves the "Peak Demand Problem" by dynamically balancing electric vehicle charging loads against real-time power grid health. The system utilizes a multi-objective optimization engine to ensure that emergency vehicles are always charged while residential and commercial loads are managed to prevent transformer failures and grid blackouts.

## 2. System Architecture
The project follows a modern microservices architecture, fully containerized for scalable deployment.

- **Backend (FastAPI)**: High-performance Python core handling optimization logic, state management, and real-time data streaming.
- **Frontend (React + Three.js)**: A premium, glassmorphic dashboard featuring interactive 3D visualizations and real-time telemetry updates.
- **Infrastructure**:
    - **PostgreSQL**: Persistent storage for session history and user profiles.
    - **Redis**: Low-latency caching for real-time grid metrics.
    - **Mosquitto (MQTT)**: IoT communication layer for future hardware integration.

## 3. Core Functional Modules

### 3.1 GSI Engine (Grid Stress Index)
The heart of the system is the **Grid Stress Index (GSI)**, a composite score (0-100) calculated from four key telemetry streams:
1.  **Grid Load (40%)**: Current utilization of transformer capacity.
2.  **Frequency Deviation (30%)**: Stability of the 50Hz/60Hz AC signal.
3.  **Transformer Temperature (20%)**: Thermal health of local distribution assets.
4.  **Renewable Penetration (-10%)**: Availability of green energy (offsets stress).

### 3.2 SAE (Slot Allocation Engine)
The SAE manages access to physical charging ports using a **6-Tier Priority System**:
- **P0 (Emergency)**: Zero deferral; immediate allocation at max available power.
- **P1 (Critical Battery)**: Urgency-based allocation for vehicles with <10% SoC.
- **P2-P4 (Public/Fleet)**: Managed based on departure deadlines and grid headroom.
- **P5 (Opportunistic)**: Charges only when renewables are high or GSI is "Green".

**Innovation**: The engine supports **Adaptive Power Throttling**, which allows sessions to recover from low-power modes (3.7kW) back to fast-charging (150kW) automatically as grid conditions improve.

### 3.3 V2G Manager (Vehicle-to-Grid)
GridCharge goes beyond load reduction by actively supporting **Grid Injection**.
- **Automated Response**: During "Red" stress events (GSI > 75), V2G-capable vehicles automatically stop charging and start discharging power into the grid.
- **Compensation Model**: Participants are rewarded at a rate of ₹2.5/kWh, tracked in real-time on the dashboard.

## 4. Key Improvements & Bug Fixes
During development, the following critical enhancements were made:
- **Queue Deadlock Fix**: Resolved an issue where vehicles remained in the queue even after slots were freed.
- **Power Ramp-Up Implementation**: Refactored the throttling logic to allow sessions to regain power after a stress event.
- **V2G Automation**: Closed the loop on grid injection, making it fully reactive to GSI scores.
- **3D Visualization**: Integrated a Three.js "Grid Core" that provides immediate visual context of grid health.

## 5. Verification & Testing
The system has been validated through:
- **Unit Tests**: Coverage for GSI calculations, Priority scoring, and V2G eligibility.
- **Scenario Simulation**: Verified resilience under "Peak Stress" and "Transformer Failure" modes.
- **UI/UX Audit**: Confirmed responsiveness and real-time metric accuracy on the React dashboard.

## 6. Conclusion
GridCharge represents a production-ready approach to the future of the electric grid. By combining real-time telemetry with priority-based orchestration and V2G flexibility, it ensures grid stability without compromising user experience.

---
**Prepared by**: Antigravity (AI Coding Assistant)
**Date**: April 2026
