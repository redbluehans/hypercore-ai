"""
HyperCore AI - Control Plane (Fase 0)
API mínima: crear agente, consultar, transicionar estado.
Mapea al contrato de API pública ya diseñado (Sec. 21):
  POST /v1/agents
  GET  /v1/agents/{id}
  GET  /v1/agents
  POST /v1/agents/{id}:activate
  POST /v1/agents/{id}:pause
  POST /v1/agents/{id}:archive

Ejecutar: python3 main.py
Probar:   python3 test_client.py
"""
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from agent import AgentDNA, AgentState, InvalidTransition, BiosValidationError, bios_validate
from store import AgentStore

store = AgentStore()

ACTIONS = {
    "activate": AgentState.ACTIVE,
    "pause": AgentState.PAUSED,
    "archive": AgentState.ARCHIVED,
    "deprecate": AgentState.DEPRECATED,
}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    # ---- POST /v1/agents  |  POST /v1/agents/{id}:action ----
    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/v1/agents":
            return self._create_agent()

        if path.startswith("/v1/agents/") and ":" in path:
            agent_id, action = path.removeprefix("/v1/agents/").split(":", 1)
            return self._transition(agent_id, action)

        self._send(404, {"error": "ruta no encontrada"})

    def _create_agent(self):
        spec = self._read_body()
        try:
            bios_validate(spec)  # HyperCore BIOS (14.2)
        except BiosValidationError as e:
            return self._send(422, {"error": "BIOS validation failed", "detail": str(e)})

        agent = AgentDNA(
            name=spec["name"],
            capabilities=spec["capabilities"],
            token_budget_per_hour=spec["token_budget_per_hour"],
        )
        agent.transition(AgentState.REGISTERED)  # BIOS pasó -> REGISTERED automático (Sec. 8)
        store.save(agent)
        self._send(201, agent.to_dict())

    def _transition(self, agent_id: str, action: str):
        agent = store.get(agent_id)
        if not agent:
            return self._send(404, {"error": f"agente {agent_id} no existe"})

        target = ACTIONS.get(action)
        if not target:
            return self._send(400, {"error": f"acción desconocida: {action}"})

        try:
            agent.transition(target)
        except InvalidTransition as e:
            return self._send(409, {"error": str(e)})

        store.save(agent)
        self._send(200, agent.to_dict())

    # ---- GET /v1/agents  |  GET /v1/agents/{id} ----
    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/v1/agents":
            return self._send(200, {"agents": [a.to_dict() for a in store.list_all()]})

        if path.startswith("/v1/agents/"):
            agent_id = path.removeprefix("/v1/agents/")
            agent = store.get(agent_id)
            if not agent:
                return self._send(404, {"error": f"agente {agent_id} no existe"})
            return self._send(200, agent.to_dict())

        self._send(404, {"error": "ruta no encontrada"})

    def log_message(self, fmt, *args):
        pass  # silencia logs por defecto de http.server


if __name__ == "__main__":
    port = 8080
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"HyperCore Control Plane (Fase 0) escuchando en :{port}")
    server.serve_forever()
