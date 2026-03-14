"""
context_generators.py
Generates rich, realistic context data for AutoSRE's AI analysis engine.
Each function simulates a real production data source and returns structured data.
"""

import os
import random
import logging
import subprocess
from datetime import datetime, timezone, timedelta
import requests

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# 1. LOG GENERATOR
# Strategy: Read from the real log file. If absent, generate synthetic logs.
# --------------------------------------------------------------------------

LOG_FILE = "../logs/sample_logs.txt"
LOG_TEMPLATES = [
    "[{svc}] INFO  - Request to /{endpoint} processed in {latency}ms",
    "[{svc}] WARN  - Response latency {latency}ms exceeds SLO threshold of 200ms",
    "[{svc}] ERROR - Health check failed with status {code}",
    "[{svc}] ERROR - Connection to {dep} timed out after 5000ms",
    "[{svc}] FATAL - OOMKilled: container exceeded memory limit (512Mi)",
    "[{svc}] INFO  - Container started successfully (pid={pid})",
    "[{svc}] ERROR - CrashLoopBackOff: process exited with code 137",
    "[{svc}] WARN  - CPU throttling detected: usage at {cpu}%",
    "[{svc}] ERROR - ECONNREFUSED connecting to database:5432",
    "[{svc}] INFO  - Serving request [GET /{endpoint}] -> 200 OK in {latency}ms",
]

SERVICES = ["faulty-service", "order-backend", "shop-frontend", "autosre-backend"]

def generate_logs(limit: int = 15) -> list:
    """Returns the most recent log lines from disk, or generates synthetic ones."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                return lines[-limit:]
        except Exception as e:
            logger.warning(f"Could not read log file: {e}")

    now = datetime.now(timezone.utc)
    logs = []
    for i in range(limit):
        ts = (now - timedelta(seconds=(limit - i) * 4)).strftime("%Y-%m-%dT%H:%M:%SZ")
        svc = random.choice(SERVICES)
        dep = random.choice([s for s in SERVICES if s != svc])
        template = random.choice(LOG_TEMPLATES)
        line = template.format(
            svc=svc, endpoint=random.choice(["health", "order", "products", "checkout"]),
            latency=random.randint(50, 5000), code=random.choice([200, 500, 503, 429]),
            dep=dep, pid=random.randint(1000, 9999), cpu=random.randint(75, 99)
        )
        logs.append(f"[{ts}] {line}")
    return logs


# --------------------------------------------------------------------------
# 2. METRICS GENERATOR
# Strategy: Pull real Docker stats first; fall back to synthesized values.
# --------------------------------------------------------------------------

def generate_metrics() -> dict:
    """Returns live container metrics from Docker, or estimated values."""
    metrics = {
        "containers": {},
        "host_cpu_percent": round(random.uniform(10, 90), 1),
        "host_memory_percent": round(random.uniform(20, 80), 1),
        "request_rate_per_sec": round(random.uniform(1, 50), 1),
        "error_rate_percent": round(random.uniform(0, 25), 1),
        "p50_latency_ms": random.randint(20, 120),
        "p95_latency_ms": random.randint(150, 600),
        "p99_latency_ms": random.randint(300, 2000),
    }

    try:
        result = subprocess.run(
            ["docker", "stats", "--no-stream", "--format", "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split(",")
            if len(parts) == 4:
                name, cpu, mem, mem_pct = parts
                metrics["containers"][name.strip()] = {
                    "cpu": cpu.strip(),
                    "memory_usage": mem.strip(),
                    "memory_percent": mem_pct.strip()
                }
    except Exception as e:
        logger.warning(f"Docker stats unavailable: {e}. Using synthetic metrics.")
        for svc in SERVICES:
            metrics["containers"][svc] = {
                "cpu": f"{round(random.uniform(0.2, 90), 1)}%",
                "memory_usage": f"{random.randint(64, 450)}MiB / 512MiB",
                "memory_percent": f"{round(random.uniform(10, 95), 1)}%"
            }
    return metrics


# --------------------------------------------------------------------------
# 3. DISTRIBUTED TRACES GENERATOR
# Strategy: Query Jaeger API for real spans; generate synthetic trace on failure.
# --------------------------------------------------------------------------

JAEGER_URL = "http://jaeger:16686/api/traces"

def generate_traces(service: str = "faulty-service", limit: int = 3) -> list:
    """Returns formatted distributed trace spans from Jaeger or synthetic fallback."""
    trace_lines = []
    try:
        resp = requests.get(f"{JAEGER_URL}?service={service}&limit={limit}", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            for trace in data.get("data", []):
                processes = trace.get("processes", {})
                spans = sorted(trace.get("spans", []), key=lambda x: x["startTime"])
                for s in spans:
                    svc = processes.get(s.get("processID"), {}).get("serviceName", "unknown")
                    op = s.get("operationName", "")
                    dur = s.get("duration", 0)
                    tags = s.get("tags", [])
                    error = any(t.get("key") == "error" and t.get("value") is True for t in tags)
                    status = "❌ ERROR" if error else "✅ OK"
                    trace_lines.append(f"  [{svc}] {op} → {status} ({dur}µs)")
        if trace_lines:
            return trace_lines
    except Exception as e:
        logger.warning(f"Jaeger unavailable: {e}. Generating synthetic traces.")

    # Synthetic fallback trace
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    trace_lines = [
        f"  [shop-frontend] GET /order → ✅ OK (12ms) @ {now}",
        f"  [order-backend] POST /process → ✅ OK (87ms) @ {now}",
        f"  [faulty-service] GET /health → ❌ ERROR (5002ms - timeout) @ {now}",
        f"  [order-backend] Upstream faulty-service unreachable → connection refused",
        f"  [shop-frontend] Request to order-backend failed → 503 Service Unavailable",
    ]
    return trace_lines


# --------------------------------------------------------------------------
# 4. DEPLOYMENT HISTORY GENERATOR
# Strategy: Read Docker image tags and running container metadata.
# --------------------------------------------------------------------------

def generate_deployment_history() -> list:
    """Returns recent container deployment events from Docker labels or simulated timestamps."""
    deployments = []
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}\t{{.Image}}\t{{.RunningFor}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) == 4:
                name, image, running, status = parts
                deployments.append({
                    "service": name,
                    "image": image,
                    "deployed": running + " ago",
                    "status": status
                })
    except Exception as e:
        logger.warning(f"Docker ps unavailable: {e}. Generating synthetic deployment history.")

    if not deployments:
        now = datetime.now(timezone.utc)
        deployments = [
            {
                "service": "faulty-service",
                "image": "autosre/faulty-service:latest",
                "deployed": (now - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "unhealthy",
                "change": "Memory limit reduced from 512Mi to 256Mi by ops team"
            },
            {
                "service": "order-backend",
                "image": "autosre/order-backend:v2.1.3",
                "deployed": (now - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "running",
                "change": "Updated order processing timeout from 5000ms to 2000ms"
            },
            {
                "service": "shop-frontend",
                "image": "autosre/shop-frontend:v1.4.1",
                "deployed": (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "status": "running",
                "change": "Deployed with new traffic burst feature"
            }
        ]
    return deployments


# --------------------------------------------------------------------------
# 5. CONFIGURATION CHANGES GENERATOR
# Strategy: Read Docker env vars from running containers; highlight suspicious changes.
# --------------------------------------------------------------------------

CRITICAL_ENV_KEYS = [
    "MEMORY_LIMIT", "CPU_LIMIT", "DB_HOST", "DB_PORT",
    "TIMEOUT", "MAX_CONNECTIONS", "LOG_LEVEL", "RETRY_COUNT"
]

def generate_config_changes() -> list:
    """Returns suspicious or recent environment configuration changes."""
    changes = []
    try:
        result = subprocess.run(
            ["docker", "ps", "-q"],
            capture_output=True, text=True, timeout=5
        )
        container_ids = result.stdout.strip().splitlines()
        for cid in container_ids[:5]:
            inspect = subprocess.run(
                ["docker", "inspect", "--format",
                 "{{.Name}} {{range .Config.Env}}{{.}} {{end}}",
                 cid],
                capture_output=True, text=True, timeout=5
            )
            line = inspect.stdout.strip()
            if line:
                parts = line.split(" ", 1)
                name = parts[0].lstrip("/")
                env_str = parts[1] if len(parts) > 1 else ""
                for env_var in env_str.split():
                    for key in CRITICAL_ENV_KEYS:
                        if key in env_var.upper():
                            changes.append({
                                "service": name,
                                "variable": env_var,
                                "flagged": True,
                                "reason": f"Critical configuration key '{key}' detected"
                            })
    except Exception as e:
        logger.warning(f"Docker inspect unavailable: {e}. Using synthetic config changes.")

    if not changes:
        now = datetime.now(timezone.utc)
        changes = [
            {
                "service": "faulty-service",
                "variable": "MEMORY_LIMIT=256Mi",
                "flagged": True,
                "timestamp": (now - timedelta(hours=2, minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reason": "Memory limit halved from 512Mi — may cause OOMKilled events under load"
            },
            {
                "service": "order-backend",
                "variable": "TIMEOUT=2000",
                "flagged": True,
                "timestamp": (now - timedelta(hours=4, minutes=50)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reason": "Timeout reduced from 5000ms — may cause upstream cascading failures"
            },
            {
                "service": "shop-frontend",
                "variable": "LOG_LEVEL=DEBUG",
                "flagged": False,
                "timestamp": (now - timedelta(days=1, hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "reason": "Non-critical: verbose logging enabled (may increase I/O)"
            }
        ]
    return changes
