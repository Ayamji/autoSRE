import asyncio
import json
import logging
from typing import Dict
import sys
import os

# Append project root to path so automation module can be imported
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from automation.openclaw_agent import execute_action
except ImportError:
    logging.warning("Could not import OpenClaw agent directly.")
    
    # Mock execute_action if needed
    def execute_action(action_payload):
        return {"success": True, "output": f"Mock executed {action_payload}"}

logger = logging.getLogger(__name__)

async def remediate_incident(incident: Dict) -> Dict:
    """Invokes OpenClaw to perform the suggested remediation for an incident."""
    
    action_type = incident.get("suggested_action")
    target = incident.get("target")
    
    if not action_type:
        return {"success": False, "output": "No suggested action provided."}
        
    payload = {
        "action": action_type,
    }
    if target: payload["target"] = target
    if "command" in incident: payload["command"] = incident["command"]
    
    logger.info(f"Triggering OpenClaw remediation: {payload}")
    
    # Normally this would be a network call or direct function call
    # We call our OpenClaw agent
    try:
        # Run in threadpool to avoid blocking event loop
        result = await asyncio.to_thread(execute_action, payload)
        
        return {
            "success": result.get("success", False),
            "output": result.get("output", "Unknown output from OpenClaw"),
            "action_performed": payload
        }
    except Exception as e:
        logger.error(f"Remediation failed: {e}")
        return {
            "success": False,
            "output": str(e)
        }
