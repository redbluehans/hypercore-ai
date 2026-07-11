from event_bus import EventBus
from memory import MemoryPlane
from reconciliation import ReconciliationLoop

bus, mem = EventBus(), MemoryPlane()
loop = ReconciliationLoop(bus, mem)
AGENT = "agt_demo01"

print("1. Agente dormido, sin mensajes -> tick no hace nada")
print("   ->", loop.tick(AGENT, ["researcher"]))

print("\n2. Llega un mensaje al Event Bus (JetStream simulado)")
bus.publish(AGENT, {"text": "investiga precios de mercado"})
print("   pending:", bus.pending(AGENT))

print("\n3. Reconciliation Loop detecta trabajo pendiente -> despierta runtime")
result = loop.tick(AGENT, ["researcher"])
print("   ->", result)

print("\n4. Working Memory quedó con checkpoint tras terminar")
print("   ->", mem.working_get(AGENT))

print("\n5. Episodic Memory (hash-chain) registró la ejecución")
for r in mem.episodic_log(AGENT):
    print("   ->", r["event"]["type"], "hash:", r["hash"][:12], "...")

print("\n6. Verificación de integridad del ledger (Sec.18.4)")
print("   cadena íntegra:", mem.verify_chain(AGENT))

print("\n7. Segundo mensaje + intento de manipular el historial")
bus.publish(AGENT, {"text": "resume hallazgos"})
loop.tick(AGENT, ["researcher"])
mem.episodic_log(AGENT)[0]["event"]["type"] = "ALTERADO"
print("   cadena íntegra tras manipulación:", mem.verify_chain(AGENT))
