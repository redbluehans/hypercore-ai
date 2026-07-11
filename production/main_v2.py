"""
HyperCore AI - Fase 4: API pública integrada (Sec.21) + Panel Web
Une todo lo de fases 0-3 detrás de una sola API REST.
Ejecutar: python3 main_v2.py  ->  abrir panel.html en el navegador (apunta a :8080)
"""
import json, sys, os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

for d in ["core", "runtime", "scheduler", "memory", "communication"]:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", d))

from agent import AgentDNA, AgentState, InvalidTransition, BiosValidationError, bios_validate
from store import AgentStore
from event_bus import EventBus
from memory import MemoryPlane
from communication import CommunicationLayer
from permission import PermissionDenied
from reconciliation import ReconciliationLoop
from cost_governor import CostGovernor, BudgetExceeded
from scheduler import Scheduler, Node

store = AgentStore()
bus, mem, cg = EventBus(), MemoryPlane(), CostGovernor()
registry: dict[str, list[str]] = {}
comm = CommunicationLayer(bus, mem, registry)
loop = ReconciliationLoop(bus, mem)
sched = Scheduler([Node("node-1", 8, 16), Node("node-2", 8, 16)])

ACTIONS = {"activate": AgentState.ACTIVE, "pause": AgentState.PAUSED,
           "archive": AgentState.ARCHIVED, "deprecate": AgentState.DEPRECATED}


class Handler(BaseHTTPRequestHandler):
    ALLOWED_ORIGIN = "http://localhost:5500"  # ajustar al dominio real del Panel Web en producción

    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", self.ALLOWED_ORIGIN)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        if n == 0:
            return {}
        try:
            return json.loads(self.rfile.read(n))
        except json.JSONDecodeError:
            raise ValueError("JSON malformado en el body")

    def do_OPTIONS(self):
        self.send_response(204); self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type"); self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/v1/agents":
                return self._create()
            if path.startswith("/v1/agents/") and ":" in path:
                agent_id, action = path.removeprefix("/v1/agents/").split(":", 1)
                return self._transition(agent_id, action)
            if path == "/v1/send":
                return self._send_message()
            if path == "/v1/tick":
                return self._tick()
        except (PermissionDenied, BudgetExceeded) as e:
            return self._send(403, {"error": str(e)})
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": "request inválido", "detail": str(e)})
        self._send(404, {"error": "ruta no encontrada"})

    def _create(self):
        spec = self._body()
        try:
            bios_validate(spec)
        except BiosValidationError as e:
            return self._send(422, {"error": "BIOS", "detail": str(e)})
        agent = AgentDNA(name=spec["name"], capabilities=spec["capabilities"],
                          token_budget_per_hour=spec["token_budget_per_hour"])
        agent.transition(AgentState.REGISTERED)
        store.save(agent)
        registry[agent.id] = agent.capabilities
        cg.set_budget(agent.id, usd=spec.get("budget_usd", 1.0))
        self._send(201, agent.to_dict())

    def _transition(self, agent_id, action):
        agent = store.get(agent_id)
        if not agent: return self._send(404, {"error": "no existe"})
        try:
            agent.transition(ACTIONS[action])
        except InvalidTransition as e:
            return self._send(409, {"error": str(e)})
        store.save(agent)
        self._send(200, agent.to_dict())

    def _send_message(self):
        b = self._body()
        reserved = cg.preflight(b["sender_id"], max_tokens=b.get("max_tokens", 1000))
        comm.send(b["sender_id"], b["target_id"], b["target_cap"], b["mode"], {"text": b["text"]})
        cg.postflight(b["sender_id"], reserved, real_tokens=b.get("max_tokens", 1000) // 2)
        self._send(200, {"status": "sent", "budget_left": cg.available(b["sender_id"])})

    def _tick(self):
        b = self._body()
        agent_id = b["agent_id"]
        sched.enqueue(agent_id, cpu=1, mem=1, mode="async")
        placement = sched.drain_one()
        result = loop.tick(agent_id, registry.get(agent_id, []))
        sched.release(agent_id)  # runtime serverless terminó -> libera CPU/RAM del nodo
        self._send(200, {"placement": placement, "execution": result})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/v1/agents":
            return self._send(200, {"agents": [a.to_dict() for a in store.list_all()]})
        if path.startswith("/v1/agents/") and "/audit" in path:
            agent_id = path.split("/")[3]
            return self._send(200, {"log": mem.episodic_log(agent_id), "chain_ok": mem.verify_chain(agent_id)})
        if path.startswith("/v1/agents/"):
            agent = store.get(path.removeprefix("/v1/agents/"))
            return self._send(200, agent.to_dict()) if agent else self._send(404, {"error": "no existe"})
        self._send(404, {"error": "ruta no encontrada"})

    def log_message(self, *a): pass


if __name__ == "__main__":
    print("HyperCore API (Fase 4) en :8080")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
