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
    executive_summary: str = Field(description="A 1-sentence punchy summary for the operator.")
    root_cause: str = Field(description="Detailed technical explanation of what broke and why.")
    internal_reasoning: str = Field(description="Internal step-by-step logic used by the AI to connect the data sources.")
    recommended_action: str = Field(description="Specific remediation action, e.g. 'restart container faulty-service'.")
    causal_chain: list = Field(
        default=[],
        description="Ordered list of 3-6 short events showing how the incident unfolded, e.g. ['High request volume detected', 'API latency increased', 'Health check timeouts', 'Service marked unhealthy']. Max 8 words per step."
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

def analyze_with_llm(
    metrics: dict,
    logs: list,
    traces: list = [],
    deployment_history: list = [],
    config_changes: list = []
) -> dict | None:
    """Analyzes all available system context to determine incidents and root causes."""
    client = get_llm_client()
    if not client:
        return None

    memories = get_relevant_memories(limit=4)
    memory_context = format_memories_for_prompt(memories)

    # Format each data source block for the prompt
    trace_context = "No distributed tracing data available." if not traces else "\n".join(traces)

    deploy_context = "No deployment history available."
    if deployment_history:
        lines = []
        for d in deployment_history:
            line = f"  • {d.get('service','?')} | image: {d.get('image','?')} | deployed: {d.get('deployed','?')} | status: {d.get('status','?')}"
            if d.get('change'):
                line += f" | change: {d['change']}"
            lines.append(line)
        deploy_context = "\n".join(lines)

    config_context = "No configuration change data available."
    if config_changes:
        lines = []
        for c in config_changes:
            flag = "⚠️ FLAGGED" if c.get('flagged') else "INFO"
            line = f"  • [{flag}] {c.get('service','?')} | {c.get('variable','?')} | reason: {c.get('reason','N/A')}"
            if c.get('timestamp'):
                line += f" | at {c['timestamp']}"
            lines.append(line)
        config_context = "\n".join(lines)

    prompt = f"""You are an expert Site Reliability Engineer (SRE) diagnosing a live production failure.

--- AI MEMORY BANK (Past Successful Resolutions) ---
{memory_context}

--- TASK ---
Analyze ALL of the following 5 data sources and determine:
1. Whether a real incident is occurring
2. Severity (Low / Medium / High / Critical)
3. Root cause — explicitly name the failing service, endpoint, or config
4. One specific, executable remediation action (e.g. 'restart container faulty-service')
5. A causal chain of 3-6 short steps showing exactly how the incident unfolded

Note: Some data sources may be absent. Use what is available and your SRE expertise to fill any gaps.
If no clear incident is found, return incident as 'No incident detected' and severity 'Low'.

--- DATA SOURCE 1: SYSTEM METRICS ---
Contains real-time CPU, memory, latency, and error rate values.
{json.dumps(metrics, indent=2)}

--- DATA SOURCE 2: APPLICATION LOGS ---
Contains recent log lines from all running microservices.
{chr(10).join(logs) if logs else 'No logs available.'}

--- DATA SOURCE 3: DISTRIBUTED TRACES (OpenTelemetry / Jaeger) ---
Contains the service call graph with per-span durations and error flags.
{trace_context}

--- DATA SOURCE 4: DEPLOYMENT HISTORY ---
Contains recent container image updates and runtime changes. A bad deploy often causes incidents.
{deploy_context}

--- DATA SOURCE 5: CONFIGURATION CHANGES ---
Contains flagged environment variable changes that may have introduced instability.
{config_context}

--- HOW WE PROVIDE REMEDIES WITHOUT FULL DATA ---
Even if some sources are missing, the AutoSRE system provides remedies via:
  1. AI World Knowledge – LLMs trained on SRE bodies of knowledge can infer root causes from partial signals.
  2. AI Memory Bank – Historical successful resolutions are retrieved from our SQLite DB and included above.
  3. Rule-Based Heuristics – If LLM is unavailable, the system uses hardcoded pattern rules (e.g. OOMKilled → restart, CPU>80% → scale).
  4. Dependency Graph Analysis – Failing downstream services indicate which upstream service to target.
  5. Simulation Engine – Before executing, the system scores risk and escalates to human if confidence is low.

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
