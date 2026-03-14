"""
AutoSRE Memory Layer
Stores past incident resolutions as a persistent knowledge base.
The AI queries this before analyzing new incidents to leverage past fixes.
"""
import json
import os
import logging
from datetime import datetime
from database import get_db, MemoryEntryModel

logger = logging.getLogger(__name__)

def record_resolution(incident: dict, success: bool):
    """Called after remediation to persist the outcome in the database."""
    try:
        db = next(get_db())
        
        details = {
            "causal_chain": incident.get("causal_chain", []),
            "suggested_action": incident.get("suggested_action", ""),
            "severity": incident.get("severity", "Unknown")
        }
        
        entry = MemoryEntryModel(
            incident_type=incident.get("type", "Unknown"),
            root_cause=incident.get("root_cause", "Unknown"),
            action_taken=incident.get("intent", {}).get("action", ""),
            target=incident.get("intent", {}).get("target", ""),
            success=success,
            details=details
        )
        
        db.add(entry)
        db.commit()
        logger.info(f"Memory DB: recorded resolution for '{entry.incident_type}' (success={success})")
    except Exception as e:
        logger.error(f"Failed to record resolution to Memory DB: {e}")

def get_relevant_memories(incident_type: str = "", limit: int = 5) -> list:
    """Fetch past resolved incidents relevant to the current one."""
    try:
        db = next(get_db())
        # Filter to successful resolutions, ordered by recent
        records = db.query(MemoryEntryModel).filter(MemoryEntryModel.success == True).order_by(MemoryEntryModel.timestamp.desc()).all()
        
        successful = []
        for r in records:
            details = r.details or {}
            successful.append({
                "timestamp": r.timestamp.isoformat() + "Z",
                "incident_type": r.incident_type,
                "root_cause": r.root_cause,
                "action_taken": r.action_taken,
                "target": r.target,
                "suggested_action": details.get("suggested_action", ""),
                "success": r.success,
                "causal_chain": details.get("causal_chain", []),
                "severity": details.get("severity", "Unknown")
            })

        # Score by relevance (simple word overlap)
        def relevance(r):
            keywords = set(incident_type.lower().split())
            type_words = set(r.get("incident_type", "").lower().split())
            return len(keywords & type_words)

        if incident_type:
            successful.sort(key=relevance, reverse=True)

        return successful[:limit]
    except Exception as e:
        logger.error(f"Failed to fetch memories from DB: {e}")
        return []

def format_memories_for_prompt(memories: list) -> str:
    if not memories:
        return "No prior resolutions found."
    lines = []
    for m in memories:
        lines.append(
            f"- Incident: {m['incident_type']} | "
            f"Root cause: {m['root_cause'][:80]} | "
            f"Fix: {m['suggested_action']} → target={m['target']} (successful)"
        )
    return "\n".join(lines)
