"""
FastAPI main application
GridCharge: Grid Stress-Aware EV Charging Slot Allocation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import health, charging, grid, v2g
from app.core.gsi_engine import GSIEngine
from app.core.slot_allocator import SlotAllocator
from app.core.v2g_manager import V2GManager


# Global state
gsi_engine = GSIEngine()
slot_allocator = SlotAllocator()
v2g_manager = V2GManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    print("🚀 GridCharge API starting...")
    yield
    print("✅ GridCharge API shutdown")


app = FastAPI(
    title="GridCharge API",
    description="Grid Stress-Aware EV Charging Slot Allocation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(charging.router, prefix="/api/charging", tags=["charging"])
app.include_router(grid.router, prefix="/api/grid", tags=["grid"])
app.include_router(v2g.router, prefix="/api/v2g", tags=["v2g"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "GridCharge API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
