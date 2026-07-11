# HyperCore AI — Infraestructura

## Estado actual (prototipo, fases 0-5 parcial)
Python stdlib, sin dependencias externas, corre en un solo proceso. Sirvió para
validar el modelo de datos, la máquina de estados, permisos, costo y scheduling
end-to-end (ver `test_faseN.py` en cada carpeta).

## Despliegue ligero (siguiente paso real)
```
docker compose up -d
```
Levanta: Control Plane, Postgres+pgvector (Episodic/Semantic), Redis (Working),
NATS JetStream (Event Bus), OTel Collector (Observability). Límites de CPU/RAM
ya declarados en `docker-compose.yml` — el gate de recursos es real desde el día 1,
no solo lógico en código.

## Ruta a "nunca visto" (enterprise, Sec.13-20 del documento de arquitectura)
No se simulan aquí porque requieren hardware/infraestructura real:

| Pieza | Qué necesita | Cuándo activarla |
|---|---|---|
| Wasm runtime | Wasmtime/Wasmer + recompilar agentes ligeros | Cuando el volumen de agentes simples justifique la densidad extra |
| Firecracker | Host con KVM, no funciona en la mayoría de laptops/CI | Al mover a servidores dedicados/bare-metal |
| Consensus Engine (Raft) | 3+ nodos de Control Plane, etcd | Al necesitar HA real (>1 región o SLA alto) |
| Atestación remota (TPM) | Instancias con vTPM (AWS Nitro, Azure Confidential VMs) | Requisito de cliente enterprise con compliance estricto |
| Cifrado Shamir + envelope | Vault o KMS del cloud provider | Antes de manejar datos sensibles de clientes reales |
| eBPF fencing | Kernel Linux con soporte, Cilium | Junto con la migración a Firecracker/gVisor |

**Regla:** cada fila de esta tabla es cara de operar y mantener. No se activa
"porque se puede" — se activa cuando hay una necesidad de cliente concreta que
la justifique. Activarlas todas de entrada sin necesidad real es sobre-ingeniería,
no "nivel enterprise".

## Seguridad ligera ya aplicable hoy (sin hardware especial)
- mTLS entre servicios vía certificados propios (no requiere TPM)
- Secrets de corta duración (Sec.17.3) vía variables de entorno + rotación manual,
  migrar a Vault cuando haya más de un cliente
- Rate limiting básico en el API gateway (nginx/Traefik delante del Control Plane)
