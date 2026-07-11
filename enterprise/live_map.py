"""Live Architecture Map: vista consolidada sobre datos ya existentes (Scheduler+Registry+Bus), sin componente nuevo."""

def snapshot(store, scheduler, registry: dict, bus) -> dict:
    nodes = [{"id": n.id, "cpu_used": n.cpu_used, "cpu_total": n.cpu_total,
              "mem_used": n.mem_used, "mem_total": n.mem_total} for n in scheduler.nodes]

    agents = [{"id": a.id, "name": a.name, "state": a.state.value,
               "capabilities": a.capabilities, "pending_messages": bus.pending(a.id)}
              for a in store.list_all()]

    edges = [{"agent": aid, "node": scheduler._affinity.get(aid)}
             for aid in registry if aid in scheduler._affinity]

    return {"nodes": nodes, "agents": agents, "placements": edges}
