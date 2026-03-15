import logging
import random
from dependency_graph import get_recursive_dependents
from sqlalchemy.orm import Session
from database import MemoryEntryModel

logger = logging.getLogger(__name__)

def simulate_remediation(remediation: dict, trace_data: list, service_graph: dict, metrics: dict = None, db: Session = None) -> dict:
    """
    Simulates the impact of the AI's suggested remediation with realistic risk factors.
    """
    action = remediation.get("action", "").lower()
    target_service = remediation.get("target", "").lower()
    suggested_action = remediation.get("suggested_action", "").lower()

    if not target_service:
        raw_cmd = remediation.get("command", "") or suggested_action
        for svc in ["faulty-service", "order-backend", "shop-frontend"]:
            if svc in raw_cmd:
                target_service = svc
                break
        if not target_service:
            target_service = "unknown"
            
    # Normalize action type
    if "restart" in action or "restart" in suggested_action:
        action_type = "restart_container"
        base_risk = 30
        downtime = "3-5 seconds"
    elif "scale" in action or "scale" in suggested_action:
        action_type = "scale_service"
        base_risk = 10
        downtime = "No downtime"
    elif "memory" in action or "limit" in action:
        action_type = "increase_memory_limit"
        base_risk = 20
        downtime = "1-2 seconds"
    else:
        action_type = "unknown_action"
        base_risk = 40
        downtime = "Unknown"

    # 1. Recursive Blast Radius
    affected_services = get_recursive_dependents(target_service, service_graph)
    blast_radius_risk = len(affected_services) * 20 # 20 points per affected downstream service
    
    # 2. Metric-Aware Risk (Load assessment)
    metric_risk = 0
    if metrics:
        # Support both 'cpu' (docker) and 'host_cpu_percent' (synthetic/host) keys
        cpu = metrics.get("cpu") or metrics.get("host_cpu_percent") or 0
        mem = metrics.get("mem") or metrics.get("host_memory_percent") or 0
        # Increase risk if system is already under stress
        if cpu > 80: metric_risk += 15
        if mem > 85: metric_risk += 15
        
    # 3. Criticality Weighting
    criticality = 0
    weights = {
        "faulty-service": 15, # Core
        "order-backend": 25,  # Mission Critical
        "shop-frontend": 5    # Edge
    }
    criticality = weights.get(target_service, 10)

    # 4. Historical Success Adjustment
    history_adjustment = 0
    if db:
        try:
            # Check last 5 remediations for this service/action
            history = db.query(MemoryEntryModel).filter(
                MemoryEntryModel.target == target_service,
                MemoryEntryModel.action_taken.contains(action)
            ).order_by(MemoryEntryModel.timestamp.desc()).limit(5).all()
            
            if history:
                success_rate = sum(1 for m in history if m.success) / len(history)
                if success_rate < 0.5:
                    history_adjustment = 20 # High risk if historical failure rate > 50%
                elif success_rate > 0.9:
                    history_adjustment = -10 # Lower risk if extremely reliable
        except Exception as e:
            logger.error(f"Failed to query history for risk simulation: {e}")

    # Total Score Calculation with subtle jitter for realism
    # Adding jitter to blast_radius_risk too so it's not perfectly linear
    risk_score = int(base_risk + (blast_radius_risk * random.uniform(0.9, 1.1)) + metric_risk + criticality + history_adjustment)
    risk_score += random.randint(-4, 4) # Real-word uncertainty jitter
    risk_score = max(5, min(98, risk_score))
    
    # Impact Metrics (Simulated for high USP)
    rps = (metrics or {}).get("request_rate_per_sec", 10)
    financial_loss_base = 0
    if "shop-frontend" in affected_services or target_service == "shop-frontend":
        financial_loss_base = 5.0 # $5.0 per request
    elif "order-backend" in affected_services or target_service == "order-backend":
        financial_loss_base = 2.5 # $2.5 per request
    
    # Add pricing jitter (±15%)
    financial_loss_base *= random.uniform(0.85, 1.15)
        
    # Actions like restarts take longer to stabilize
    estimated_impact_duration = 2 if "scale" in action_type else 5 
    estimated_impact_duration += random.uniform(-0.5, 1.5) # duration jitter
    
    # Financial loss = RPS * base_cost * duration
    total_financial_impact = round(rps * financial_loss_base * estimated_impact_duration, 2)
    
    # Safety Checklist (Dynamic based on action)
    safety_checklist = [
        {"task": f"Snapshot {target_service} state", "status": "Ready"},
        {"task": f"Divert {int(random.uniform(50, 100))}% traffic from " + target_service, "status": "Planned"},
        {"task": f"Execute {action_type} via OpenClaw", "status": "Pending"},
        {"task": "Verify upstream dependency health", "status": random.choice(["Ready", "In Progress", "Scheduled"])}
    ]
    
    # Risk Breakdown
    risk_breakdown = {
        "Dependency": "HIGH" if blast_radius_risk > 30 else ("MEDIUM" if blast_radius_risk > 10 else "LOW"),
        "Resource": "CRITICAL" if metric_risk > 20 else ("MEDIUM" if metric_risk > 0 else "STABLE"),
        "Stability": "VOLATILE" if history_adjustment > 0 else "RELIABLE",
        "Criticality": "CORE" if criticality > 20 else "NORMAL"
    }

    if risk_score <= 35:
        risk_level = "LOW"
        recommendation = "SAFE TO AUTOMATE: Low impact and high confidence."
        auto_rec = True
    elif risk_score <= 70:
        risk_level = "MEDIUM"
        recommendation = "MANUAL REVIEW RECOMMENDED: Significant dependencies or system load detected."
        auto_rec = False
    else:
        risk_level = "HIGH"
        recommendation = "MANUAL FIX REQUIRED: High blast radius or historical instability."
        auto_rec = False
        
    # Expected Outcome description
    if "restart" in action_type:
        outcome = f"System will experience a brief {estimated_impact_duration:.1f}s freeze followed by immediate pod state recovery and cache warmup."
    elif "scale" in action_type:
        outcome = "Latency will gradually normalize as load is distributed across new replicas; no downtime expected."
    else:
        outcome = "Service health will stabilize after remediation. Manual monitoring recommended during the first 5 minutes."

    result = {
        "predicted_downtime": f"{estimated_impact_duration:.1f} seconds" if "restart" in action_type else downtime,
        "affected_services": affected_services,
        "expected_outcome": outcome,
        "risk_score": int(risk_score),
        "risk_level": risk_level,
        "recommendation": recommendation,
        "automation_recommended": auto_rec,
        "impact_metrics": {
            "ux_impact": "Degraded" if len(affected_services) > 0 else "Minimal",
            "data_loss_risk": "None" if "restart" in action_type else "Low"
        },
        "risk_breakdown": risk_breakdown,
        "safety_checklist": safety_checklist
    }
    
    logger.info(f"High-impact simulation complete for {target_service}. Risk: {risk_score}")
    
    return result
