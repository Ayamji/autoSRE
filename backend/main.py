from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import asyncio
import logging
from typing import List

from dotenv import load_dotenv
load_dotenv()

from analyzer import analyze_logs, get_active_incidents, get_all_incidents, update_incident_status, active_incidents
from monitor import start_monitor, get_stats
from remediation import remediate_incident
from report import generate_json_report, generate_pdf_report
from llm_analyzer import analyze_with_llm, map_action_to_intent
import uuid
from datetime import datetime
import os

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

# Start background monitoring thread
@app.on_event("startup")
async def startup_event():
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

@app.get("/incidents")
async def get_incidents():
    return {"incidents": get_active_incidents()}

@app.get("/ai-analyze")
async def trigger_ai_analysis():
    """Trigger LLM log analysis and return newly discovered incidents."""
    metrics_data = get_stats()
    
    logs = []
    if os.path.exists("../logs/sample_logs.txt"):
        with open("../logs/sample_logs.txt", "r") as f:
            lines = f.readlines()
            # Only send the latest logs to the LLM
            logs = [line.strip() for line in lines[-50:] if line.strip()]
            
    analysis = analyze_with_llm(metrics_data, logs)
    if not analysis:
        # Fallback to rule-based if LLM fails or not configured
        new_incidents = analyze_logs()
        return {"analyzed": False, "error": "LLM failed", "fallback_incidents": new_incidents}
        
    intent = map_action_to_intent(analysis.get("recommended_action", ""))
    
    incident_id = f"inc-{uuid.uuid4().hex[:6]}"
    
    approval_mode = os.environ.get("APPROVAL_MODE", "false").lower() == "true"
    initial_status = "pending_approval" if approval_mode else "active"
    
    incident = {
        "id": incident_id,
        "type": analysis.get("incident", "Unknown"),
        "severity": analysis.get("severity", "Unknown"),
        "root_cause": analysis.get("root_cause", "Unknown"),
        "suggested_action": analysis.get("recommended_action", ""),
        "intent": intent,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": initial_status,
        "log_evidence": "\n".join(logs[-3:]) if logs else ""
    }
    
    active_incidents[incident_id] = incident
    
    logger.info(f"Analyzed metrics/logs with LLM. Incident: {incident['type']}")
    await broadcast_event("new_incident", incident)
        
    return {"analyzed": True, "incident": incident, "all_active": get_active_incidents()}

from pydantic import BaseModel
class RemediateRequest(BaseModel):
    incident_id: str
    approved: bool = True

@app.post("/remediate")
async def remediate(req: RemediateRequest):
    incident = active_incidents.get(req.incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident["status"] == "pending_approval":
        if not req.approved:
            return {"status": "skipped", "message": "Remediation was not approved."}
        # If approved, move to active to allow remediation
        update_incident_status(req.incident_id, "active")
        
    if incident["status"] != "active":
        return {"status": "skipped", "message": "Incident is already remediating or recovered."}

    update_incident_status(req.incident_id, "remediating")
    await broadcast_event("incident_update", {"id": req.incident_id, "status": "remediating"})
    
    # Run remediation using OpenClaw logic
    if "intent" in incident:
        incident["suggested_action"] = incident["intent"].get("action")
        incident["target"] = incident["intent"].get("target")
        incident["command"] = incident["intent"].get("command")
        
    result = await remediate_incident(incident)
    
    if result.get("success"):
        update_incident_status(req.incident_id, "recovered", action_taken=incident.get("suggested_action"))
        await broadcast_event("incident_update", {"id": req.incident_id, "status": "recovered"})
        
        # Give system a moment to recover and write logs
        return {"status": "success", "result": result}
    else:
        update_incident_status(req.incident_id, "failed")
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
async def get_report(incident_id: str, format: str = "json"):
    incident = active_incidents.get(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
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
