# Votómetro Argentina 2027

HTML estático puro para proyección electoral. Colaboración CIGOB + Redlines Estrategia y Comunicación.

## Archivos

| Archivo | Descripción |
|---|---|
| `web/votometro.html` | Versión activa — editar aquí |

El archivo canónico (datos inline + datos en `encuestas.json` espejo) vive en
`projects/votometro/web/`.

## Cómo actualizar encuestas

**Opción A — script (recomendado).** Desde la raíz del repo:

```bash
python scripts/actualizar_encuestas.py            # modo interactivo
python scripts/actualizar_encuestas.py nueva.csv  # desde CSV
python scripts/actualizar_encuestas.py nueva.json # desde JSON
```

Hace _dual-write_: actualiza `projects/votometro/web/encuestas.json` y parcha el
array `encuestasRaw` dentro de `projects/votometro/web/votometro.html` (con backup
automático `.bak` y rollback si el parcheo falla).

**Opción B — manual.** Editar el array `encuestasRaw` (al inicio del `<script>`, ~línea 1169)
en `projects/votometro/web/votometro.html`.

## Deploy

GitHub Pages: `https://juanpintoselso33.github.io/biblitotecario-ai/`

Workflow: editar → commit → push `main` → deploy automático.

## Metodología

- Ponderación quíntuple: decaimiento temporal (λ=0.015) × calidad consultora × sesgo histórico × orientación del medio × metodología
- Monte Carlo: 10.000 simulaciones con σ=6.5 calibrado al error histórico argentino
- Corrección de voto oculto bayesiana
- Verificación Arts. 97-98 CN en cada simulación
- Prior de fundamentals con blend dinámico encuestas × prior estructural
