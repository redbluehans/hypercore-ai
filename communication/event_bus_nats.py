"""
Event Bus real con NATS JetStream. Requiere: pip install -r requirements.txt
y un NATS corriendo con -js (ver docker-compose.yml en la raíz).
Interfaz async (NATS es async-nativo) — a diferencia de event_bus.py (sync/memoria).
"""
import os, json
import nats
from nats.js.api import StreamConfig

NATS_URL = os.environ.get("NATS_URL", "nats://localhost:4222")


class EventBusNATS:
    def __init__(self):
        self.nc = None
        self.js = None

    async def connect(self):
        self.nc = await nats.connect(NATS_URL)
        self.js = self.nc.jetstream()
        # Stream persistente (Sec.8: los mensajes sobreviven aunque el agente esté dormido)
        try:
            await self.js.add_stream(StreamConfig(name="HYPERCORE_AGENTS", subjects=["agents.>"]))
        except Exception:
            pass  # ya existe

    async def publish(self, agent_id: str, message: dict):
        subject = f"agents.inbox.{agent_id}"
        await self.js.publish(subject, json.dumps(message).encode())

    async def pending(self, agent_id: str) -> bool:
        subject = f"agents.inbox.{agent_id}"
        try:
            info = await self.js.stream_info("HYPERCORE_AGENTS", subjects_filter=subject)
            return info.state.messages > 0
        except Exception:
            return False

    async def consume_all(self, agent_id: str) -> list[dict]:
        subject = f"agents.inbox.{agent_id}"
        sub = await self.js.pull_subscribe(subject, durable=f"consumer_{agent_id}")
        out = []
        try:
            msgs = await sub.fetch(batch=100, timeout=1)
            for m in msgs:
                out.append(json.loads(m.data))
                await m.ack()
        except TimeoutError:
            pass
        return out

    async def close(self):
        if self.nc:
            await self.nc.close()
