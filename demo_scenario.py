import requests
import time
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger("Demo")

BASE_URL = "http://localhost:8000"

def write_trigger_log():
    log_file = "logs/sample_logs.txt"
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    # We write a fatal database error to trigger an incident
    line = f"[{timestamp}] FATAL [faulty-service] database connection refused, psycopg2.OperationalError. Connection to tcp://postgres:5432 failed.\n"
    with open(log_file, "a") as f:
        f.write(line)
    logger.info("1. Wrote failure log to logs/sample_logs.txt")

def analyze_logs():
    logger.info("2. Triggering AI log analysis...")
    resp = requests.get(f"{BASE_URL}/analyze")
    data = resp.json()
    new_incidents = data.get("new_incidents", [])
    if not new_incidents:
        logger.error("No new incidents detected!")
        return None
        
    incident = new_incidents[0]
    logger.info(f"   -> AI Detected Incident [{incident['id']}]: {incident['type']}")
    logger.info(f"   -> Root Cause: {incident['root_cause']}")
    logger.info(f"   -> Suggested Action: {incident['suggested_action']} on target {incident.get('target')}")
    return incident['id']

def remediate_incident(incident_id):
    logger.info(f"3. Triggering automated remediation for {incident_id}...")
    resp = requests.post(f"{BASE_URL}/remediate", json={"incident_id": incident_id})
    data = resp.json()
    if data.get("status") == "success":
        logger.info(f"   -> Remediation Success! OpenClaw output: {data['result']['output'].strip()}")
    else:
        logger.error(f"   -> Remediation Failed: {data}")

def check_status(incident_id):
    logger.info(f"4. Polling incident status...")
    for _ in range(5):
        resp = requests.get(f"{BASE_URL}/incidents")
        incidents = resp.json().get("incidents", [])
        for inc in incidents:
            if inc['id'] == incident_id:
                logger.info(f"   -> Status is currently: {inc['status']}")
                return inc['status']
        
        # If not active, maybe it is recovered and thus removed from active list?
        # Actually our active list includes remediating but maybe not recovered depending on implementation.
        # Let's check the report endpoint to see if it exists.
        time.sleep(1)
        
    resp = requests.get(f"{BASE_URL}/report/{incident_id}?format=json")
    if resp.status_code == 200:
        status = resp.json().get("status")
        logger.info(f"   -> Final Status: {status}")
        return status
    return "unknown"

def download_report(incident_id):
    logger.info("5. Downloading Incident Report JSON...")
    resp = requests.get(f"{BASE_URL}/report/{incident_id}?format=json")
    report = resp.json()
    print("\n--- FINAL AI INCIDENT REPORT ---")
    print(json.dumps(report, indent=2))
    print("--------------------------------\n")
    logger.info("Demo Scenario Complete!")

if __name__ == "__main__":
    logger.info("=== Starting AutoSRE E2E Demo ===")
    
    # 1. Trigger failure via log injection
    write_trigger_log()
    time.sleep(2) # Wait for filesystem sync
    
    # 2. Run analysis
    incident_id = analyze_logs()
    
    if incident_id:
        time.sleep(2)
        
        # 3. Remediate
        remediate_incident(incident_id)
        
        # 4. Check status
        check_status(incident_id)
        
        # 5. Get repot
        download_report(incident_id)
