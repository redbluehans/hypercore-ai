"""Policy Engine (ABAC): capa sobre Permission Engine (Sec.7), no reemplazo. Añade atributos dinámicos."""
from permission import check as capability_check

class ABACDenied(Exception): pass

class ABACPolicyEngine:
    def __init__(self):
        self._rules: list[dict] = []  # {"attr": "risk_level", "op": "<=", "value": 5}

    def add_rule(self, attr: str, op: str, value):
        self._rules.append({"attr": attr, "op": op, "value": value})

    def _eval(self, rule, context: dict) -> bool:
        actual = context.get(rule["attr"])
        if actual is None:
            return False
        ops = {"<=": lambda a, v: a <= v, ">=": lambda a, v: a >= v,
               "==": lambda a, v: a == v, "!=": lambda a, v: a != v}
        return ops[rule["op"]](actual, rule["value"])

    def authorize(self, sender_caps: list[str], target_cap: str, mode: str, context: dict) -> bool:
        """Debe pasar capability check (base) Y todas las reglas ABAC (contexto)."""
        if not capability_check(sender_caps, target_cap, mode):
            raise ABACDenied(f"capability check falló: {sender_caps} -> {target_cap} ({mode})")
        for rule in self._rules:
            if not self._eval(rule, context):
                raise ABACDenied(f"regla ABAC falló: {rule} con contexto {context}")
        return True
