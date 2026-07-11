#!/usr/bin/env python3
"""Benchmark de operaciones críticas. Uso: python3 benchmark.py"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hypercore-fase1"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "hypercore-fase3"))
from memory import MemoryPlane
from cost_governor import CostGovernor
from scheduler import Scheduler, Node

N = 10_000

def bench(name, fn, n=N):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    dt = time.perf_counter() - t0
    print(f"{name:35s} {n/dt:>10,.0f} ops/seg   ({dt*1e6/n:.2f} µs/op)")

mem = MemoryPlane()
bench("Memory.episodic_append (hash-chain)", lambda: mem.episodic_append("bench", {"x": 1}))

cg = CostGovernor(); cg.set_budget("bench", usd=1e9)
bench("CostGovernor.preflight+postflight",
      lambda: cg.postflight("bench", cg.preflight("bench", 100), 50))

sched = Scheduler([Node(f"n{i}", 1000, 1000) for i in range(10)])
bench("Scheduler.enqueue+drain_one",
      lambda: (sched.enqueue("agt", 0.001, 0.001, "async"), sched.drain_one()))

print(f"\nVerificación de integridad sobre {N} eventos encadenados:", mem.verify_chain("bench"))
