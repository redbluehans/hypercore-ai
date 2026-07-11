"""Cost Governor (Sec.11): pre-flight (reservar con max_tokens) -> post-flight (debitar costo real)."""

PRICE_PER_TOKEN = 0.000002  # ejemplo, USD

class BudgetExceeded(Exception):
    pass

class CostGovernor:
    def __init__(self):
        self._budget: dict[str, float] = {}      # agent_id -> USD disponible esta ventana
        self._reserved: dict[str, float] = {}     # agent_id -> USD reservados en vuelo

    def set_budget(self, agent_id: str, usd: float):
        self._budget[agent_id] = usd

    def available(self, agent_id: str) -> float:
        return self._budget.get(agent_id, 0) - self._reserved.get(agent_id, 0)

    def preflight(self, agent_id: str, max_tokens: int) -> float:
        """Fase 1: estima costo máximo, reserva, o rechaza (Sec.11)."""
        estimate = max_tokens * PRICE_PER_TOKEN
        if estimate > self.available(agent_id):
            raise BudgetExceeded(
                f"{agent_id}: estimate=${estimate:.4f} > disponible=${self.available(agent_id):.4f}"
            )
        self._reserved[agent_id] = self._reserved.get(agent_id, 0) + estimate
        return estimate

    def postflight(self, agent_id: str, reserved: float, real_tokens: int) -> float:
        """Fase 2: libera reserva, debita costo real (Sec.11)."""
        real_cost = real_tokens * PRICE_PER_TOKEN
        self._reserved[agent_id] -= reserved
        self._budget[agent_id] -= real_cost
        return real_cost
