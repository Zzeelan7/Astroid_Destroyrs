"""Health check and maintenance endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db.database import SessionLocal, engine
from ..db.models import Base
from ..state import simulator

router = APIRouter()


@router.get("/")
async def health_check():
    """Service health status"""
    return {
        "status": "🟢 Healthy",
        "service": "GridCharge API",
        "version": "1.0.0"
    }


@router.post("/purge-db")
async def purge_db():
    """Maintenance: Clear all database tables and reset simulation state."""
    # 1. Reset simulator state
    simulator.slot_allocator.active_sessions = {}
    simulator.slot_allocator.queue = []
    simulator.v2g_manager.participants = {}
    simulator.v2g_manager.active_discharge_sessions = {}
    simulator.v2g_manager.total_compensation_paid = 0.0
    
    # 2. Drop and recreate tables (extreme purge)
    # Alternatively, just delete all rows.
    db = SessionLocal()
    try:
        from ..db.models import ChargingSession, V2GSession
        db.query(ChargingSession).delete()
        db.query(V2GSession).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()
        
    return {"status": "purged", "message": "Database and in-memory state cleared."}
