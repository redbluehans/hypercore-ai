"""Prueba end-to-end del Control Plane Fase 0: crea agente, lo activa, lo pausa, intenta transición inválida."""
import json
import urllib.request

BASE = "http://localhost:8080"


def call(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method,
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


print("1. Crear agente (BIOS valida capabilities y budget)")
status, agent = call("POST", "/v1/agents", {
    "name": "market-researcher-01",
    "capabilities": ["researcher"],
    "token_budget_per_hour": 50000,
})
print(f"   -> {status} state={agent.get('state')} id={agent.get('id')}")
agent_id = agent["id"]

print("\n2. Crear agente con capability NO aprobada (debe fallar en BIOS)")
status, err = call("POST", "/v1/agents", {
    "name": "bad-agent", "capabilities": ["hacker"], "token_budget_per_hour": 1000,
})
print(f"   -> {status} {err}")

print("\n3. Activar agente (REGISTERED -> ACTIVE)")
status, agent = call("POST", f"/v1/agents/{agent_id}:activate")
print(f"   -> {status} state={agent.get('state')}")

print("\n4. Pausar agente (ACTIVE -> PAUSED)")
status, agent = call("POST", f"/v1/agents/{agent_id}:pause")
print(f"   -> {status} state={agent.get('state')}")

print("\n5. Intentar transición ilegal (PAUSED -> DEPRECATED, no permitida)")
status, err = call("POST", f"/v1/agents/{agent_id}:deprecate")
print(f"   -> {status} {err}")

print("\n6. Reactivar y archivar (PAUSED -> ACTIVE -> ARCHIVED)")
call("POST", f"/v1/agents/{agent_id}:activate")
status, agent = call("POST", f"/v1/agents/{agent_id}:archive")
print(f"   -> {status} state={agent.get('state')}")

print("\n7. Listar todos los agentes")
status, agents = call("GET", "/v1/agents")
print(f"   -> {status} total={len(agents['agents'])}")
