import logging
import sys
import os

# Set up logging to avoid errors in imported modules
logging.basicConfig(level=logging.INFO)

# Simulation engine and dependencies are in the current dir
from simulation_engine import simulate_remediation
from dependency_graph import build_service_graph

def test_scenarios():
    # Mocked service graph for testing recursion and weights
    service_graph = {
        "shop-frontend": ["order-backend"],
        "order-backend": ["faulty-service"],
        "faulty-service": []
    }
    
    print("--- SCENARIO 1: Restart faulty-service (Core, 2 Downstream) ---")
    rem = {"action": "restart", "target": "faulty-service"}
    res = simulate_remediation(rem, [], service_graph, metrics={"cpu": 10, "mem": 10})
    print(f"Risk Score: {res['risk_score']} | Level: {res['risk_level']}")
    print(f"Impact: {res['impact_metrics']['financial_loss_est']} (Loss rate), UX: {res['impact_metrics']['ux_impact']}")
    print(f"Breakdown: {res['risk_breakdown']}")
    print(f"Checklist count: {len(res['safety_checklist'])}")
    
    print("\n--- SCENARIO 4: High CPU Scenario (+30 risk) ---")
    rem = {"action": "restart", "target": "faulty-service"}
    res = simulate_remediation(rem, [], service_graph, metrics={"cpu": 95, "mem": 90})
    print(f"Risk Score: {res['risk_score']} | Level: {res['risk_level']}")
    print(f"Resource Risk: {res['risk_breakdown']['Resource']}")

if __name__ == "__main__":
    test_scenarios()
