"""
HyperCore AI - Fase 0: Control Plane mínimo
Agent DNA (spec) + máquina de estados de identidad (Sec. 8 del diseño)
"""
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone
import uuid


class AgentState(str, Enum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


# Transiciones legales — cualquier otra combinación es rechazada (Sec. 8: Agent State Machine)
VALID_TRANSITIONS = {
    AgentState.DRAFT: {AgentState.REGISTERED},
    AgentState.REGISTERED: {AgentState.ACTIVE},
    AgentState.ACTIVE: {AgentState.PAUSED, AgentState.DEPRECATED, AgentState.ARCHIVED},
    AgentState.PAUSED: {AgentState.ACTIVE, AgentState.ARCHIVED},
    AgentState.DEPRECATED: {AgentState.ARCHIVED},
    AgentState.ARCHIVED: set(),  # estado terminal, soft-delete (Sec. 8)
}


class InvalidTransition(Exception):
    pass


class BiosValidationError(Exception):
    """HyperCore BIOS (14.2): validación previa a REGISTERED."""
    pass


@dataclass
class AgentDNA:
    """Agent Spec / Agent DNA (Sec. 6, 14.1)."""
    name: str
    capabilities: list[str]
    token_budget_per_hour: int
    memory_namespace: str = ""
    version: str = "0.1.0"

    id: str = field(default_factory=lambda: f"agt_{uuid.uuid4().hex[:8]}")
    state: AgentState = AgentState.DRAFT
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        if not self.memory_namespace:
            self.memory_namespace = self.id

    def transition(self, target: AgentState):
        allowed = VALID_TRANSITIONS.get(self.state, set())
        if target not in allowed:
            raise InvalidTransition(
                f"No se puede pasar de {self.state} a {target}. "
                f"Transiciones válidas: {[s.value for s in allowed]}"
            )
        self.state = target
        self.updated_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self):
        d = self.__dict__.copy()
        d["state"] = self.state.value
        return d


def bios_validate(spec: dict) -> None:
    """
    HyperCore BIOS (Sec. 14.2) / Spec Compiler:
    validación estática antes de permitir DRAFT -> REGISTERED.
    Solo el operador humano aprueba capabilities válidas (decisión Sec. 7).
    """
    APPROVED_CAPABILITIES = {"researcher", "writer", "reviewer"}  # catálogo del operador

    if not spec.get("name"):
        raise BiosValidationError("El agente requiere 'name'")

    caps = spec.get("capabilities", [])
    if not caps:
        raise BiosValidationError("El agente requiere al menos una capability")

    invalid = set(caps) - APPROVED_CAPABILITIES
    if invalid:
        raise BiosValidationError(
            f"Capabilities no aprobadas por el operador: {invalid}. "
            f"Catálogo válido: {APPROVED_CAPABILITIES}"
        )

    budget = spec.get("token_budget_per_hour", 0)
    if budget <= 0:
        raise BiosValidationError("token_budget_per_hour debe ser > 0 (Cost Governor, Sec. 11)")
