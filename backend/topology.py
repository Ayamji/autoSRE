import subprocess
import json
import logging
import math

logger = logging.getLogger(__name__)

def get_topology():
    nodes = []
    edges = []
    try:
        # Get all running containers
        cmd = ["docker", "ps", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Failed to run docker ps")
            return {"nodes": [], "edges": []}
            
        container_ids = result.stdout.strip().split()
        if not container_ids:
            return {"nodes": [], "edges": []}
            
        cmd = ["docker", "inspect"] + container_ids
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error("Failed to run docker inspect")
            return {"nodes": [], "edges": []}
            
        containers = json.loads(result.stdout)
        
        container_map = {} 
        name_to_id = {} 
        
        for c in containers:
            name = c["Name"].lstrip("/")
            cid = c["Id"]
            
            labels = c["Config"].get("Labels", {})
            service_name = labels.get("com.docker.compose.service", name)
            
            image = c["Config"].get("Image", "")
            node_type = "service"
            if "prometheus" in image or "grafana" in image or "loki" in image or "promtail" in image:
                node_type = "infra"
                
            node = {
                "id": cid,
                "label": service_name.capitalize(),
                "sublabel": name,
                "type": node_type,
                "container": name
            }
            nodes.append(node)
            container_map[cid] = node
            
            name_to_id[name] = cid
            name_to_id[service_name] = cid
            
            networks = c.get("NetworkSettings", {}).get("Networks", {})
            for net_name, net_info in networks.items():
                aliases = net_info.get("Aliases", [])
                if aliases:
                    for alias in aliases:
                        name_to_id[alias] = cid

        for c in containers:
            cid = c["Id"]
            env_vars = c["Config"].get("Env", [])
            for env in env_vars:
                key, _, value = env.partition("=")
                for alias, target_id in name_to_id.items():
                    if target_id == cid:
                        continue 
                    if len(alias) > 3 and alias in value:
                        edges.append({
                            "from": cid,
                            "to": target_id,
                            "label": key.split("_")[0].lower() # e.g. PAYMENT_URL -> payment
                        })
                        
        # Add a mock "Browser" external node
        nodes.append({
            "id": "external-user",
            "label": "Browser",
            "sublabel": "External",
            "type": "external",
            "container": "user"
        })
        container_map["external-user"] = nodes[-1]
        
        # Link user to frontend
        for n in nodes:
            if "frontend" in n["sublabel"] or "grafana" in n["sublabel"]:
                edges.append({
                    "from": "external-user",
                    "to": n["id"],
                    "label": "HTTP"
                })

    except Exception as e:
        logger.error(f"Error getting topology: {e}")
        
    unique_edges = []
    seen = set()
    for e in edges:
        sig = (e["from"], e["to"])
        if sig not in seen:
            seen.add(sig)
            unique_edges.append(e)

    front_nodes = []
    for n in nodes:
        front_nodes.append({
            "id": n["container"], 
            "label": n["label"],
            "sublabel": n["sublabel"],
            "type": n["type"],
            "container": n["container"]
        })
        
    front_edges = []
    for e in unique_edges:
        from_container = container_map[e["from"]]["container"]
        to_container = container_map[e["to"]]["container"]
        front_edges.append({
            "from": from_container,
            "to": to_container,
            "label": e["label"]
        })
        
    # Hardcode some infra connections since they don't use ENV vars
    front_edges.append({"from": "promtail", "to": "loki", "label": "logs"})
    front_edges.append({"from": "prometheus", "to": "grafana", "label": "query"})
    front_edges.append({"from": "loki", "to": "grafana", "label": "query"})
    front_edges.append({"from": "autosre-backend", "to": "prometheus", "label": "metrics"})

    # Hierarchical Column Layout
    externals = [n for n in front_nodes if n["type"] == "external"]
    services = [n for n in front_nodes if n["type"] == "service"]
    infra = [n for n in front_nodes if n["type"] == "infra"]
    
    # Sort services for a logical flow
    def service_sort(n):
        name = n["sublabel"].lower()
        if "shop" in name: return 0
        if "order" in name: return 1
        if "faulty" in name: return 2
        if "autosre" in name: return 3
        return 4
    services.sort(key=service_sort)
    
    def distribute_column(nodes, cx, available_height=360, center_y=210):
        if not nodes: return
        count = len(nodes)
        spacing = min(110, available_height / max(1, count))
        start_y = center_y - (count - 1) * spacing / 2
        for i, n in enumerate(nodes):
            n["cx"] = int(cx)
            n["cy"] = int(start_y + i * spacing)
            n["r"] = 42 if n["type"] in ["service", "external"] else 36

    distribute_column(externals, 100)
    
    # Split services into two staggered columns if there are many
    if len(services) > 3:
        mid = math.ceil(len(services) / 2)
        distribute_column(services[:mid], 290)
        distribute_column(services[mid:], 490)
    else:
        distribute_column(services, 390)
        
    # Sort infra for logical vertical flow
    def infra_sort(n):
        name = n["sublabel"].lower()
        if "promtail" in name: return 0
        if "loki" in name: return 1
        if "prometheus" in name: return 2
        if "grafana" in name: return 3
        return 4
    infra.sort(key=infra_sort)
    
    distribute_column(infra, 680)
        
    return {"nodes": front_nodes, "edges": front_edges}
