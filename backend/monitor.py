import time
import threading
import logging
import random
import configparser
from prometheus_client import Gauge, start_http_server
import requests
import os

import psutil
import subprocess

logger = logging.getLogger(__name__)

# Prometheus metrics
sre_cpu_percent = Gauge('sre_cpu_percent', 'Simulated CPU usage percentage')
sre_memory_percent = Gauge('sre_memory_percent', 'Simulated Memory usage percentage')
sre_service_up = Gauge('sre_service_up', 'Is the faulty service up? 1 for yes, 0 for no')

# State
current_cpu = 0.0
current_mem = 0.0
is_service_up = True
running_containers = 0
total_containers = 1 # at least itself

LOG_FILE = "../logs/sample_logs.txt"

def append_log(msg: str):
    """Appends a synthetic log line to the local log file for the analyzer to pick up."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")

def monitor_loop():
    global current_cpu, current_mem, is_service_up, running_containers, total_containers
    
    while True:
        try:
            # 1. Get real System Metrics
            current_cpu = psutil.cpu_percent(interval=None)
            current_mem = psutil.virtual_memory().percent
            
            # 2. Query Docker for container counts
            try:
                # Use docker cli since it's already installed in Dockerfile
                cmd = "docker ps -a --format '{{.Status}}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    total_containers = len(lines) if lines[0] != '' else 0
                    running_containers = len([line for line in lines if "Up" in line])
            except Exception as e:
                logger.error(f"Failed to query docker: {e}")

            # 3. Ping faulty service
            url = os.environ.get("FAULTY_SERVICE_URL", "http://faulty-service:8080/health")
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    sre_service_up.set(1)
                    is_service_up = True
                else:
                    sre_service_up.set(0)
                    is_service_up = False
                    append_log(f"ERROR [faulty-service] Health check failed with status {resp.status_code}")
            except requests.exceptions.RequestException:
                sre_service_up.set(0)
                is_service_up = False
                # only log if it was previously up to avoid log spam
                # append_log("ERROR [faulty-service] Connection refused.")
            
            sre_cpu_percent.set(current_cpu)
            sre_memory_percent.set(current_mem)
            
        except Exception as e:
            logger.error(f"Monitor loop error: {e}")
            
        time.sleep(5)

def start_monitor():
    """Starts the un-managed monitoring thread. Prometheus exporter goes on 8001 by default, but FastAPI will expose it too."""
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()
    logger.info("Monitoring thread started.")

def get_stats():
    """Returns the current real-time stats."""
    return {
        "cpu": current_cpu,
        "mem": current_mem,
        "running_containers": running_containers,
        "total_containers": total_containers,
        "service_up": is_service_up
    }
