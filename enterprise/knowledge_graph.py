"""Knowledge Graph: relaciona conocimiento entre agentes (Semantic Memory compartida), no infraestructura."""
from collections import defaultdict

class KnowledgeGraph:
    def __init__(self):
        self._edges: list[tuple[str, str, str, float]] = []  # (origen, relación, destino, confianza)
        self._by_node: dict[str, list[int]] = defaultdict(list)

    def relate(self, source: str, relation: str, target: str, confidence: float = 1.0):
        idx = len(self._edges)
        self._edges.append((source, relation, target, confidence))
        self._by_node[source].append(idx)
        self._by_node[target].append(idx)

    def neighbors(self, node: str, min_confidence: float = 0.0) -> list[dict]:
        out = []
        for idx in self._by_node.get(node, []):
            s, r, t, c = self._edges[idx]
            if c >= min_confidence:
                out.append({"source": s, "relation": r, "target": t, "confidence": c})
        return out

    def path_exists(self, start: str, end: str) -> bool:
        seen, stack = {start}, [start]
        while stack:
            n = stack.pop()
            if n == end:
                return True
            for e in self.neighbors(n):
                nxt = e["target"] if e["source"] == n else e["source"]
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        return False
