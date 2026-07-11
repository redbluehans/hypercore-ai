from event_bus import EventBus
from memory import MemoryPlane
from communication import CommunicationLayer
from permission import PermissionDenied
from reconciliation import ReconciliationLoop

bus, mem = EventBus(), MemoryPlane()
registry = {"agt_r1": ["researcher"], "agt_w1": ["writer"]}
comm = CommunicationLayer(bus, mem, registry)
loop = ReconciliationLoop(bus, mem)

print("1. researcher -> writer, async (permitido por policy_matrix)")
comm.send("agt_r1", "agt_w1", "writer", "async", {"text": "hallazgo: precios subieron 8%"})
print("   enviado. writer despierta y procesa:")
print("   ->", loop.tick("agt_w1", ["writer"]))

print("\n2. writer -> researcher, sync (NO está en la policy_matrix -> debe denegar)")
try:
    comm.send("agt_w1", "agt_r1", "researcher", "sync", {"text": "dame más datos"})
except PermissionDenied as e:
    print("   DENEGADO:", e)

print("\n3. Auditoría de agt_w1: se registró el intento denegado, igual que uno permitido")
for r in mem.episodic_log("agt_w1"):
    print("   ->", r["event"])
