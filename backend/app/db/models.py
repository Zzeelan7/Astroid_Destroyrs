from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from .database import Base

class ChargingSession(Base):
    __tablename__ = "charging_sessions"

    id = Column(String, primary_key=True, index=True) # vehicle_id + timestamp or just vehicle_id
    vehicle_id = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    energy_kwh = Column(Float, default=0.0)
    peak_power_kw = Column(Float, default=0.0)
    is_v2g = Column(Boolean, default=False)
    priority = Column(Integer, default=4)
    status = Column(String, default="active")

class V2GSession(Base):
    __tablename__ = "v2g_sessions"

    id = Column(String, primary_key=True, index=True) # vehicle_id + timestamp
    vehicle_id = Column(String, index=True)
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    energy_discharged_kwh = Column(Float, default=0.0)
    compensation_earned_inr = Column(Float, default=0.0)
    status = Column(String, default="discharging")
