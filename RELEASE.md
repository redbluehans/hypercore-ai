# Cómo publicar la primera Release en GitHub

Tras el push del código:
```bash
git tag -a v0.1.0-alpha -m "HyperCore AI v0.1.0-alpha: prototipo funcional probado"
git push origin v0.1.0-alpha
```
Luego en GitHub: Releases → "Draft a new release" → selecciona el tag `v0.1.0-alpha`
→ marca "Set as a pre-release" (es alpha, sé honesto en la UI también) → publica.

Notas sugeridas para la release (copiar de CHANGELOG.md sección [0.1.0-alpha]).
