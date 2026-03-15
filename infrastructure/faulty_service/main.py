"""
faulty_service/main.py
A realistic chaos simulator with 9 distinct failure modes that rotate automatically.
Each failure emits distinct logs so AutoSRE can identify 9 different incident types.
"""

import time
import random
import sys
import os
import logging
import threading
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response, JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
logger = logging.getLogger("faulty-service")

app = FastAPI(title="Faulty Microservice")

# ─── Failure Modes ─────────────────────────────────────────────────────────────
# 0  = Healthy
# 1  = Database connection refused (TCP 5432)
# 2  = OOMKilled / Memory exhaustion
# 3  = CrashLoopBackOff (actual exit)
# 4  = Rate limit / 429 Too Many Requests
# 5  = SSL / TLS certificate expiry
# 6  = Disk full – no space left on device
# 7  = Cascading upstream timeout (order-backend → faulty-service)
# 8  = Authentication failure / 401 from downstream
# 9  = Thread pool exhaustion / connection pool drained

FAILURE_MODES = {
    0: "Healthy",
    1: "DatabaseConnectionRefused",
    2: "MemoryExhaustion",
    3: "CrashLoopBackOff",
    4: "RateLimitExceeded",
    5: "CertificateExpiry",
    6: "DiskSpaceExhausted",
    7: "CascadingUpstreamTimeout",
    8: "AuthenticationFailure",
    9: "ThreadPoolExhausted",
}

current_state = 0
auto_rotate = True   # auto-cycle through failure modes every N seconds
_rotate_interval = int(os.environ.get("FAILURE_ROTATE_SECS", "60"))  # 60s default


def _emit_failure_log(state: int):
    """Emit once-per-state realistic logs when the error state changes."""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if state == 1:
        logger.error("database connection refused. Connection to tcp://postgres:5432 refused after 3 retries.")
        logger.error("ECONNREFUSED 127.0.0.1:5432 — database pool exhausted")
    elif state == 2:
        logger.warning("RSS memory usage at 498MiB / 512MiB — approaching OOM kill threshold")
        logger.error("memory exhaustion detected. OOMKilled by kernel — signal 9 received")
    elif state == 3:
        logger.critical("Unhandled exception in main thread — RuntimeError: null pointer dereference")
        logger.critical("CrashLoopBackOff: service unavailable, container crashed (exit code 137)")
    elif state == 4:
        logger.warning("Upstream rate limiter triggered — HTTP 429 Too Many Requests from api-gateway")
        logger.warning("Backpressure: request queue at capacity (1024/1024). Shedding load.")
    elif state == 5:
        logger.error("SSL handshake failed: certificate expired on 2026-02-28T00:00:00Z")
        logger.error("TLS certificate validation error for endpoint api.internal:443 — x509: certificate has expired")
    elif state == 6:
        logger.error("IOError: [Errno 28] No space left on device — write to /var/log/app.log failed")
        logger.critical("Disk full: /dev/sda1 usage at 100% (32GB / 32GB). Log rotation stalled.")
    elif state == 7:
        logger.warning("Upstream call to order-backend /process timed out after 5000ms")
        logger.error("CascadingUpstreamTimeout: 3 consecutive timeouts to order-backend:8080 — marking UNHEALTHY")
    elif state == 8:
        logger.error("Authentication failed — JWT signature verification error: invalid token issuer")
        logger.warning("HTTP 401 Unauthorized from identity-service:9000 — token may be rotated or expired")
    elif state == 9:
        logger.error("ThreadPoolExhausted: all 64 executor threads busy — rejecting new tasks")
        logger.critical("Connection pool drained: max_connections=100 reached for postgres:5432 — new requests blocked")


def _auto_rotate_loop():
    """Background thread: cycles through failure modes every _rotate_interval seconds."""
    global current_state
    modes = list(FAILURE_MODES.keys())
    idx = 0
    while True:
        time.sleep(_rotate_interval)
        if not auto_rotate:
            continue
        idx = (idx + 1) % len(modes)
        new_state = modes[idx]
        if new_state != current_state:
            logger.info(f"[AutoRotate] Switching from state {current_state} ({FAILURE_MODES[current_state]}) → {new_state} ({FAILURE_MODES[new_state]})")
            current_state = new_state
            _emit_failure_log(new_state)
            if new_state == 3:
                logger.critical("State 3 triggered — exiting process to simulate crash")
                sys.exit(1)


# Start auto-rotate background thread
_thread = threading.Thread(target=_auto_rotate_loop, daemon=True)
_thread.start()


# ─── API Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
def health_check():
    global current_state

    # 3% chance of spontaneous state change when healthy
    if current_state == 0 and random.random() < 0.03:
        new_state = random.choice([1, 2, 4, 5, 6, 7, 8, 9])
        logger.warning(f"Spontaneous failure injected: state {new_state} ({FAILURE_MODES[new_state]})")
        current_state = new_state
        _emit_failure_log(new_state)

    state = current_state

    if state == 0:
        return {"status": "ok", "mode": "Healthy", "latency_ms": random.randint(5, 20)}

    elif state == 1:
        logger.error("Health check: database connection refused on postgres:5432")
        raise HTTPException(status_code=500, detail="database connection refused")

    elif state == 2:
        mem_used = random.randint(490, 512)
        logger.error(f"Health check: memory exhaustion at {mem_used}MiB/512MiB. OOMKilled imminent.")
        raise HTTPException(status_code=503, detail=f"OOMKilled: {mem_used}MiB/512MiB used")

    elif state == 3:
        logger.critical("Health check: CrashLoopBackOff — container crashed. Exiting.")
        sys.exit(1)

    elif state == 4:
        logger.warning("Health check: rate limit exceeded — HTTP 429 from upstream")
        raise HTTPException(status_code=429, detail="Too Many Requests — rate limit exceeded")

    elif state == 5:
        logger.error("Health check: SSL certificate expired — TLS handshake failed")
        raise HTTPException(status_code=503, detail="SSL certificate expired: x509 validation error")

    elif state == 6:
        logger.error("Health check: disk full — /dev/sda1 at 100% capacity")
        raise HTTPException(status_code=507, detail="Insufficient Storage: disk full")

    elif state == 7:
        delay = random.randint(4500, 6000)
        logger.warning(f"Health check: upstream timeout after {delay}ms — order-backend unreachable")
        raise HTTPException(status_code=504, detail=f"Gateway Timeout: upstream call timed out after {delay}ms")

    elif state == 8:
        logger.error("Health check: authentication failure — JWT invalid or token rotated")
        raise HTTPException(status_code=401, detail="Unauthorized: JWT verification failed")

    elif state == 9:
        logger.error("Health check: thread pool exhausted — all workers busy")
        raise HTTPException(status_code=503, detail="Service Unavailable: thread pool exhausted")

    return {"status": "unknown"}


@app.post("/trigger_failure/{state_id}")
def trigger_failure(state_id: int):
    global current_state
    if state_id not in FAILURE_MODES:
        raise HTTPException(status_code=400, detail=f"Unknown failure state: {state_id}. Valid: {list(FAILURE_MODES.keys())}")
    old_state  = current_state
    current_state = state_id
    _emit_failure_log(state_id)
    if state_id == 3:
        logger.critical("Manual crash triggered")
        sys.exit(1)
    logger.info(f"State manually changed: {old_state} → {state_id} ({FAILURE_MODES[state_id]})")
    return {"status": "state updated", "old_state": old_state, "new_state": state_id, "mode": FAILURE_MODES[state_id]}


@app.post("/reset")
def reset_state():
    global current_state
    old = current_state
    current_state = 0
    logger.info(f"State reset to Healthy from {old} ({FAILURE_MODES.get(old, '?')})")
    return {"status": "reset", "previous_state": old}


@app.get("/state")
def get_state():
    return {"state": current_state, "mode": FAILURE_MODES.get(current_state, "unknown")}


@app.get("/metrics")
def metrics():
    """Prometheus-compatible metrics endpoint."""
    reqs = random.randint(10, 1000)
    errors = random.randint(0, reqs // 4) if current_state != 0 else random.randint(0, 2)
    latency = random.uniform(5, 5000) if current_state != 0 else random.uniform(2, 50)
    lines = [
        "# HELP faulty_service_requests_total Total requests",
        "# TYPE faulty_service_requests_total counter",
        f"faulty_service_requests_total {reqs}",
        "# HELP faulty_service_errors_total Total errors",
        "# TYPE faulty_service_errors_total counter",
        f"faulty_service_errors_total {errors}",
        "# HELP faulty_service_latency_ms Request latency",
        "# TYPE faulty_service_latency_ms gauge",
        f"faulty_service_latency_ms {latency:.1f}",
        f"faulty_service_state {current_state}",
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
