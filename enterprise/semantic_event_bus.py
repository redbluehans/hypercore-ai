"""Semantic Event Bus: enriquece mensajes con prioridad/confianza. Ruteo explícito (Intent Bus fue rechazado, 14.7)."""
from event_bus import EventBus

class SemanticEventBus:
    def __init__(self, bus: EventBus = None):
        self.bus = bus or EventBus()

    def publish(self, agent_id: str, payload: dict, priority: int = 5, confidence: float = 1.0, source: str = ""):
        assert 0 <= priority <= 10, "priority en rango 0-10"
        assert 0.0 <= confidence <= 1.0, "confidence en rango 0-1"
        envelope = {"payload": payload, "priority": priority, "confidence": confidence, "source": source}
        self.bus.publish(agent_id, envelope)

    def consume_sorted(self, agent_id: str) -> list[dict]:
        """Consume todo lo pendiente, ordenado por prioridad desc, luego confianza desc."""
        msgs = self.bus.consume_all(agent_id)
        return sorted(msgs, key=lambda m: (-m["priority"], -m["confidence"]))
