import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import get_db, MemoryEntryModel, init_db

init_db()
db = next(get_db())

if not db.query(MemoryEntryModel).first():
    entry = MemoryEntryModel(
        incident_type="Baseline: Faulty Service Outage",
        root_cause="The faulty-service container often becomes unresponsive due to simulated high load or internal connection drops. A standard container restart is the verified resolution.",
        action_taken="docker restart faulty-service",
        target="faulty-service",
        success=True,
        details={
            "severity": "High", 
            "causal_chain": ["Constant baseline traffic", "Service latency increases", "Health check begins timing out", "Service marked degraded"],
            "suggested_action": "restart container faulty-service"
        }
    )
    db.add(entry)
    db.commit()
    print("Success: Memory database seeded with baseline insights.")
else:
    print("Info: Database already contains memory entries. No seeding needed.")
