"""
context_generators.py
Generates rich, realistic context data for AutoSRE's AI analysis engine.
Each function simulates a real production data source and returns structured data.
"""

import os
import time
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

# ── 9 distinct failure scenario log banks ────────────────────────────────────
# Each bank generates a unique cluster of logs that the LLM can identify distinctly.
SCENARIO_LOG_BANKS = {
    "db_refused": [
        "FATAL [order-backend] database connection refused. Connection to tcp://postgres:5432 refused after 3 retries",
        "ERROR [order-backend] ECONNREFUSED 10.0.0.5:5432 — PostgreSQL not reachable",
        "ERROR [faulty-service] DB health probe failed: connection reset by peer on port 5432",
        "ERROR [order-backend] SQLAlchemy pool exhausted: max_overflow=10 connections exceeded",
        "WARN  [shop-frontend] Checkout failed — downstream DB unavailable: returning cached data",
        "ERROR [order-backend] Transaction rollback: could not serialize access due to concurrent update",
        "ERROR [faulty-service] Health check failed with status 500 — root cause: postgres:5432",
    ],
    "oom_killed": [
        "WARN  [faulty-service] RSS memory usage at 498MiB / 512MiB — OOM kill threshold approaching",
        "FATAL [faulty-service] OOMKilled: container exceeded memory limit (512Mi) — killed by kernel",
        "ERROR [faulty-service] memory exhaustion detected. Out of memory: process 2341 killed",
        "WARN  [order-backend] Heap usage at 92% — GC pressure causing latency spikes",
        "ERROR [faulty-service] malloc: Cannot allocate memory — RSS 512MiB exceeded Linux limit",
        "ERROR [k8s-node] OOM event: faulty-service killed, Reason: OOMKilled, Exit code: 137",
        "WARN  [autosre-backend] Downstream faulty-service returned 503 — likely due to OOM restart",
    ],
    "crash_loop": [
        "FATAL [faulty-service] Unhandled exception: NullPointerException at handler.py:142",
        "CRITICAL [faulty-service] CrashLoopBackOff — service restarted 5 times in last 120s",
        "ERROR [faulty-service] Process exited with code 137 (SIGKILL) — Container crashed",
        "ERROR [faulty-service] service unavailable, container crashed. Restart policy: always",
        "WARN  [shop-frontend] /api/checkout returned 503 — faulty-service backend unreachable",
        "ERROR [faulty-service] RuntimeError: division by zero in order_processor.py line 87",
    ],
    "rate_limit": [
        "WARN  [api-gateway] Rate limit triggered for client 10.2.1.50 — 429 Too Many Requests",
        "ERROR [shop-frontend] HTTP 429 from order-backend — retry after 60s backoff",
        "WARN  [order-backend] Upstream rate limiter active — request queue depth: 1024/1024",
        "ERROR [faulty-service] Backpressure: shedding load — current RPS 3200 exceeds limit 2500",
        "WARN  [shop-frontend] Cart service returning 429 — exponential backoff at 15s",
        "ERROR [api-gateway] Circuit breaker OPEN for faulty-service — rate limit exceeded 3x",
    ],
    "cert_expiry": [
        "ERROR [faulty-service] SSL handshake failed: x509: certificate has expired or is not yet valid",
        "ERROR [order-backend] TLS certificate for api.internal:443 expired on 2026-02-28T00:00:00Z",
        "FATAL [shop-frontend] HTTPS connection failed: peer certificate cannot be authenticated",
        "ERROR [faulty-service] curl: (60) SSL certificate problem: certificate has expired",
        "WARN  [autosre-backend] Certificate renewal webhook failed — cert-manager pod not responding",
        "ERROR [order-backend] mTLS client cert verification failed — handshake aborted",
    ],
    "disk_full": [
        "FATAL [faulty-service] IOError: [Errno 28] No space left on device — /var/log/app.log write failed",
        "CRITICAL [node] Disk full: /dev/sda1 usage at 100% (32.0 GiB / 32.0 GiB) — log rotation stalled",
        "ERROR [faulty-service] Database WAL log overflow: pg_wal directory exceeded 8GB limit",
        "ERROR [order-backend] JournalD: no space available — skipping log entry",
        "WARN  [autosre-backend] Tmp directory /tmp/uploads at 98% — uploads may fail",
        "ERROR [faulty-service] Container /overlay2 filesystem full — unable to write checkpoint",
    ],
    "upstream_timeout": [
        "WARN  [shop-frontend] Upstream call to order-backend:8080/process timed out after 5000ms",
        "ERROR [order-backend] CascadingTimeout: faulty-service /compute did not respond in 5s — marking UNHEALTHY",
        "ERROR [shop-frontend] HTTP 504 Gateway Timeout — 3 consecutive upstream failures to order-backend",
        "WARN  [order-backend] Retry attempt 3/3 to faulty-service — all attempts timed out",
        "ERROR [api-gateway] Upstream connection pool exhausted for route /api/orders — 504 served",
        "ERROR [faulty-service] Background worker stalled: upstream dependency unreachable for 90s",
    ],
    "auth_failure": [
        "ERROR [faulty-service] JWT signature verification failed — invalid token issuer: expected 'autosre-auth'",
        "WARN  [order-backend] HTTP 401 Unauthorized from identity-service:9000 — token may have been rotated",
        "ERROR [shop-frontend] OAuth2 access_token expired — refresh failed: identity service returned 500",
        "ERROR [order-backend] RBAC denial: user 'svc-order' lacks permission 'db:write' on resource 'orders'",
        "WARN  [api-gateway] API key revoked for client_id=a38fb2c1 — all requests blocked",
        "ERROR [faulty-service] mTLS: client certificate CN=faulty revoked by CA — connection rejected",
    ],
    "thread_pool": [
        "CRITICAL [faulty-service] ThreadPoolExhausted — all 64 executor threads busy, rejecting new tasks",
        "ERROR [order-backend] Connection pool drained: max_connections=100 on postgres:5432 — new requests blocked",
        "WARN  [faulty-service] Async worker queue depth 2048/2048 — producer blocked on queue.put()",
        "ERROR [shop-frontend] Service mesh sidecar: upstream concurrency limit (50) exceeded for faulty-service",
        "ERROR [faulty-service] goroutine count: 4096 — likely goroutine leak detected",
        "WARN  [order-backend] HTTP connection pool at 95% capacity — latency increasing (p99: 4500ms)",
    ],
}

SERVICES = ["faulty-service", "order-backend", "shop-frontend", "autosre-backend"]

def _pick_scenario() -> str:
    """Picks a random scenario with high entropy so back-to-back analyses are unique."""
    scenarios = list(SCENARIO_LOG_BANKS.keys())
    # Use time and random for maximum variety
    return random.choice(scenarios)

def generate_logs(limit: int = 15) -> list:
    """Returns real log lines from disk, or produces scenario-specific synthetic logs."""
    import time as _time
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if lines:
                    return lines[-limit:]
        except Exception as e:
            logger.warning(f"Could not read log file: {e}")

    now = datetime.now(timezone.utc)
    scenario = _pick_scenario()
    bank = SCENARIO_LOG_BANKS[scenario]

    logs = []
    for i in range(min(limit, len(bank) + 3)):
        ts = (now - timedelta(seconds=(limit - i) * 8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = bank[i % len(bank)]
        # add some healthy noise at the start
        if i < 2:
            svc = random.choice(SERVICES)
            ep = random.choice(["health", "order", "products", "checkout"])
            line = f"INFO  [{svc}] GET /{ep} → 200 OK in {random.randint(8, 90)}ms"
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
        "host_cpu_percent": round(random.uniform(5, 95), 1),
        "host_memory_percent": round(random.uniform(10, 90), 1),
        "request_rate_per_sec": round(random.uniform(5, 200), 1), # Wider RPS range
        "error_rate_percent": round(random.uniform(0, 40), 1),
        "p50_latency_ms": random.randint(10, 300),
        "p95_latency_ms": random.randint(200, 1200),
        "p99_latency_ms": random.randint(500, 5000),
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
