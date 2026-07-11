#!/usr/bin/env python3
"""Corre todas las pruebas. Uso: python3 run_all_tests.py"""
import subprocess, sys, time, os

ROOT = os.path.dirname(os.path.abspath(__file__))
MODULE_DIRS = ["core", "runtime", "scheduler", "memory", "communication", "marketplace", "enterprise", "database"]

TESTS = [
    ("Core - Control Plane", "tests/test_core.py", "core"),
    ("Runtime/Memoria", "tests/test_runtime_memory.py", None),
    ("Comunicación/Permisos", "tests/test_communication.py", None),
    ("Scheduler/Cost", "tests/test_scheduler_cost.py", None),
    ("Enterprise (8 mejoras)", "tests/test_enterprise.py", None),
]

env = os.environ.copy()
env["PYTHONPATH"] = os.pathsep.join(os.path.join(ROOT, d) for d in MODULE_DIRS) + os.pathsep + env.get("PYTHONPATH", "")

results = []
for name, path, server_dir in TESTS:
    full = os.path.join(ROOT, path)
    proc_server = None
    if server_dir:
        proc_server = subprocess.Popen([sys.executable, "main.py"], cwd=os.path.join(ROOT, server_dir),
                                        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    t0 = time.time()
    r = subprocess.run([sys.executable, full], cwd=ROOT, capture_output=True, text=True, env=env)
    elapsed = time.time() - t0
    if proc_server:
        proc_server.terminate()
    ok = r.returncode == 0
    results.append((name, ok, elapsed, r.stderr[-300:] if not ok else ""))

print(f"\n{'='*60}\nRESULTADOS\n{'='*60}")
for name, ok, elapsed, err in results:
    print(f"{'✅ PASS' if ok else '❌ FAIL'}  {name:30s} {elapsed:.2f}s")
    if not ok:
        print(f"        {err}")

failed = sum(1 for _, ok, _, _ in results if not ok)
print(f"\n{len(results)-failed}/{len(results)} suites OK")
sys.exit(1 if failed else 0)
