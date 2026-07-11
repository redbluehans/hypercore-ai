"""Permission Engine (Sec.7): capability-based, no por par de agentes. Solo operador define la matriz."""

# policy_matrix[origen][destino] = modos permitidos
POLICY_MATRIX = {
    "researcher": {"writer": {"async", "sync"}},
    "writer": {"reviewer": {"sync"}},
    # reviewer -> * : nada definido = deny-by-default
}

class PermissionDenied(Exception):
    pass

def check(sender_caps: list[str], target_cap: str, mode: str) -> bool:
    """True si algún capability del emisor tiene permiso hacia target_cap en ese modo."""
    for cap in sender_caps:
        if mode in POLICY_MATRIX.get(cap, {}).get(target_cap, set()):
            return True
    return False
