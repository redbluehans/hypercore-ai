"""Event Bus (Sec.7). Simula JetStream: persiste mensajes aunque el agente esté dormido."""
import threading, queue

class EventBus:
    def __init__(self):
        self._lock = threading.Lock()
        self._queues: dict[str, queue.Queue] = {}

    def _q(self, agent_id):
        with self._lock:
            return self._queues.setdefault(agent_id, queue.Queue())

    def publish(self, agent_id: str, message: dict):
        self._q(agent_id).put(message)

    def pending(self, agent_id: str) -> bool:
        return not self._q(agent_id).empty()

    def consume_all(self, agent_id: str) -> list[dict]:
        q, out = self._q(agent_id), []
        while not q.empty():
            out.append(q.get_nowait())
        return out
