from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import asyncio
import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

from database import init_db, get_db, IncidentModel, RemediationModel, MemoryEntryModel
from sqlalchemy.orm import Session
from fastapi import Depends

from analyzer import analyze_logs, get_active_incidents, get_all_incidents, update_incident_status
from monitor import start_monitor, get_stats
from remediation import remediate_incident
from report import generate_json_report, generate_pdf_report
from llm_analyzer import analyze_with_llm, map_action_to_intent
try:
    from memory import record_resolution
except ImportError:
    def record_resolution(*a, **kw): pass
from topology import get_topology
try:
    from dependency_graph import build_service_graph
    from simulation_engine import simulate_remediation
except ImportError:
    pass
try:
    from context_generators import (
        generate_logs, generate_metrics, generate_traces,
        generate_deployment_history, generate_config_changes
    )
except ImportError:
    def generate_logs(**kw): return []
    def generate_metrics(): return {}
    def generate_traces(**kw): return []
    def generate_deployment_history(): return []
    def generate_config_changes(): return []
import uuid
import os
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AutoSRE Backend", version="1.0.0")

@app.get("/metrics")
async def metrics():
    return get_stats()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB and monitoring on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    start_monitor()

# WebSocket for real-time dashboard updates
connections: List[WebSocket] = []

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            # just keep connection alive, we push from backend loop or routes
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)

async def broadcast_event(event_type: str, payload: dict):
    message = {"event": event_type, "payload": payload}
    for connection in connections:
        try:
            await connection.send_json(message)
        except Exception:
            pass

@app.get("/data-sources")
async def get_data_sources():
    """Returns all 5 raw context data sources used to power the AI analysis engine."""
    return {
        "logs":               generate_logs(limit=20),
        "metrics":            generate_metrics(),
        "traces":             generate_traces(service="faulty-service", limit=3),
        "deployment_history": generate_deployment_history(),
        "config_changes":     generate_config_changes(),
        "fallback_chain": [
            "1. AI LLM World Knowledge — Infers root causes from best-practice SRE patterns",
            "2. AI Memory Bank       — Queries past successful remediations from SQLite DB",
            "3. Rule-Based Heuristics — Pattern matches logs: OOMKilled→restart, CPU>80%→scale",
            "4. Dependency Graph     — Identifies failing upstream service from trace call graph",
            "5. Simulation Engine    — Scores remediation risk; escalates to human if HIGH"
        ]
    }

@app.get("/incidents")
async def get_incidents_route(db: Session = Depends(get_db)):
    return {"incidents": get_active_incidents(db)}

@app.get("/topology")
async def get_system_topology():
    return get_topology()

@app.get("/history")
async def get_history(db: Session = Depends(get_db)):
    incidents = db.query(IncidentModel).order_by(IncidentModel.timestamp.desc()).limit(20).all()
    return {"history": [
        {
            "id": i.id,
            "type": i.type,
            "severity": i.severity,
            "status": i.status,
            "timestamp": i.timestamp.isoformat() + "Z",
            "root_cause": i.root_cause
        } for i in incidents
    ]}

@app.get("/memory-bank")
async def get_memory_bank(db: Session = Depends(get_db)):
    entries = db.query(MemoryEntryModel).order_by(MemoryEntryModel.timestamp.desc()).all()
    return {"memory": [
        {
            "id": e.id,
            "type": e.incident_type,
            "cause": e.root_cause,
            "fix": e.action_taken,
            "success": e.success,
            "time": e.timestamp.isoformat() + "Z"
        } for e in entries
    ]}

@app.get("/ai-analyze")
async def trigger_ai_analysis():
    """Trigger LLM log analysis with all 5 context data sources."""
    # Collect all context data from generators
    metrics_data = generate_metrics()
    logs        = generate_logs(limit=50)
    traces      = generate_traces(service="faulty-service", limit=3)
    deployments = generate_deployment_history()
    configs     = generate_config_changes()
    
    # Fall back to legacy monitor stats for additional signal
    try:
        live_stats = get_stats()
        metrics_data.update({k: v for k, v in live_stats.items() if k not in metrics_data})
    except Exception:
        pass
            
    analysis = analyze_with_llm(
        metrics=metrics_data,
        logs=logs,
        traces=traces,
        deployment_history=deployments,
        config_changes=configs
    )
    if not analysis:
        # LLM failed (quota/timeout) — create a rule-based incident from logs and metrics
        logger.warning("LLM unavailable, falling back to rule-based analysis.")
        service_up = metrics_data.get("service_up", True)
        cpu = metrics_data.get("cpu", 0)
        
        if not service_up:
            incident_type = "Faulty-service health check failure"
            severity = "High"
            root_cause = "Faulty-service is not responding to health checks. It may be in a failed state (DB outage, OOM, or crash)."
            action = "restart container faulty-service"
            chain = ["Normal traffic flowing", "Health check failure detected", "Service returning non-200", "Incident triggered"]
        elif cpu > 80:
            incident_type = "High CPU Usage"
            severity = "Medium"
            root_cause = f"System CPU is at {cpu:.1f}%, causing service degradation."
            action = "restart container autosre-backend"
            chain = ["Load increased", "CPU saturation detected", "Response times degraded", "Incident triggered"]
        elif logs:
            incident_type = "Log anomaly detected"
            severity = "Medium"
            root_cause = f"Recent log: {logs[-1]}" if logs else "Unexpected log entries found."
            action = "restart container faulty-service"
            chain = ["Anomaly in logs", "Service health degraded", "Incident triggered"]
        else:
            return {"analyzed": False, "error": "LLM unavailable and no anomalies detected."}

        analysis = {
            "incident": incident_type,
            "severity": severity,
            "root_cause": root_cause,
            "recommended_action": action,
            "causal_chain": chain,
        }
        
    intent = map_action_to_intent(analysis.get("recommended_action", ""))
    
    # Run the What-If Simulation Engine
    try:
        service_graph = build_service_graph("shop-frontend")
        simulation_res = simulate_remediation(intent, traces, service_graph)
    except Exception as e:
        logger.error(f"Simulation engine failed: {e}")
        simulation_res = {
            "predicted_downtime": "Unknown",
            "affected_services": [],
            "risk_score": 50,
            "risk_level": "UNKNOWN",
            "recommendation": "MANUAL REVIEW RECOMMENDED",
            "automation_recommended": False
        }
    
    incident_id = f"inc-{uuid.uuid4().hex[:6]}"
    
    # Automatic approval routing based on simulation + environment
    approval_mode = os.environ.get("APPROVAL_MODE", "false").lower() == "true"
    initial_status = "active"
    if approval_mode or not simulation_res.get("automation_recommended", False):
        initial_status = "pending_approval"
    
    incident_data = {
        "id": incident_id,
        "type": analysis.get("incident", "Unknown"),
        "severity": analysis.get("severity", "Unknown"),
        "root_cause": analysis.get("root_cause", "Unknown"),
        "suggested_action": analysis.get("recommended_action", ""),
        "causal_chain": analysis.get("causal_chain", []),
        "intent": intent,
        "status": initial_status,
        "log_evidence": "\n".join(logs[-3:]) if logs else "",
        "simulation_result": simulation_res,
        "risk_score": simulation_res.get("risk_score", 0),
        "risk_level": simulation_res.get("risk_level", "UNKNOWN"),
        "automation_recommended": simulation_res.get("automation_recommended", False)
    }
    
    # Save to DB
    db = next(get_db())
    new_inc = IncidentModel(**incident_data)
    db.add(new_inc)
    db.commit()
    db.refresh(new_inc)
    
    # Convert for response
    incident = incident_data
    incident["timestamp"] = new_inc.timestamp.isoformat() + "Z"

    logger.info(f"Analyzed metrics/logs with LLM. Incident: {incident['type']}")
    await broadcast_event("new_incident", incident)
        
    return {"analyzed": True, "incident": incident, "all_active": get_active_incidents(db)}

from pydantic import BaseModel
class RemediateRequest(BaseModel):
    incident_id: str
    approved: bool = True

@app.post("/remediate")
async def remediate(req: RemediateRequest, db: Session = Depends(get_db)):
    incident_record = db.query(IncidentModel).filter(IncidentModel.id == req.incident_id).first()
    if not incident_record:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Manual dict conversion for compatibility with existing remediation.py
    incident = {
        "id": incident_record.id,
        "status": incident_record.status,
        "suggested_action": incident_record.suggested_action,
        "intent": incident_record.intent
    }

    if incident["status"] == "pending_approval":
        if not req.approved:
            return {"status": "skipped", "message": "Remediation was not approved."}
        update_incident_status(req.incident_id, "active", db=db)
        incident["status"] = "active"
        
    if incident["status"] != "active":
        return {"status": "skipped", "message": "Incident is already remediating or recovered."}

    update_incident_status(req.incident_id, "remediating", db=db)
    await broadcast_event("incident_update", {"id": req.incident_id, "status": "remediating"})
    
    if incident.get("intent"):
        incident["suggested_action"] = incident["intent"].get("action")
        incident["target"] = incident["intent"].get("target")
        incident["command"] = incident["intent"].get("command")
        
    result = await remediate_incident(incident)
    
    if result.get("success"):
        update_incident_status(req.incident_id, "recovered", db=db)
        record_resolution(incident, success=True)
        # Deep persistence: Save remediation log
        rem = RemediationModel(incident_id=req.incident_id, action_taken=incident.get("suggested_action"), success=True, output=result.get("output"))
        db.add(rem)
        db.commit()
        
        await broadcast_event("incident_update", {"id": req.incident_id, "status": "recovered"})
        await broadcast_event("system_recovered", {"message": "All clear – system has recovered."})
        return {"status": "success", "result": result}
    else:
        update_incident_status(req.incident_id, "failed", db=db)
        record_resolution(incident, success=False)
        rem = RemediationModel(incident_id=req.incident_id, action_taken=incident.get("suggested_action"), success=False, output=result.get("output"))
        db.add(rem)
        db.commit()
        
        await broadcast_event("incident_update", {"id": req.incident_id, "status": "failed"})
        return {"status": "failed", "result": result}

@app.get("/report")
async def get_latest_report(format: str = "json"):
    active = get_active_incidents()
    if not active:
        all_inc = get_all_incidents()
        if not all_inc:
            raise HTTPException(status_code=404, detail="No incidents found")
        incident = all_inc[-1]
    else:
        incident = active[-1]
    return await get_report(incident["id"], format)

@app.get("/report/{incident_id}")
async def get_report(incident_id: str, format: str = "json", db: Session = Depends(get_db)):
    incident_rec = db.query(IncidentModel).filter(IncidentModel.id == incident_id).first()
    if not incident_rec:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Convert to dict for legacy report generators
    incident = {
        "id": incident_rec.id,
        "type": incident_rec.type,
        "severity": incident_rec.severity,
        "root_cause": incident_rec.root_cause,
        "timestamp": incident_rec.timestamp.isoformat() + "Z",
        "log_evidence": incident_rec.log_evidence,
        "simulation_result": incident_rec.simulation_result,
        "risk_level": incident_rec.risk_level
    }
    
    if format == "pdf":
        pdf_bytes = generate_pdf_report(incident)
        return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=report_{incident_id}.pdf"})
    else:
        return generate_json_report(incident)

@app.get("/prometheus")
async def prometheus_metrics():
    """Endpoint for Prometheus scraping."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
