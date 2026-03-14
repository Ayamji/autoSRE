import os
import json
import logging
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

try:
    from memory import get_relevant_memories, format_memories_for_prompt
except ImportError:
    def get_relevant_memories(*a, **kw): return []
    def format_memories_for_prompt(m): return "Memory module not available."

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

logger = logging.getLogger(__name__)

class IncidentAnalysis(BaseModel):
    incident: str = Field(description="Short name/description of the incident.")
    severity: str = Field(description="Severity level: Low, Medium, High, or Critical.")
    root_cause: str = Field(description="Detailed explanation of the root cause.")
    recommended_action: str = Field(description="Specific remediation action, e.g. 'restart container faulty-service'.")
    causal_chain: list = Field(
        default=[],
        description="Ordered list of 3-6 short events showing how the incident unfolded, e.g. ['High request volume detected', 'API latency increased', 'Health check timeouts', 'Service marked unhealthy']. Each step should be short (max 8 words)."
    )

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

    memories = get_relevant_memories(limit=4)
    memory_context = format_memories_for_prompt(memories)

    prompt = f"""You are an expert Site Reliability Engineer responsible for diagnosing production infrastructure failures.

You have a memory of past incidents and their successful resolutions:

{memory_context}

Analyze the following system metrics and logs.

Determine:
1. If there is an incident
2. The severity level
3. The root cause
4. The recommended remediation action (be very specific — name the exact container or service to target, e.g. 'restart container faulty-service')
5. A causal chain of 3-6 short steps showing how the incident unfolded

Metrics:
{json.dumps(metrics, indent=2)}

Logs:
{chr(10).join(logs)}

Return your response in JSON format matching the schema exactly.
"""
    MODELS_TO_TRY = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
    last_error = None
    for model in MODELS_TO_TRY:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=IncidentAnalysis,
                    temperature=0.2
                ),
            )
            logger.info(f"LLM response from model: {model}")
            if hasattr(response, 'parsed') and response.parsed:
                return response.parsed.model_dump()
            else:
                return json.loads(response.text)
        except Exception as e:
            last_error = e
            logger.warning(f"Model {model} failed: {e}. Trying next model...")
            continue
    logger.error(f"All LLM models failed. Last error: {last_error}")
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
        else:
            # Fallback for "restart faulty-service" or "restart the service"
            idx = words.index("restart") if "restart" in words else -1
            # Search forward for the first word that isn't a stopword
            stopwords = ["the", "to", "a", "an", "and", "in", "on", "fix", "resolve"]
            for i in range(idx + 1, len(words)):
                word = words[i].strip('.,!?"\'')
                if word and word not in stopwords:
                    # Check if it resembles a known container
                    if "api" in word or "backend" in word:
                        target = "autosre-backend"
                    elif "grafana" in word:
                        target = "grafana"
                    elif "faulty" in word or "service" in word:
                        target = "faulty-service"
                    else:
                        target = word
                    break
                    
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
