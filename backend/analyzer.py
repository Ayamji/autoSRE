from datetime import datetime
from typing import List, Dict, Optional
from database import SessionLocal, IncidentModel
from sqlalchemy.orm import Session

# Rules for simplistic rule-based detection
RULES = [
    {
        "pattern": ["OOMKilled", "memory exhaustion", "Out of memory"],
        "type": "MemoryExhaustion",
        "severity": "Critical",
        "root_cause": "A container exceeded its memory limit and was terminated by the OOM killer.",
        "explanation": "Memory limits were breached, causing the host OS to forcibly kill the process to reclaim RAM.",
        "suggested_action": "docker_restart",
        "target": "faulty-service"
    },
    {
        "pattern": ["connection refused", "ECONNREFUSED", "timeout", "database connection refused"],
        "type": "DatabaseTimeout",
        "severity": "High",
        "root_cause": "The application is unable to establish a connection to the database layer within the expected timeframe.",
        "explanation": "Metrics indicate high latency or complete failure when connecting to Postgres DB port 5432.",
        "suggested_action": "docker_restart",
        "target": "autosre-db"
    },
    {
        "pattern": ["CrashLoopBackOff", "container crashed", "service unavailable"],
        "type": "ContainerCrash",
        "severity": "Critical",
        "root_cause": "The service process exited abruptly and is failing to stay running upon restart.",
        "explanation": "A critical exception was thrown without being caught, causing app termination.",
        "suggested_action": "docker_restart",
        "target": "faulty-service"
    },
    {
        "pattern": ["CPU throttling", "high cpu"],
        "type": "HighCPU",
        "severity": "Medium",
        "root_cause": "CPU requests are maxing out limits, leading to throttling by the orchestrator.",
        "explanation": "Intensive computation or a stuck loop is consuming all allocated CPU cycles.",
        "suggested_action": "shell",
        "command": "echo 'Scaling up CPU limits...'"
    }
]

# Helper to get DB session
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

def analyze_logs(log_file_path: str = "../logs/sample_logs.txt", db: Session = None) -> List[Dict]:
    """Reads logs and runs pattern matching to identify incidents."""
    import os
    import uuid
    
    detected = []
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True
        
    try:
        if not os.path.exists(log_file_path):
            return detected

        with open(log_file_path, "r") as f:
            lines = f.readlines()
            
        for line in lines[-50:]:
            line = line.strip()
            if not line:
                continue
                
            for rule in RULES:
                if any(pattern.lower() in line.lower() for pattern in rule["pattern"]):
                    # Check for existing active/remediating incident of same type in DB
                    exists = db.query(IncidentModel).filter(
                        IncidentModel.type == rule["type"],
                        IncidentModel.status.in_(["active", "remediating"])
                    ).first()
                    
                    if not exists:
                        incident_id = f"inc-{uuid.uuid4().hex[:6]}"
                        new_incident = IncidentModel(
                            id=incident_id,
                            type=rule["type"],
                            severity=rule["severity"],
                            root_cause=rule["root_cause"],
                            explanation=rule["explanation"],
                            suggested_action=rule["suggested_action"],
                            status="active",
                            log_evidence=line,
                            intent={"action": rule["suggested_action"], "target": rule.get("target")}
                        )
                        db.add(new_incident)
                        db.commit()
                        db.refresh(new_incident)
                        
                        # Convert to dict for compatibility
                        incident_dict = {
                            "id": new_incident.id,
                            "type": new_incident.type,
                            "severity": new_incident.severity,
                            "root_cause": new_incident.root_cause,
                            "explanation": new_incident.explanation,
                            "suggested_action": new_incident.suggested_action,
                            "status": new_incident.status,
                            "timestamp": new_incident.timestamp.isoformat() + "Z",
                            "log_evidence": new_incident.log_evidence,
                            "intent": new_incident.intent
                        }
                        detected.append(incident_dict)
    finally:
        if own_db:
            db.close()
                        
    return detected

def get_active_incidents(db: Session = None):
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True
    try:
        incidents = db.query(IncidentModel).filter(
            IncidentModel.status.in_(["active", "remediating", "pending_approval"])
        ).all()
        return [
            {
                "id": i.id,
                "type": i.type,
                "severity": i.severity,
                "root_cause": i.root_cause,
                "explanation": i.explanation,
                "suggested_action": i.suggested_action,
                "status": i.status,
                "timestamp": i.timestamp.isoformat() + "Z",
                "log_evidence": i.log_evidence,
                "intent": i.intent,
                "causal_chain": i.causal_chain,
                "simulation_result": i.simulation_result,
                "risk_score": i.risk_score,
                "risk_level": i.risk_level,
                "automation_recommended": i.automation_recommended
            } for i in incidents
        ]
    finally:
        if own_db:
            db.close()

def get_all_incidents(db: Session = None):
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True
    try:
        incidents = db.query(IncidentModel).order_by(IncidentModel.timestamp.desc()).all()
        return [
            {
                "id": i.id,
                "type": i.type,
                "severity": i.severity,
                "status": i.status,
                "timestamp": i.timestamp.isoformat() + "Z"
            } for i in incidents
        ]
    finally:
        if own_db:
            db.close()

def update_incident_status(incident_id: str, status: str, action_taken: str = None, db: Session = None):
    own_db = False
    if db is None:
        db = SessionLocal()
        own_db = True
    try:
        incident = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
        if incident:
            incident.status = status
            db.commit()
            return True
        return False
    finally:
        if own_db:
            db.close()
