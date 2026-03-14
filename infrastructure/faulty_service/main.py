import time
import random
import sys
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Faulty Microservice")

# State
# 0 = normal
# 1 = database outage
# 2 = OOM loop
# 3 = container crash (sys.exit)
current_state = 0

@app.get("/health")
def health_check():
    global current_state
    
    if current_state == 0:
        if random.random() < 0.05:
            # 5% chance of spontaneous failure
            current_state = random.choice([1, 2, 3])
            
    if current_state == 1:
        # DB failure - timeout or connection refused
        logger.error("database connection refused. Connection to tcp://postgres:5432 failed.")
        raise HTTPException(status_code=500, detail="database connection refused")
        
    elif current_state == 2:
        # Memory exhaustion / CPU hog
        logger.warning("CPU throttling detected. High cpu usage.")
        logger.error("memory exhaustion detected. OOMKilled imminent.")
        # We can't actually OOM easily without killing ourselves, so we simulate it via logs and 503
        raise HTTPException(status_code=503, detail="Service Unavailable: High Load")
        
    elif current_state == 3:
        logger.critical("service unavailable, container crashed. CrashLoopBackOff")
        sys.exit(1) # actually crash
        
    return {"status": "ok"}

@app.post("/trigger_failure/{state_id}")
def trigger_failure(state_id: int):
    global current_state
    current_state = state_id
    if current_state == 3:
        logger.critical("service unavailable, container crashed. CrashLoopBackOff")
        sys.exit(1)
    return {"status": "state updated", "new_state": current_state}

@app.get("/metrics")
def metrics():
    """Dummy endpoint for prometheus to scrape so the target exists"""
    count = random.randint(10, 100)
    lines = [
        "# HELP faulty_service_requests_total Total number of requests",
        "# TYPE faulty_service_requests_total counter",
        f"faulty_service_requests_total {count}"
    ]
    return Response("\n".join(lines) + "\n", media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
