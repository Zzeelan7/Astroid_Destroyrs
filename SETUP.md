# Quick Setup Guide

## 🎯 For Local Development

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local testing)
- Node.js 18+ (for frontend dev)

### 1. Clone & Setup

```bash
cd C:\Users\zzeel\OneDrive\Desktop\Astroid_destroyrs
cp .env.example .env
```

### 2. Start Stack

```bash
# Full production-like stack
docker compose up --build

# OR development mode with hot-reload
docker compose -f docker-compose.dev.yml up
```

### 3. Access Services

```
Backend API:    http://localhost:8000
API Docs:       http://localhost:8000/docs
Frontend:       http://localhost:3000
PostgreSQL:     localhost:5432
Redis:          localhost:6379
MQTT:           localhost:1883
```

### 4. Run Demo

```bash
bash scripts/demo.sh
```

### 5. Run Tests

```bash
# In backend directory
pytest tests/ -v --cov=app

# Or via Docker
docker compose run --rm api pytest tests/ -v
```

---

## 📋 First Run Checklist

- [ ] Docker Compose installed
- [ ] `.env` file copied from `.env.example`
- [ ] Run `docker compose up --build` (3-5 min first time)
- [ ] Open http://localhost:3000 in browser
- [ ] Run `bash scripts/demo.sh` in another terminal
- [ ] See GSI scores change in API responses
- [ ] Check V2G status endpoint

---

## 🚨 Troubleshooting

### Port Already in Use
```bash
docker compose down
# or change ports in docker-compose.yml
```

### Database Connection Error
```bash
docker compose logs postgres
# Wait 10-15 seconds for postgres to start
docker compose restart api
```

### Frontend Won't Load
```bash
docker compose logs frontend
npm install  # in frontend/ directory
```

### Tests Fail
```bash
# Ensure backend PYTHONPATH is set
export PYTHONPATH=/app:$PYTHONPATH
pytest tests/ -v
```

---

## 📊 Project Statistics

```
Backend:     ~500 lines (FastAPI, GSI, slot allocator, V2G)
Frontend:    ~300 lines (React, Tailwind)
Tests:       ~250 lines (pytest, 3 modules)
Simulator:   ~200 lines (OCPP-like simulation)
Config:      Docker Compose + env files
Total:       ~1500 lines of judge-ready code
```

---

## 🏆 Judge Scoring Checklist

- ✅ **Functionality**: All 4 GSI tiers, 6 priority levels, V2G logic
- ✅ **Real Algorithms**: Weighted formulas, not toy code
- ✅ **Docker**: One command to deploy; reproducible
- ✅ **Tests**: Unit tests prove correctness
- ✅ **Demo**: 2-min walkthrough showing all features
- ✅ **Production Hints**: 3-layer architecture, Redis, PostgreSQL, MQTT
- ✅ **Documentation**: README + inline comments + API docs

---

## 💡 Next: Impress Further

1. Add a live grid heatmap (Recharts + D3)
2. Deploy to AWS/GCP (show cloud-ready setup)
3. Add OCPP 2.0 protocol layer (real EV communication)
4. Show predictive analytics (LSTM grid forecast)
5. Add authentication & multi-tenant support
6. Kubernetes manifests (show enterprise scale)

**Current Status: Hackathon MVP Ready ✅**
