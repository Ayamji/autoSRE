"""
AutoSRE Memory Layer
Stores past incident resolutions as a persistent knowledge base.
The AI queries this before analyzing new incidents to leverage past fixes.
"""
import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "incident_memory.json")

def _load_memory() -> list:
    if not os.path.exists(MEMORY_FILE):
        return []
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load memory: {e}")
        return []

def _save_memory(records: list):
    try:
        with open(MEMORY_FILE, "w") as f:
            json.dump(records, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save memory: {e}")

def record_resolution(incident: dict, success: bool):
    """Called after remediation to persist the outcome."""
    records = _load_memory()
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "incident_type": incident.get("type", "Unknown"),
        "severity": incident.get("severity", "Unknown"),
        "root_cause": incident.get("root_cause", "Unknown"),
        "action_taken": incident.get("intent", {}).get("action", ""),
        "target": incident.get("intent", {}).get("target", ""),
        "suggested_action": incident.get("suggested_action", ""),
        "success": success,
        "causal_chain": incident.get("causal_chain", []),
    }
    records.append(entry)
    # Keep only 50 most recent
    records = records[-50:]
    _save_memory(records)
    logger.info(f"Memory: recorded resolution for '{entry['incident_type']}' (success={success})")

def get_relevant_memories(incident_type: str = "", limit: int = 5) -> list:
    """Fetch past resolved incidents relevant to the current one."""
    records = _load_memory()
    # Filter to successful resolutions, sort recent first
    successful = [r for r in records if r.get("success")]
    successful.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

    # Score by relevance (simple word overlap)
    def relevance(r):
        keywords = set(incident_type.lower().split())
        type_words = set(r.get("incident_type", "").lower().split())
        return len(keywords & type_words)

    if incident_type:
        successful.sort(key=relevance, reverse=True)

    return successful[:limit]

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
