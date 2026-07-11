"""
Agent Runner (Sec.8, 13.1): modelo serverless — despierta al llegar mensaje, procesa, se duerme.
Aislamiento: subprocess (equivalente mínimo a Docker/Wasm de la arquitectura final).
"""
import subprocess, json, sys

WORKER = "/home/claude/hypercore/worker.py"

def wake_and_run(agent_id: str, capabilities: list[str], messages: list[dict], working_mem: dict) -> dict:
    """
    PENDING -> SCHEDULED -> RUNNING -> checkpoint -> TERMINATED (Sec.8)
    El worker corre en un proceso separado (aislamiento real de fallos/memoria).
    """
    payload = json.dumps({"agent_id": agent_id, "capabilities": capabilities,
                           "messages": messages, "working_memory": working_mem})
    result = subprocess.run([sys.executable, WORKER], input=payload,
                             capture_output=True, text=True, timeout=10)
    if result.returncode != 0:
        return {"status": "CRASHED", "error": result.stderr.strip()}
    return json.loads(result.stdout)
