# 09 — Onboarding: día uno de un colaborador

## Requisitos

- **Python 3.12** y **Node 20+** (las mismas versiones que usa CI).
- `gh` CLI autenticado (para mirar/relanzar deploys).
- Git con acceso al repo (privado; pedir invitación como colaborador).

## Setup

```bash
git clone <repo>            # el repo raíz "Analisis CIGOB"
cd "Analisis CIGOB/projects/informe_coyuntura"
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
cd web && npm install
```

⚠️ `xlrd==1.2.0` está pineado a propósito (el ICC de UTDT llega en `.xls`
OLE2; xlrd ≥2 no lo lee). No "actualizar" esa dependencia.

### Credenciales — `.env` en la raíz del repo (gitignored)

```bash
PRESUPUESTO_ABIERTO_TOKEN=   # API Presupuesto Abierto (TDPS); sin él hay plan B por ZIPs
ACLED_USERNAME=              # cuenta ACLED principal
ACLED_PASSWORD=
ACLED_UBA_USERNAME=          # cuenta académica UBA (sonda de upgrade)
ACLED_UBA_PASSWORD=
BA_TRANSPORTE_CLIENT_ID=     # API Transporte GCBA (alertas)
BA_TRANSPORTE_CLIENT_SECRET=
```

Los mismos nombres existen como secrets de GitHub Actions. Casi todo el
pipeline funciona SIN credenciales (fuentes públicas): sin `.env` van a
fallar solo TDPS en vivo, ACLED y alertas — y el carry-forward + stores
mantienen la web íntegra.

## La corrida completa a mano

```bash
cd projects/informe_coyuntura
.venv/bin/python scripts/macro.py                # colector (o el del cinturón que toque)
.venv/bin/python scripts/generar_informe.py      # ensambla (NO refresca colectores)
.venv/bin/python scripts/descargar_series.py     # series + stores resilientes
.venv/bin/python scripts/validacion_externa.py   # robustez pilar 3
.venv/bin/python scripts/publicar.py             # scoring + snapshot web/src/data
.venv/bin/python -m pytest tests/ -q             # verdes o no se pushea
```

## Ver la web local

```bash
cd web
npm run build      # sale a dist/ (base /)
npm run preview    # sirve dist/ con el MIME correcto
```

⚠️ No servir el build con `python -m http.server` pelado: en Windows sirve
`.js` como `text/plain` y los módulos mueren. `npm run preview` alcanza; si
hace falta un server propio, con MIME correcto:

```python
# srv.py — python srv.py, sirve dist/ en :8932
import http.server, functools
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory="dist")
h.extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                    ".js": "text/javascript", ".mjs": "text/javascript"}
http.server.HTTPServer(("", 8932), h).serve_forever()
```

Para screenshots de verificación visual se usa Playwright contra ese server
(los modales se capturan por elemento: `.cg-modal-card` o `#cg-modal-chart`).

## Flujo de trabajo

1. Cambio metodológico → **ADR primero** (`docs/adr/`, formato de los
   existentes). El índice del README y las relaciones inversas **no se
   escriben a mano**: los regenera `.venv/bin/python scripts/adr_coherencia.py`
   desde el frontmatter, y los manuales de cinturón,
   `.venv/bin/python scripts/manual_cinturon.py --todos`.
2. Código + tests recalibrados **con el engine** (nunca valores a mano).
3. Si toca la web: build + screenshot comparado contra una card aprobada.
4. Commit de archivos relevantes (nada de `git add -A`), push a `main`,
   verificar el deploy con un marcador único del cambio (ver
   [05 — Operaciones](05-operaciones.md)).
5. Texto público: registro institucional, cero jerga interna (ni "ADR-XXXX"
   ni IDs de serie en la web).

## Trampas conocidas del entorno

- El bot nocturno commitea a `main` a la madrugada: empezar el día con
  `git pull --rebase`; si hay conflicto en `informe.json`/caches →
  `checkout --theirs` y regenerar.
- OneDrive: el repo vive dentro de OneDrive; si un archivo aparece lockeado,
  esperar la sincronización.
- PowerShell 5.1: los here-strings `@"..."@` se comen backticks — para
  Python inline usar `@'...'@` (literal) o la shell Bash.
- `gh run watch` a veces engancha el run anterior — verificar por SHA.
