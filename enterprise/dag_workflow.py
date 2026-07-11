"""DAG Workflow Engine: sobre el Global Resource Graph existente. Topological sort + fan-out paralelo."""
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

class CycleError(Exception): pass

class DAGWorkflow:
    def __init__(self):
        self._edges: dict[str, set[str]] = defaultdict(set)  # nodo -> dependientes
        self._indegree: dict[str, int] = defaultdict(int)
        self._nodes: set[str] = set()

    def add_step(self, step_id: str, depends_on: list[str] = None):
        self._nodes.add(step_id)
        for dep in (depends_on or []):
            if step_id not in self._edges[dep]:
                self._edges[dep].add(step_id)
                self._indegree[step_id] += 1
            self._nodes.add(dep)

    def _topo_layers(self) -> list[list[str]]:
        """Cada capa = nodos ejecutables en paralelo (Sec.16.3 Execution Planner)."""
        indeg = {n: self._indegree.get(n, 0) for n in self._nodes}
        layers, frontier = [], [n for n in self._nodes if indeg[n] == 0]
        visited = 0
        while frontier:
            layers.append(frontier)
            visited += len(frontier)
            nxt = []
            for n in frontier:
                for m in self._edges[n]:
                    indeg[m] -= 1
                    if indeg[m] == 0:
                        nxt.append(m)
            frontier = nxt
        if visited != len(self._nodes):
            raise CycleError("El workflow tiene un ciclo, no es un DAG válido")
        return layers

    def run(self, executor_fn, max_workers=4) -> dict:
        """executor_fn(step_id) -> resultado. Cada capa corre en paralelo, capas en orden."""
        results = {}
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            for layer in self._topo_layers():
                futs = {pool.submit(executor_fn, step): step for step in layer}
                for f in futs:
                    results[futs[f]] = f.result()
        return results
