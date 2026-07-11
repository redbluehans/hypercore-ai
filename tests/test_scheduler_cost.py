from cost_governor import CostGovernor, BudgetExceeded
from scheduler import Scheduler, Node

print("=== Cost Governor ===")
cg = CostGovernor()
cg.set_budget("agt_r1", usd=0.10)

print("1. Preflight con budget suficiente")
reserved = cg.preflight("agt_r1", max_tokens=10000)
print(f"   reservado=${reserved:.4f} disponible=${cg.available('agt_r1'):.4f}")

print("2. Postflight con uso real menor al estimado")
real_cost = cg.postflight("agt_r1", reserved, real_tokens=6000)
print(f"   costo_real=${real_cost:.4f} budget_restante=${cg.available('agt_r1'):.4f}")

print("3. Preflight que excede budget -> debe rechazar")
try:
    cg.preflight("agt_r1", max_tokens=999999)
except BudgetExceeded as e:
    print("   RECHAZADO:", e)

print("\n=== Scheduler ===")
sched = Scheduler([Node("node-1", cpu_total=4, mem_total=8), Node("node-2", cpu_total=4, mem_total=8)])

sched.enqueue("agt_w1", cpu=1, mem=1, mode="async")
sched.enqueue("agt_r1", cpu=1, mem=1, mode="sync")   # llegó después pero es RPC -> prioridad

print("Cola drenada en orden (RPC primero aunque llegó 2do):")
while True:
    r = sched.drain_one()
    if not r:
        break
    print("   ->", r)

print("\nSegunda ejecución de agt_r1 -> respeta afinidad (mismo nodo, cache hit)")
sched.enqueue("agt_r1", cpu=1, mem=1, mode="sync")
print("   ->", sched.drain_one())
