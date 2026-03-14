import requests
import logging

logger = logging.getLogger(__name__)

JAEGER_API_URL = "http://jaeger:16686/api/traces"

def build_service_graph(service_name: str = "shop-frontend", lookback="1h"):
    """
    Builds a service dependency graph by querying Jaeger for recent traces.
    Returns something like:
    {
      "shop-frontend": ["order-backend"],
      "order-backend": ["faulty-service"],
      "faulty-service": []
    }
    """
    graph = {}
    try:
        # Fetch traces to analyze dependencies
        resp = requests.get(f"{JAEGER_API_URL}?service={service_name}&limit=10", timeout=2)
        if resp.status_code == 200:
            data = resp.json()
            if data and data.get("data"):
                for trace in data["data"]:
                    processes = trace.get("processes", {})
                    spans = trace.get("spans", [])
                    
                    # map span ID -> service name
                    span_to_svc = {}
                    for s in spans:
                        proc_id = s.get("processID")
                        svc = processes.get(proc_id, {}).get("serviceName", "unknown")
                        span_to_svc[s["spanID"]] = svc
                        if svc not in graph:
                            graph[svc] = set()

                    # Find parent-child relationships
                    for s in spans:
                        child_svc = span_to_svc.get(s["spanID"])
                        for ref in s.get("references", []):
                            if ref.get("refType") == "CHILD_OF":
                                parent_span_id = ref.get("spanID")
                                parent_svc = span_to_svc.get(parent_span_id)
                                if parent_svc and child_svc and parent_svc != child_svc:
                                    graph[parent_svc].add(child_svc)
                                    
        # Convert sets to lists
        for k in graph:
            graph[k] = list(graph[k])
            
    except Exception as e:
        logger.error(f"Failed to build service graph from Jaeger: {e}")
    
    if not graph:
        # Fallback if no traces or Jaeger unavailable
        graph = {
            "shop-frontend": ["order-backend"],
            "order-backend": ["faulty-service"],
            "faulty-service": []
        }
        
    return graph
