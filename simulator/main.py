"""
FastAPI main application
GridCharge: Grid Stress-Aware EV Charging Slot Allocation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import health, charging, grid, v2g


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 GridCharge API starting...")
    yield
    print("✅ GridCharge API shutdown")


app = FastAPI(
    title="GridCharge API",
    description="Grid Stress-Aware EV Charging Slot Allocation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS — allow all origins for dev/demo
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
    return {
        "service": "GridCharge API",
        "version": "1.0.0",
        "status": "🟢 Online",
        "docs": "/docs"
    }


@app.get("/health")
async def health_simple():
    """Simple health check for Docker healthcheck"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)