import logging

logger = logging.getLogger(__name__)

def simulate_remediation(remediation: dict, trace_data: list, service_graph: dict) -> dict:
    """
    Simulates the impact of the AI's suggested remediation.
    """
    action = remediation.get("action", "").lower()
    target_service = remediation.get("target", "").lower()

    if not target_service:
        # Try to extract from the raw string
        raw_cmd = remediation.get("command", "") or remediation.get("suggested_action", "")
        if "faulty-service" in raw_cmd:
            target_service = "faulty-service"
        elif "order-backend" in raw_cmd:
            target_service = "order-backend"
        elif "shop-frontend" in raw_cmd:
            target_service = "shop-frontend"
        else:
            target_service = "unknown"
            
    if "restart" in action or "restart" in remediation.get("suggested_action", "").lower():
        action_type = "restart_container"
    elif "scale" in action:
        action_type = "scale_service"
    elif "memory" in action:
        action_type = "increase_memory_limit"
    else:
        action_type = "unknown_action"

    # Evaluate rules based on action typed
    downtime = "0 seconds"
    base_risk = 10
    
    if action_type == "restart_container":
        downtime = "3-5 seconds"
        base_risk = 30
    elif action_type == "scale_service":
        downtime = "No downtime"
        base_risk = 10
    elif action_type == "increase_memory_limit":
        downtime = "1-2 seconds (restart required)"
        base_risk = 20
    else:
        downtime = "Unknown"
        base_risk = 40

    # Calculate affected downstream/upstream based on dependency graph
    # Find who depends on the target service
    affected_services = []
    
    for service, dependencies in service_graph.items():
        if target_service in dependencies:
            affected_services.append(service)
            
    # Risk calculation
    risk_score = base_risk
    
    # +15 risk for every service that depends on it
    risk_score += (len(affected_services) * 15)
    
    # Depth in graph heuristics
    if target_service == "faulty-service":
        risk_score += 10 # core backing service
    elif target_service == "order-backend":
        risk_score += 20 # critical middleware
    elif target_service == "shop-frontend":
        risk_score += 5 # edge
        
    # Cap score
    risk_score = min(risk_score, 100)
    risk_score = max(risk_score, 0)
    
    if risk_score <= 30:
        risk_level = "LOW"
        recommendation = "SAFE TO AUTOMATE"
        auto_rec = True
    elif risk_score <= 60:
        risk_level = "MEDIUM"
        recommendation = "MANUAL REVIEW RECOMMENDED"
        auto_rec = False
    else:
        risk_level = "HIGH"
        recommendation = "MANUAL FIX REQUIRED"
        auto_rec = False
        
    result = {
        "predicted_downtime": downtime,
        "affected_services": affected_services,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "recommendation": recommendation,
        "automation_recommended": auto_rec
    }
    
    logger.info(f"Simulated {action_type} on {target_service}. Risk: {risk_score} ({risk_level})")
    
    return result
