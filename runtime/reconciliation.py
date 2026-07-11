"""Reconciliation Loop (Sec.8): estado deseado (mensaje pendiente + ACTIVE) vs real (sin runtime) -> despierta."""
from event_bus import EventBus
from memory import MemoryPlane
from runner import wake_and_run

class ReconciliationLoop:
    def __init__(self, bus: EventBus, memory: MemoryPlane):
        self.bus = bus
        self.memory = memory

    def tick(self, agent_id: str, capabilities: list[str]):
        if not self.bus.pending(agent_id):
            return None  # sigue dormido, sin costo (Sec.8 serverless)

        messages = self.bus.consume_all(agent_id)
        working = self.memory.working_get(agent_id)

        result = wake_and_run(agent_id, capabilities, messages, working)

        if result["status"] == "TERMINATED":
            self.memory.working_set(agent_id, result["working_memory"])  # checkpoint
            self.memory.episodic_append(agent_id, {
                "type": "runtime_execution", "in": messages, "out": result["responses"]
            })
        else:
            self.memory.episodic_append(agent_id, {"type": "runtime_crash", "error": result.get("error")})

        return result
