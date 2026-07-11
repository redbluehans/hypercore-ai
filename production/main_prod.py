"""
Fase 8b — Servidor de producción real: Postgres + NATS detrás de la misma API HTTP.
Puente: EventBusNATS es async, http.server es sync -> se envuelve con asyncio.run()
por request. Válido para carga moderada; para alto throughput, migrar a aiohttp
(siguiente paso, no incluido aquí para no fallar a medias sin poder probarlo).

Requiere: pip install -r requirements.txt  +  docker compose up -d postgres nats
Ejecutar: python3 main_prod.py
"""
import asyncio, json, sys, os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

for d in ["core", "scheduler", "communication", "database"]:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", d))

from agent import AgentDNA, AgentState, InvalidTransition, BiosValidationError, bios_validate
from permission import PermissionDenied
from cost_governor import CostGovernor, BudgetExceeded
from db_postgres import PostgresDB, AgentStorePG, MemoryPlanePG
from event_bus_nats import EventBusNATS
# Nota: Scheduler no está wireado aquí todavía — este server cubre CRUD + comunicación
# auditada + costo. El endpoint /v1/tick (placement + ejecución real) queda pendiente,
# ver hypercore-fase4/main_v2.py para la referencia de cómo integrarlo.


class NATSSyncAdapter:
    """Expone la interfaz sync (publish/pending/consume_all) que espera communication.py,
    envolviendo cada llamada async con asyncio.run(). Documentado como el trade-off consciente."""
    def __init__(self, nats_bus: EventBusNATS):
        self._bus = nats_bus

    def publish(self, agent_id, message):
        asyncio.run(self._bus.publish(agent_id, message))

    def pending(self, agent_id):
        return asyncio.run(self._bus.pending(agent_id))

    def consume_all(self, agent_id):
        return asyncio.run(self._bus.consume_all(agent_id))


# --- Bootstrap real: conecta a Postgres y NATS de verdad ---
pg_db = PostgresDB()
store = AgentStorePG(pg_db)
mem = MemoryPlanePG(pg_db)

_nats_raw = EventBusNATS()
asyncio.run(_nats_raw.connect())
bus = NATSSyncAdapter(_nats_raw)

cg = CostGovernor()
registry: dict[str, list[str]] = {}

from permission import check as perm_check

ACTIONS = {"activate": AgentState.ACTIVE, "pause": AgentState.PAUSED,
           "archive": AgentState.ARCHIVED, "deprecate": AgentState.DEPRECATED}


def send_message(sender_id, target_id, target_cap, mode, text, max_tokens):
    sender_caps = registry.get(sender_id, [])
    allowed = perm_check(sender_caps, target_cap, mode)
    mem.episodic_append(sender_id, {"type": "comm_attempt", "target": target_id,
                                     "target_cap": target_cap, "mode": mode, "allowed": allowed})
    if not allowed:
        raise PermissionDenied(f"{sender_id} no puede enviar '{mode}' a '{target_cap}'")
    reserved = cg.preflight(sender_id, max_tokens)
    bus.publish(target_id, {"from": sender_id, "mode": mode, "text": text})
    cg.postflight(sender_id, reserved, real_tokens=max_tokens // 2)
    return {"status": "sent", "budget_left": cg.available(sender_id)}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/v1/agents":
                spec = self._body()
                bios_validate(spec)
                a = AgentDNA(name=spec["name"], capabilities=spec["capabilities"],
                             token_budget_per_hour=spec["token_budget_per_hour"])
                a.transition(AgentState.REGISTERED)
                store.save(a)
                registry[a.id] = a.capabilities
                cg.set_budget(a.id, usd=spec.get("budget_usd", 1.0))
                return self._send(201, a.to_dict())

            if path.startswith("/v1/agents/") and ":" in path:
                agent_id, action = path.removeprefix("/v1/agents/").split(":", 1)
                a = store.get(agent_id)
                if not a: return self._send(404, {"error": "no existe"})
                a.transition(ACTIONS[action])
                store.save(a)
                return self._send(200, a.to_dict())

            if path == "/v1/send":
                b = self._body()
                return self._send(200, send_message(b["sender_id"], b["target_id"],
                                                      b["target_cap"], b["mode"], b["text"],
                                                      b.get("max_tokens", 1000)))
        except BiosValidationError as e:
            return self._send(422, {"error": "BIOS", "detail": str(e)})
        except InvalidTransition as e:
            return self._send(409, {"error": str(e)})
        except (PermissionDenied, BudgetExceeded) as e:
            return self._send(403, {"error": str(e)})
        except (ValueError, KeyError) as e:
            return self._send(400, {"error": "request inválido", "detail": str(e)})
        self._send(404, {"error": "ruta no encontrada"})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/v1/agents":
            return self._send(200, {"agents": [a.to_dict() for a in store.list_all()]})
        if path.startswith("/v1/agents/") and "/audit" in path:
            agent_id = path.split("/")[3]
            return self._send(200, {"log": mem.episodic_log(agent_id), "chain_ok": mem.verify_chain(agent_id)})
        if path.startswith("/v1/agents/"):
            a = store.get(path.removeprefix("/v1/agents/"))
            return self._send(200, a.to_dict()) if a else self._send(404, {"error": "no existe"})
        self._send(404, {"error": "ruta no encontrada"})

    def log_message(self, *a): pass


if __name__ == "__main__":
    print("HyperCore PRODUCCIÓN (Postgres+NATS) en :8080")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
