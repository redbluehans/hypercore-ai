# Índice técnico — Arquitectura ↔ Código

Mapea cada componente del documento de arquitectura a su implementación y prueba.

| Sección del diseño | Componente | Código | Test |
|---|---|---|---|
| Sec.6, 14.1 | Agent DNA + máquina de estados | `agent.py` | `test_client.py` |
| Sec.3 | Control Plane (Store) | `store.py` | `test_client.py` |
| Sec.14.2 | HyperCore BIOS | `agent.py::bios_validate` | `test_client.py` |
| Sec.7, 8 | Event Bus (JetStream sim.) | `event_bus.py` | `test_fase1.py` |
| Sec.10 | Memory Plane (Working/Episodic) | `memory.py` | `test_fase1.py` |
| Sec.8, 13.1 | Agent Runner (serverless) | `runner.py` + `worker.py` | `test_fase1.py` |
| Sec.8 | Reconciliation Loop | `reconciliation.py` | `test_fase1.py` |
| Sec.18.4 | Hash-chain (Audit Log) | `memory.py::verify_chain` | `test_fase1.py`, `benchmark.py` |
| Sec.7 | Permission Engine (capability) | `permission.py` | `test_fase2.py` |
| Sec.7 | Comunicación auditada | `communication.py` | `test_fase2.py` |
| Sec.11 | Cost Governor (2 fases) | `cost_governor.py` | `test_fase3.py`, `benchmark.py` |
| Sec.9 | Scheduler (filtro+afinidad+cola) | `scheduler.py` | `test_fase3.py`, `benchmark.py` |
| Sec.21 | API pública + integración | `main_v2.py` | manual (`curl`) |
| — | Panel Web (3 vistas) | `panel.html` | manual (navegador) |
| Sec.6, Marketplace | Catálogo de Agent Images | `marketplace.py` | inline |
| Sec.14.5 | Shadow Execution | `shadow_execution.py` | inline |
| Sec.16.3 | DAG Workflow / Execution Planner | `dag_workflow.py` | `test_fase6.py` |
| — | Semantic Event Bus | `semantic_event_bus.py` | `test_fase6.py` |
| — | Chaos Testing Engine | `chaos_engine.py` | `test_fase6.py` |
| Sec.7 (extensión) | Policy Engine ABAC | `policy_abac.py` | `test_fase6.py` |
| — | Knowledge Graph | `knowledge_graph.py` | `test_fase6.py` |
| Sec.15.1 (vista) | Live Architecture Map | `live_map.py` | manual |
| — | Agent Reputation | `reputation.py` | `test_fase6.py` |
| — | Smart Cache Layer | `smart_cache.py` | `test_fase6.py` |

## Cómo correr todo
```bash
python3 run_all_tests.py   # 5 suites, ~1 segundo total
python3 benchmark.py        # throughput de operaciones críticas
```

## Última medición de rendimiento (referencia, no comprometida como SLA)
```
Memory.episodic_append (hash-chain)    ~217,000 ops/seg   (4.60 µs/op)
CostGovernor.preflight+postflight    ~2,370,000 ops/seg   (0.42 µs/op)
Scheduler.enqueue+drain_one            ~429,000 ops/seg   (2.33 µs/op)
```
Prototipo Python de un solo proceso. En Go+Postgres real (Sec.5), estos números
cambian — esto es piso de referencia para detectar regresiones, no promesa de producción.

## Qué NO tiene test automatizado todavía
API HTTP integrada (Fase 4) y Panel Web — requieren servidor vivo + navegador,
se validan manualmente por ahora (comandos `curl` en el README de esa fase).
