"""Smart Cache Layer: cache por hash de input, evita re-pagar al Cost Governor por queries repetidas."""
import hashlib, json, time

class SmartCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[float, dict]] = {}
        self.ttl = ttl_seconds
        self.hits = self.misses = 0

    def _key(self, agent_id: str, input_payload: dict) -> str:
        raw = json.dumps({"agent": agent_id, "input": input_payload}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, agent_id: str, input_payload: dict):
        k = self._key(agent_id, input_payload)
        entry = self._store.get(k)
        if entry and (time.time() - entry[0]) < self.ttl:
            self.hits += 1
            return entry[1]
        self.misses += 1
        return None

    def set(self, agent_id: str, input_payload: dict, result: dict):
        self._store[self._key(agent_id, input_payload)] = (time.time(), result)

    def stats(self) -> dict:
        total = self.hits + self.misses
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": round(self.hits / total, 2) if total else None}
