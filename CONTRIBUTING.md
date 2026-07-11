# Contribuir a HyperCore AI

## Estructura del proyecto
Cada carpeta es un dominio funcional, no una fase de desarrollo:
`core/` identidad y lifecycle · `runtime/` ejecución serverless · `scheduler/`
placement y costo · `memory/` persistencia por capas · `communication/` bus y
permisos · `marketplace/` catálogo y versionado · `enterprise/` mejoras
opcionales · `database/` drivers reales · `production/` API + servidores.

## Antes de un PR
```bash
python3 run_all_tests.py   # debe quedar 5/5
python3 benchmark.py         # revisa que no haya regresión de rendimiento
```

## Estilo
Sin dependencias externas fuera de `requirements.txt` (que es solo para
`production/main_prod.py`). El resto del núcleo es stdlib puro a propósito.

## Principio no negociable
Fail-fast, fail-visible: ningún componente nuevo puede tomar decisiones
estructurales de forma autónoma sin que quede auditado y sea reversible por
un humano. Ver `docs/architecture.txt` Sec.2.
