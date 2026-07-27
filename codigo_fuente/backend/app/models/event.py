from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.sql import func
import uuid
from app.db import Base

class Event(Base):
    __tablename__ = "eventos"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    source_platform = Column(String(50), nullable=False)
    source_id = Column(String(100), nullable=False)
    source_url = Column(Text)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    venue_name = Column(String(255))
    address = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    city = Column(String(100), nullable=False)
    tags = Column(JSON, default=list)
    raw_data = Column(JSON)
    is_tech = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Subscription(Base):
    __tablename__ = "suscripciones"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    preference_channel = Column(String(50), default="email")
    city = Column(String(100), default="Buenos Aires")
    latitude = Column(Float)
    longitude = Column(Float)
    radius_km = Column(Float, default=15.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class IACache(Base):
    __tablename__ = "cache_ia"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key = Column(String(255), unique=True, nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
