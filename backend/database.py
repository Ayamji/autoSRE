from sqlalchemy import create_engine, Column, String, Integer, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Use SQLite for simplicity and zero-config in this local demo
# Can be easily changed to Postgres by updating this URL
DATABASE_URL = "sqlite:///./autosre.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class IncidentModel(Base):
    __tablename__ = "incidents"

    id = Column(String, primary_key=True, index=True)
    type = Column(String)
    severity = Column(String)
    status = Column(String) # active, remediating, recovered, failed, pending_approval
    root_cause = Column(Text)
    executive_summary = Column(Text)
    internal_reasoning = Column(Text)
    explanation = Column(Text)
    suggested_action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    log_evidence = Column(Text)
    causal_chain = Column(JSON) # Stores the list of events
    intent = Column(JSON) # Stores action, target, command
    
    # Simulation fields
    simulation_result = Column(JSON)
    risk_score = Column(Integer)
    risk_level = Column(String)
    automation_recommended = Column(Boolean)
    
    # Relationship to remediation events
    remediations = relationship("RemediationModel", back_populates="incident")

class RemediationModel(Base):
    __tablename__ = "remediations"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String, ForeignKey("incidents.id"))
    action_taken = Column(String)
    success = Column(Boolean)
    output = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)

    incident = relationship("IncidentModel", back_populates="remediations")

class MemoryEntryModel(Base):
    __tablename__ = "ai_memory"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String, index=True)
    root_cause = Column(Text)
    action_taken = Column(String)
    target = Column(String)
    success = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON) # Flexible extra data
    
    # Simulation fields
    simulation_result = Column(JSON)
    risk_score = Column(Integer)
    risk_level = Column(String)
    automation_recommended = Column(Boolean)

# Initializing database
def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
