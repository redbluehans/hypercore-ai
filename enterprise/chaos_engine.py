"""Chaos Testing Engine: inyecta fallos controlados, valida self-healing (Sec.8 Reconciliation Loop)."""
import random

class ChaosEngine:
    def __init__(self, reconciliation_loop, event_bus):
        self.loop = reconciliation_loop
        self.bus = event_bus
        self.report_log: list[dict] = []

    def kill_random(self, agent_ids: list[str], failure_rate: float = 0.3):
        """Simula caída de runtime: fuerza CRASHED en vez de TERMINATED, monkeypatch temporal."""
        import runner
        original = runner.wake_and_run

        def flaky(agent_id, caps, messages, working_mem):
            if random.random() < failure_rate:
                return {"status": "CRASHED", "error": "chaos: nodo caído simulado"}
            return original(agent_id, caps, messages, working_mem)

        runner.wake_and_run = flaky
        try:
            for aid in agent_ids:
                result = self.loop.tick(aid, [])
                self.report_log.append({"agent": aid, "result": result})
        finally:
            runner.wake_and_run = original  # restaurar, nunca dejar el sistema en modo caos

    def recovery_rate(self) -> float:
        if not self.report_log:
            return 1.0
        ok = sum(1 for r in self.report_log if r["result"] and r["result"]["status"] == "TERMINATED")
        return ok / len(self.report_log)
