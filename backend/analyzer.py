import os
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime

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

# In-memory store of incidents
active_incidents = {}

def analyze_logs(log_file_path: str = "../logs/sample_logs.txt") -> List[Dict]:
    """Reads logs and runs pattern matching to identify incidents."""
    detected = []
    
    if not os.path.exists(log_file_path):
        return detected

    with open(log_file_path, "r") as f:
        lines = f.readlines()
        
    for line in lines[-50:]:  # Check last 50 lines to keep it bounded
        line = line.strip()
        if not line:
            continue
            
        for rule in RULES:
            # Simple rule logic: if any pattern matches the line
            if any(pattern.lower() in line.lower() for pattern in rule["pattern"]):
                # AI Agent reasoning generation mock
                incident = {
                    "id": f"inc-{uuid.uuid4().hex[:6]}",
                    "type": rule["type"],
                    "severity": rule["severity"],
                    "root_cause": rule["root_cause"],
                    "explanation": rule["explanation"],
                    "suggested_action": rule["suggested_action"],
                    "target": rule.get("target"),
                    "command": rule.get("command"),
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "status": "active",
                    "log_evidence": line
                }
                
                # Deduplication logic: avoid creating multiple active incidents of the same type
                if not any(i['type'] == incident['type'] and i['status'] in ['active', 'remediating'] for i in active_incidents.values()):
                    active_incidents[incident['id']] = incident
                    detected.append(incident)
                    
    return detected

def get_active_incidents():
    return [i for i in active_incidents.values() if i['status'] in ['active', 'remediating']]

def get_all_incidents():
    return list(active_incidents.values())

def update_incident_status(incident_id: str, status: str, action_taken: str = None):
    if incident_id in active_incidents:
        active_incidents[incident_id]['status'] = status
        if action_taken:
            active_incidents[incident_id]['action_taken'] = action_taken
        return True
    return False
