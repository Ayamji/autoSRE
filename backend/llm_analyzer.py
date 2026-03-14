import os
import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class IncidentAnalysis(BaseModel):
    incident: str = Field(description="Short description or name of the incident.")
    severity: str = Field(description="Severity level (e.g., Low, Medium, High, Critical).")
    root_cause: str = Field(description="Detailed explanation of the root cause.")
    recommended_action: str = Field(description="Specific recommended remediation action, like 'restart container api'.")

def get_llm_client():
    if not genai:
        logger.error("google-genai package not installed.")
        return None
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY or API_KEY not set in environment.")
        return None
    return genai.Client(api_key=api_key)

def analyze_with_llm(metrics: dict, logs: List[str]) -> Optional[Dict]:
    """Analyzes system metrics and logs to determine incidents and root causes."""
    client = get_llm_client()
    if not client:
        return None

    prompt = f"""You are an expert Site Reliability Engineer responsible for diagnosing production infrastructure failures.

Analyze the following system metrics and logs.

Determine:
1. If there is an incident
2. The severity level
3. The root cause
4. The recommended remediation action

Metrics:
{json.dumps(metrics, indent=2)}

Logs:
{chr(10).join(logs)}

Return your response in JSON format matching the schema exactly.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=IncidentAnalysis,
                temperature=0.2
            ),
        )
        # GenAI SDK with response_schema automatically parses to the Pydantic type
        # Or we can just read the text and parse it if parsed is not supported by this version
        if hasattr(response, 'parsed') and response.parsed:
            return response.parsed.model_dump()
        else:
            return json.loads(response.text)
    except Exception as e:
        logger.error(f"LLM Analysis failed: {e}")
        return None

def map_action_to_intent(recommended_action: str, default_target: str = "faulty-service") -> Dict:
    """
    Translates raw text actions from the LLM into OpenClaw compatible intents.
    """
    action_lower = recommended_action.lower()
    
    # Example mapping logic
    if "restart container" in action_lower or "restart" in action_lower:
        # Try to extract the target container name from the text
        target = default_target
        words = action_lower.split()
        if "container" in words:
            idx = words.index("container")
            if idx + 1 < len(words):
                target = words[idx + 1]
                
        return {
            "action": "docker_restart",
            "target": target
        }
    elif "scale" in action_lower:
        # Fallback to shell command for scaling
        return {
            "action": "shell",
            "command": "echo 'Scaling action not yet supported out-of-the-box by OpenClaw docker mapper'"
        }
    
    # Fallback default
    return {
        "action": "shell",
        "command": f"echo 'Unmapped action: {recommended_action}'"
    }
