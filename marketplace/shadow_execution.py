"""Shadow Execution (Sec.14.5): nueva versión corre en paralelo (tráfico espejo), se compara, humano aprueba promoción."""

class ShadowExecution:
    def __init__(self, reconciliation_loop):
        self.loop = reconciliation_loop
        self._shadow_log: list[dict] = []

    def mirror_and_compare(self, live_id: str, shadow_id: str, messages: list[dict], live_caps, shadow_caps):
        """Ambas versiones procesan el mismo tráfico; solo la respuesta de 'live' se devuelve al usuario."""
        live_result = self.loop.tick(live_id, live_caps) or {"responses": []}
        shadow_result = self.loop.tick(shadow_id, shadow_caps) or {"responses": []}

        diff = live_result.get("responses") != shadow_result.get("responses")
        record = {"live": live_result, "shadow": shadow_result, "diverged": diff}
        self._shadow_log.append(record)
        return live_result  # el usuario solo ve la respuesta de la versión activa

    def report(self):
        total = len(self._shadow_log)
        diverged = sum(1 for r in self._shadow_log if r["diverged"])
        return {"total": total, "diverged": diverged,
                "agreement_rate": (total - diverged) / total if total else None}

    def promote(self, approved_by_human: bool):
        """Promoción de v_shadow a ACTIVE requiere aprobación explícita (Sec.2 fail-visible)."""
        if not approved_by_human:
            raise PermissionError("Promoción requiere aprobación humana explícita")
        return {"status": "PROMOTED"}
