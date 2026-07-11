"""Agent Reputation System: score derivado de Episodic Memory (éxitos, crashes, denies) ya existente."""

def compute_reputation(memory, agent_id: str) -> dict:
    log = memory.episodic_log(agent_id)
    if not log:
        return {"agent_id": agent_id, "score": None, "runs": 0}

    total = len(log)
    crashes = sum(1 for r in log if r["event"]["type"] == "runtime_crash")
    denies = sum(1 for r in log if r["event"]["type"] == "comm_attempt" and not r["event"].get("allowed", True))
    success = total - crashes

    # score simple 0-100: penaliza crashes fuerte, denies leve
    score = max(0, 100 - (crashes / total * 70) - (denies / total * 20)) if total else None

    return {"agent_id": agent_id, "score": round(score, 1) if score is not None else None,
            "runs": total, "crashes": crashes, "denies": denies, "success_rate": round(success / total, 2)}
