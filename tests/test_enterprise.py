from dag_workflow import DAGWorkflow
from semantic_event_bus import SemanticEventBus
from policy_abac import ABACPolicyEngine, ABACDenied
from knowledge_graph import KnowledgeGraph
from reputation import compute_reputation
from smart_cache import SmartCache
from event_bus import EventBus
from memory import MemoryPlane
from reconciliation import ReconciliationLoop
from chaos_engine import ChaosEngine

print("1. DAG Workflow — capas paralelas")
dag = DAGWorkflow()
dag.add_step("fetch"); dag.add_step("clean", ["fetch"]); dag.add_step("analyze", ["clean"])
dag.add_step("report_a", ["analyze"]); dag.add_step("report_b", ["analyze"])
print("   ->", dag.run(lambda s: f"done:{s}"))

print("\n2. Semantic Event Bus — orden por prioridad/confianza")
seb = SemanticEventBus()
seb.publish("agt_x", {"t": "low"}, priority=2, confidence=0.9)
seb.publish("agt_x", {"t": "urgent"}, priority=9, confidence=0.5)
print("   ->", [m["payload"]["t"] for m in seb.consume_sorted("agt_x")])

print("\n3. Policy ABAC — capability OK pero riesgo excede umbral")
abac = ABACPolicyEngine()
abac.add_rule("risk_level", "<=", 5)
try:
    abac.authorize(["researcher"], "writer", "async", {"risk_level": 8})
except ABACDenied as e:
    print("   DENEGADO:", e)

print("\n4. Knowledge Graph — relación y verificación de camino")
kg = KnowledgeGraph()
kg.relate("agt_r1", "informa_a", "agt_w1", confidence=0.95)
print("   path agt_r1->agt_w1:", kg.path_exists("agt_r1", "agt_w1"))

print("\n5. Reputation — sobre un log simulado")
mem = MemoryPlane()
mem.episodic_append("agt_x", {"type": "runtime_execution"})
mem.episodic_append("agt_x", {"type": "runtime_crash"})
print("   ->", compute_reputation(mem, "agt_x"))

print("\n6. Smart Cache — hit tras repetir el mismo input")
cache = SmartCache()
print("   1a llamada:", cache.get("agt_x", {"q": "precio"}))
cache.set("agt_x", {"q": "precio"}, {"resp": "100"})
print("   2a llamada (hit):", cache.get("agt_x", {"q": "precio"}), cache.stats())

print("\n7. Chaos Engine — 50% de fallos forzados, valida recuperación")
bus2 = EventBus()
mem2 = MemoryPlane()
loop2 = ReconciliationLoop(bus2, mem2)
bus2.publish("agt_c1", {"text": "hola"})
chaos = ChaosEngine(loop2, bus2)
chaos.kill_random(["agt_c1"], failure_rate=0.5)
print("   recovery_rate:", chaos.recovery_rate())

print("\n8. Live Architecture Map — requiere store/scheduler reales, ver hypercore-fase4")
