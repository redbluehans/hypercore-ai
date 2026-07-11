"""
State Store del Control Plane (Sec. 3). En producción: Postgres (MVP) / etcd (enterprise).
Aquí: in-memory thread-safe, para validar el modelo antes de portar a Go+Postgres.
"""
import threading
from agent import AgentDNA


class AgentStore:
    def __init__(self):
        self._lock = threading.RLock()
        self._agents: dict[str, AgentDNA] = {}

    def save(self, agent: AgentDNA) -> None:
        with self._lock:
            self._agents[agent.id] = agent

    def get(self, agent_id: str) -> AgentDNA | None:
        with self._lock:
            return self._agents.get(agent_id)

    def list_all(self) -> list[AgentDNA]:
        with self._lock:
            return list(self._agents.values())

    def delete(self, agent_id: str) -> None:
        # No se usa en flujo normal: ARCHIVED es soft-delete (Sec. 8), esto es solo para tests
        with self._lock:
            self._agents.pop(agent_id, None)
