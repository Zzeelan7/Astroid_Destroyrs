"""
FastAPI main application
GridCharge: Grid Stress-Aware EV Charging Slot Allocation
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, charging, grid, v2g
from .state import simulator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: launch background simulation tasks. Shutdown: cancel them."""
    print("[*] GridCharge API starting — launching background simulators...")
    grid_task = asyncio.create_task(simulator.run(),        name="grid_sim")
    ev_task   = asyncio.create_task(simulator.run_auto_ev(), name="ev_sim")
    yield
    grid_task.cancel()
    ev_task.cancel()
    try:
        await asyncio.gather(grid_task, ev_task, return_exceptions=True)
    except Exception:
        pass
    print("[*] GridCharge API shutdown")


app = FastAPI(
    title="GridCharge API",
    description="Grid Stress-Aware EV Charging Slot Allocation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,   prefix="/api/health",   tags=["health"])
app.include_router(charging.router, prefix="/api/charging", tags=["charging"])
app.include_router(grid.router,     prefix="/api/grid",     tags=["grid"])
app.include_router(v2g.router,      prefix="/api/v2g",      tags=["v2g"])


@app.get("/")
async def root():
    return {
        "service": "GridCharge API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)