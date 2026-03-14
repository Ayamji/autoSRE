import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OpenClaw")

def execute_action(payload: dict) -> dict:
    """
    OpenClaw structured executor.
    Accepts:
    { "action": "docker_restart", "target": "container_name" }
    { "action": "shell", "command": "echo ok" }
    """
    action = payload.get("action")
    target = payload.get("target", "")
    command_str = payload.get("command", "")
    
    logger.info(f"OpenClaw received task: {payload}")
    
    cmd = []
    
    if action == "docker_restart":
        if not target:
            return {"success": False, "output": "Target container required for docker_restart"}
        cmd = ["docker", "restart", target]
    elif action == "kubectl_rollout":
        if not target:
            return {"success": False, "output": "Target required for kubectl_rollout"}
        cmd = ["kubectl", "rollout", "restart", f"deployment/{target}"]
    elif action == "shell":
        if not command_str:
            return {"success": False, "output": "Command string required for shell action"}
        cmd = ["sh", "-c", command_str]
    else:
        return {"success": False, "output": f"Unknown action: {action}"}
        
    try:
        # Run command
        logger.info(f"Executing: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        success = result.returncode == 0
        output = result.stdout + "\n" + result.stderr if not success else result.stdout
        
        logger.info(f"Execution {'succeeded' if success else 'failed'}")
        return {
            "success": success,
            "output": output.strip()
        }
        
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return {
            "success": False,
            "output": str(e)
        }
    
if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", help="JSON payload", required=True)
    args = parser.add_argument()
    payload = json.loads(args.payload)
    print(json.dumps(execute_action(payload), indent=2))
