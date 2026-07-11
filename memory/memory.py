"""Memory Plane (Sec.10) - Fase 1: Working + Episodic. Semantic llega en Fase 3."""
import hashlib, json, time

class MemoryPlane:
    def __init__(self):
        self._working: dict[str, dict] = {}          # namespace -> contexto vivo (Redis en prod)
        self._episodic: dict[str, list[dict]] = {}    # namespace -> log inmutable (Postgres en prod)

    def working_get(self, ns): return self._working.get(ns, {})
    def working_set(self, ns, data): self._working[ns] = data
    def working_clear(self, ns): self._working.pop(ns, None)  # checkpoint al dormir (Sec.8)

    def episodic_append(self, ns: str, event: dict):
        log = self._episodic.setdefault(ns, [])
        prev_hash = log[-1]["hash"] if log else "0" * 64
        record = {"ts": time.time(), "event": event}
        record["hash"] = hashlib.sha256((json.dumps(record["event"], sort_keys=True) + prev_hash).encode()).hexdigest()
        record["prev_hash"] = prev_hash
        log.append(record)  # hash-chain (Sec.18.4)

    def episodic_log(self, ns): return self._episodic.get(ns, [])

    def verify_chain(self, ns: str) -> bool:
        """Detecta manipulación del historial (Sec.18.4)."""
        log = self._episodic.get(ns, [])
        prev = "0" * 64
        for r in log:
            expected = hashlib.sha256((json.dumps(r["event"], sort_keys=True) + prev).encode()).hexdigest()
            if expected != r["hash"]:
                return False
            prev = r["hash"]
        return True
