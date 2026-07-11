"""Scheduler (Sec.9): filtrar nodos válidos -> afinidad soft -> cola priorizada."""
import heapq, itertools

class Node:
    def __init__(self, node_id, cpu_total, mem_total):
        self.id, self.cpu_total, self.mem_total = node_id, cpu_total, mem_total
        self.cpu_used = self.mem_used = 0

    def has_room(self, cpu, mem):
        return self.cpu_used + cpu <= self.cpu_total and self.mem_used + mem <= self.mem_total

class Scheduler:
    def __init__(self, nodes: list[Node]):
        self.nodes = nodes
        self._affinity: dict[str, str] = {}   # agent_id -> último nodo (Sec.9, soft)
        self._placements: dict[str, tuple] = {}  # agent_id -> (node, cpu, mem), para poder liberar
        self._counter = itertools.count()
        self._queue = []                       # heap: (prioridad, seq, item)

    def enqueue(self, agent_id: str, cpu: float, mem: float, mode: str):
        priority = 0 if mode == "sync" else 1  # RPC primero (Sec.9)
        heapq.heappush(self._queue, (priority, next(self._counter), (agent_id, cpu, mem)))

    def _filter(self, cpu, mem):
        return [n for n in self.nodes if n.has_room(cpu, mem)]

    def _pick(self, agent_id, candidates):
        pref = self._affinity.get(agent_id)
        for n in candidates:
            if n.id == pref:
                return n  # cache hit (Sec.9)
        return max(candidates, key=lambda n: n.cpu_used, default=None)  # most-allocated packing

    def drain_one(self):
        if not self._queue:
            return None
        _, _, (agent_id, cpu, mem) = heapq.heappop(self._queue)
        candidates = self._filter(cpu, mem)
        if not candidates:
            return {"agent_id": agent_id, "status": "REJECTED_NO_CAPACITY"}

        node = self._pick(agent_id, candidates)
        node.cpu_used += cpu
        node.mem_used += mem
        self._affinity[agent_id] = node.id
        self._placements[agent_id] = (node, cpu, mem)
        return {"agent_id": agent_id, "status": "SCHEDULED", "node": node.id}

    def release(self, agent_id: str):
        """Libera recursos cuando el runtime serverless termina (Sec.8: TERMINATED/CRASHED).
        Sin esto, los nodos se llenan para siempre y el sistema rechaza todo con el tiempo."""
        placement = self._placements.pop(agent_id, None)
        if not placement:
            return
        node, cpu, mem = placement
        node.cpu_used = max(0, node.cpu_used - cpu)
        node.mem_used = max(0, node.mem_used - mem)
