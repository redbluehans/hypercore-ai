# Política de Seguridad

## Reportar una vulnerabilidad
No abras un issue público. Envía el detalle a security@hypercore.ai (placeholder)
con: descripción, pasos de reproducción, impacto estimado. Respuesta en 72h.

## Alcance de seguridad ya implementado (prototipo)
- Permission Engine capability-based, deny-by-default (Sec.7)
- Auditoría con hash-chain verificable (Sec.18.4)
- Cost Governor con gate de dos fases, sin fugas de presupuesto (Sec.11)
- Secretos de vida corta vía .env, nunca hardcodeados en código

## Pendiente antes de producción con datos reales de clientes
Ver INFRA.md — atestación remota, cifrado por sobres (Shamir), eBPF fencing,
mTLS entre servicios. No activar sin necesidad real (evita sobre-ingeniería).
