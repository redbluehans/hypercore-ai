"""
Comunicación agente-a-agente (Sec.7): nunca directa, siempre Permission Engine -> Event Bus.
Subject naming: agents.<capability>.<agent_id>.<intent>
"""
from event_bus import EventBus
from memory import MemoryPlane
from permission import check, PermissionDenied

class CommunicationLayer:
    def __init__(self, bus: EventBus, memory: MemoryPlane, registry: dict):
        self.bus = bus
        self.memory = memory
        self.registry = registry  # agent_id -> capabilities

    def send(self, sender_id: str, target_id: str, target_cap: str, mode: str, message: dict):
        sender_caps = self.registry.get(sender_id, [])
        allowed = check(sender_caps, target_cap, mode)

        # Nota: deny se audita igual que allow (Sec.2 fail-visible, Sec.7)
        self.memory.episodic_append(sender_id, {
            "type": "comm_attempt", "target": target_id, "target_cap": target_cap,
            "mode": mode, "allowed": allowed,
        })

        if not allowed:
            raise PermissionDenied(
                f"{sender_id} (caps={sender_caps}) no puede enviar '{mode}' a capability '{target_cap}'"
            )

        self.bus.publish(target_id, {"from": sender_id, "mode": mode, **message})
        return True
