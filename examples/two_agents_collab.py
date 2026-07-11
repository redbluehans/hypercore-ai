"""
Ejemplo: dos agentes colaborando con permisos, costo y auditoría reales.
Correr desde la raíz del repo:
  PYTHONPATH=core:runtime:scheduler:memory:communication python3 examples/two_agents_collab.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "core"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "runtime"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scheduler"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "memory"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "communication"))

from event_bus import EventBus
from memory import MemoryPlane
from communication import CommunicationLayer
from reconciliation import ReconciliationLoop
from cost_governor import CostGovernor

bus, mem, cg = EventBus(), MemoryPlane(), CostGovernor()
registry = {"agt_researcher": ["researcher"], "agt_writer": ["writer"]}
comm = CommunicationLayer(bus, mem, registry)
loop = ReconciliationLoop(bus, mem)
cg.set_budget("agt_researcher", usd=1.0)

print("Researcher envía un hallazgo al Writer (permitido por policy_matrix)...")
reserved = cg.preflight("agt_researcher", max_tokens=500)
comm.send("agt_researcher", "agt_writer", "writer", "async",
          {"text": "el mercado creció 12% este trimestre"})
cg.postflight("agt_researcher", reserved, real_tokens=300)

print("Writer despierta (modelo serverless) y procesa el mensaje...")
result = loop.tick("agt_writer", ["writer"])
print("Resultado:", result["responses"])

print("\nAuditoría (hash-chain verificable):")
print("  cadena íntegra:", mem.verify_chain("agt_writer"))
print("  budget restante researcher: $%.4f" % cg.available("agt_researcher"))
