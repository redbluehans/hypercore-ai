# Changelog

## [0.1.0-alpha] - 2026-07-11
### Added
- Control Plane con Agent DNA y máquina de estados formal (core/)
- Runtime serverless (wake-on-message) con checkpoint (runtime/)
- Memory Plane en 3 capas con hash-chain verificable (memory/)
- Permission Engine capability-based + comunicación auditada (communication/)
- Cost Governor de 2 fases + Scheduler con afinidad y prioridad (scheduler/)
- API pública + Panel Web (production/)
- Marketplace + Shadow Execution (marketplace/)
- 8 mejoras: DAG Workflow, Semantic Event Bus, Chaos Engine, Policy ABAC,
  Knowledge Graph, Live Map, Reputation, Smart Cache (enterprise/)
- Persistencia real: SQLite (database/db.py) y Postgres+NATS (database/db_postgres.py,
  communication/event_bus_nats.py, sin probar en runtime — falta entorno con red)
- Suite de tests (5/5) y benchmark de throughput

### Fixed
- Scheduler no liberaba CPU/RAM tras terminar un runtime (fuga de capacidad
  en el modelo serverless) — agregado `Scheduler.release()`

### Known limitations
Ver `docs/roadmap-enterprise.md` — Wasm, Firecracker, Raft, TPM, cifrado
Shamir no implementados, solo diseñados.
