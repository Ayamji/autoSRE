
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm_analyzer import analyze_with_llm
import logging

logging.basicConfig(level=logging.INFO)

def test_gemini():
    metrics = {"service_up": False, "cpu": 45, "mem": 30}
    logs = ["ERROR: faulty-service connection refused", "CRITICAL: Health check failed for /health"]
    
    print("Triggering Gemini Analysis...")
    result = analyze_with_llm(metrics, logs)
    
    if result:
        print("\n--- Gemini Analysis Success! ---")
        print(f"Incident: {result.get('incident')}")
        print(f"Severity: {result.get('severity')}")
        print(f"Root Cause: {result.get('root_cause')}")
        print(f"Action: {result.get('recommended_action')}")
    else:
        print("\n--- Gemini Analysis Failed (Fallback Mode) ---")

if __name__ == "__main__":
    test_gemini()
