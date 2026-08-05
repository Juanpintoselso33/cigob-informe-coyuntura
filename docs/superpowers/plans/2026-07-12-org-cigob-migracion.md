# Migración a organización `fundacion-cigob` — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar `biblitotecario-ai` con solo el Informe de Coyuntura, mudarlo
(renombrado) junto con `cigob-informe` a una organización de GitHub
`fundacion-cigob`, y sumar ahí a los colaboradores no técnicos.

**Architecture:** No hay código de aplicación nuevo — es limpieza de repo
(remover Votómetro/Bibliotecario IA preservando un fallback de datos),
edición de workflows/docs, y operaciones de GitHub (org, transfer, rename,
collaborators) vía `gh` CLI/API.

**Tech Stack:** git, GitHub CLI (`gh`), GitHub Actions (`pages.yml`), Python
(pytest para verificar que nada se rompió).

## Global Constraints

- Repo real hoy: `Juanpintoselso33/biblitotecario-ai` (privado). Repo de
  deploy del dominio: `Juanpintoselso33/cigob-informe` (privado, solo
  `gh-pages`, sin código fuente).
- `informe.cigob.org` está **en producción** (lanzamiento público
  agosto 2026) — cualquier paso que toque `cigob-informe` o el owner de
  `biblitotecario-ai` se verifica con `gh api repos/OWNER/cigob-informe/pages`
  (esperar siempre `"https_certificate":{"state":"approved"}` y
  `"cname":"informe.cigob.org"`) antes de darlo por bueno.
- `python -m pytest tests -q` y `python scripts/gate_calidad.py` (desde
  `projects/informe_coyuntura/`) son la validación estándar de este repo
  antes de pushear cualquier cambio que toque `scripts/`.
- Nombre de la org ya confirmado disponible: **`fundacion-cigob`**. Nombre
  nuevo del repo principal: **`cigob-informe-coyuntura`**.
- El indicador `votometro_ventaja_lla` del ITCP usa
  `https://cigob.github.io/Votometro/` como fuente primaria (cuenta
  `CiGob`, ajena a este repo — no tocar) y
  `projects/votometro/web/votometro.html` como fallback si la URL live
  falla. El fallback se preserva, movido dentro de `informe_coyuntura`.

---

### Task 1: Preservar el fallback del Votómetro y desacoplar `projects/votometro/`

**Files:**
- Move: `projects/votometro/web/votometro.html` → `projects/informe_coyuntura/data/politica/votometro_fallback.html`
- Modify: `projects/informe_coyuntura/scripts/politica.py:82-83`
- Delete: `projects/votometro/` (resto del árbol, tras el move de arriba)

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `VOTOMETRO_HTML` en `politica.py` apunta al nuevo path — Task 4
  lo verifica corriendo `politica.py` y la suite de tests.

- [ ] **Step 1: Mover el archivo preservando historial**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git mv projects/votometro/web/votometro.html projects/informe_coyuntura/data/politica/votometro_fallback.html
```

- [ ] **Step 2: Actualizar el path en `politica.py`**

En `projects/informe_coyuntura/scripts/politica.py`, reemplazar:

```python
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR.parent / "votometro" / "web" / "votometro.html"  # fallback local
```

por:

```python
VOTOMETRO_URL  = "https://cigob.github.io/Votometro/"  # Votómetro live (embebido en cigob.org/votometro)
VOTOMETRO_HTML = PROJECT_DIR / "data" / "politica" / "votometro_fallback.html"  # fallback local
```

- [ ] **Step 3: Verificar que el archivo movido existe donde el código lo espera**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python -c "from pathlib import Path; p = Path('data/politica/votometro_fallback.html'); print(p.resolve(), p.exists())"
```

Expected: imprime la ruta y `True`.

- [ ] **Step 4: Borrar el resto de `projects/votometro/`**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git rm -r projects/votometro
```

Expected: lista `projects/votometro/README.md`, `docs/...`,
`web/encuestas.json`, `web/.gitkeep`, `scripts/.gitkeep`, `output/.gitkeep`,
`docs/protocolo_actualizacion.md` como `deleted`. NO debe aparecer
`votometro.html` (ya se movió en el Step 1).

- [ ] **Step 5: Commit**

```bash
git add projects/informe_coyuntura/scripts/politica.py
git commit -m "refactor: mueve el fallback del Votómetro dentro de informe_coyuntura y saca projects/votometro/"
```

---

### Task 2: Remover Votómetro de la web pública y del pipeline de deploy

**Files:**
- Modify: `.github/workflows/pages.yml`
- Modify: `.gitignore`
- Modify: `web/index.html`
- Modify: `web/README.md`
- Delete: `scripts/actualizar_encuestas.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: nada (independiente de Task 1, pero se hace después para
  mantener los commits temáticos separados).
- Produces: nada que otra task consuma.

- [ ] **Step 1: Sacar el paso de copia de Votómetro en `pages.yml`**

En `.github/workflows/pages.yml`, eliminar estas líneas:

```yaml
      - name: Publicar Votómetro en la carpeta de deploy
        run: cp projects/votometro/web/votometro.html web/votometro.html
```

- [ ] **Step 2: Limpiar `.gitignore`**

Reemplazar:

```
# Build outputs que el CI regenera desde el código fuente versionado:
#   - web/informe/      → lo buildea Astro (pages.yml)
#   - web/votometro.html → lo copia el deploy desde projects/votometro/web/
#   - web-dominio/      → build del informe para informe.cigob.org (repo cigob-informe)
web/informe/
web/votometro.html
web-dominio/
```

por:

```
# Build outputs que el CI regenera desde el código fuente versionado:
#   - web/informe/      → lo buildea Astro (pages.yml)
#   - web-dominio/      → build del informe para informe.cigob.org (repo cigob-informe)
web/informe/
web-dominio/
```

- [ ] **Step 3: Sacar la card de Votómetro de `web/index.html`**

Eliminar este bloque completo (dentro de `.tools-grid`):

```html
      <a href="votometro.html" class="tool-card">
        <span class="tool-tag tag-electoral">Analisis Electoral</span>
        <h2>Votometro Argentina 2027</h2>
        <p>Agregador ponderado de encuestas presidenciales con simulacion Monte Carlo y proyeccion distrital.</p>
        <ul class="tool-features">
          <li>Ponderacion quintuple de encuestas</li>
          <li>10.000 simulaciones Monte Carlo</li>
          <li>Proyeccion en los 24 distritos</li>
          <li>Verificacion Art. 97-98 CN</li>
        </ul>
        <span class="tool-link">Abrir Votometro &rarr;</span>
      </a>

```

Y en el footer, reemplazar:

```html
    <span>&copy; 2026 Fundacion CIGOB &middot; </span>
    <a href="https://github.com/Juanpintoselso33/biblitotecario-ai" target="_blank">GitHub</a>
    <span> &middot; Colaboracion CIGOB + Redlines</span>
```

por (sin la mención a Redlines, que era específica de Votómetro; el link de
GitHub se actualiza en la Task 6 cuando el repo ya tenga owner nuevo):

```html
    <span>&copy; 2026 Fundacion CIGOB &middot; </span>
    <a href="https://github.com/Juanpintoselso33/biblitotecario-ai" target="_blank">GitHub</a>
```

- [ ] **Step 4: Actualizar `web/README.md`**

Reemplazar toda la tabla y sección de deploy:

```markdown
| Archivo / carpeta | Qué es | Versionado |
|---|---|---|
| `index.html` | Landing — índice de herramientas de análisis (linkea a las tres de abajo) | ✅ sí |
| `bibliotecario.html` | Prototipo del **Bibliotecario IA** (RAG sobre corpus CIGOB) | ✅ sí |
| `votometro.html` | Votómetro publicado | ❌ no — lo copia el CI desde `projects/votometro/web/votometro.html` en cada deploy |
| `informe/` | Build de la app Astro del Informe de Coyuntura | ❌ no — lo regenera el CI (`outDir`) |

> Los artefactos generados (`votometro.html`, `informe/`) están en `.gitignore`: se
> producen en el deploy, no se versionan, para evitar duplicados que se desincronicen.

## ⚠️ Estado del Bibliotecario IA

`bibliotecario.html` es un **prototipo en desarrollo — todavía no está funcional**.
La API key de Anthropic se ingresa en runtime y se guarda en `localStorage` del
navegador (no se versiona ninguna credencial). Ver el estado del proyecto en la nota
de viabilidad técnica antes de retomarlo.

## Cómo se arma el sitio (deploy)

`pages.yml` hace, en orden:

1. `npm ci && npm run build` en `projects/informe_coyuntura/web` → genera `web/informe/`.
2. Copia `projects/votometro/web/votometro.html` → `web/votometro.html`.
3. Sube toda la carpeta `web/` como artefacto de Pages.

Por eso al clonar verás `index.html`, `bibliotecario.html` y este README, pero **no**
`votometro.html` ni `informe/`: aparecen solo en el sitio publicado.
```

por:

```markdown
| Archivo / carpeta | Qué es | Versionado |
|---|---|---|
| `index.html` | Landing — índice de herramientas de análisis | ✅ sí |
| `informe/` | Build de la app Astro del Informe de Coyuntura | ❌ no — lo regenera el CI (`outDir`) |

> El artefacto generado (`informe/`) está en `.gitignore`: se produce en el
> deploy, no se versiona, para evitar duplicados que se desincronicen.

## Cómo se arma el sitio (deploy)

`pages.yml` hace, en orden:

1. `npm ci && npm run build` en `projects/informe_coyuntura/web` → genera `web/informe/`.
2. Sube toda la carpeta `web/` como artefacto de Pages.

Por eso al clonar verás `index.html` y este README, pero **no** `informe/`:
aparece solo en el sitio publicado.
```

(El Bibliotecario IA sale del todo en la Task 3 — este README ya queda sin
mencionarlo.)

- [ ] **Step 5: Borrar el script de actualización de encuestas**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git rm scripts/actualizar_encuestas.py
```

- [ ] **Step 6: Actualizar `README.md` raíz**

Quitar la fila de Votómetro de la tabla `## Proyectos`:

```markdown
| **Votómetro Argentina 2027** | Proyector electoral (Monte Carlo + fundamentals) en HTML estático | [`projects/votometro/`](projects/votometro/) |
```

Quitar la fila de `web/votometro.html` de la tabla `## Web pública`:

```markdown
| `web/votometro.html` | Espejo del Votómetro (fuente en `projects/votometro/`) |
```

Quitar la fila de `scripts/actualizar_encuestas.py` de `## Scripts de utilidad`:

```markdown
| `scripts/actualizar_encuestas.py` | Agrega una encuesta al Votómetro (dual-write a `projects/votometro/web/encuestas.json` y al HTML) |
```

En `## Estructura del repo`, quitar la línea `votometro/` del árbol:

```
└── projects/
    ├── informe_coyuntura/     # colectores + informe + web Astro (docs propios en projects/informe_coyuntura/docs/)
    └── votometro/             # proyector electoral HTML (docs propios en projects/votometro/docs/)
```

queda:

```
└── projects/
    └── informe_coyuntura/     # colectores + informe + web Astro (docs propios en projects/informe_coyuntura/docs/)
```

En `## Onboarding para colaboradores`, quitar el punto 3 (Votómetro) y
renumerar:

```markdown
2. Para trabajar sobre el **Informe de Coyuntura**, seguir su [`README`](projects/informe_coyuntura/) (Python + Astro).
3. Para el **Votómetro**, seguir su [`README`](projects/votometro/) (HTML estático, sin build).
```

queda:

```markdown
2. Para trabajar sobre el **Informe de Coyuntura**, seguir su [`README`](projects/informe_coyuntura/) (Python + Astro).
```

En la tabla `## Qué se versiona y qué no`, sacar `web/votometro.html` de la
fila "Regenerable":

```markdown
| ♻️ **Regenerable** | `node_modules/`, `__pycache__/`, `web/informe/`, `web/votometro.html` | Se reconstruyen desde el código/source versionado (`npm install`, `pip install`, build de CI) |
```

queda:

```markdown
| ♻️ **Regenerable** | `node_modules/`, `__pycache__/`, `web/informe/` | Se reconstruyen desde el código/source versionado (`npm install`, `pip install`, build de CI) |
```

- [ ] **Step 7: Commit**

```bash
git add .github/workflows/pages.yml .gitignore web/index.html web/README.md README.md
git commit -m "chore: da de baja el Votómetro público (repo + deploy + docs)"
```

---

### Task 3: Remover Bibliotecario IA

**Files:**
- Delete: `web/bibliotecario.html`
- Modify: `web/index.html`
- Modify: `README.md`

**Interfaces:** ninguna — independiente de las tasks anteriores.

- [ ] **Step 1: Borrar el prototipo**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git rm web/bibliotecario.html
```

- [ ] **Step 2: Sacar la card de `web/index.html`**

Eliminar este bloque completo:

```html
      <a href="bibliotecario.html" class="tool-card">
        <span class="tool-tag tag-ia">IA Documental</span>
        <h2>Bibliotecario IA</h2>
        <p>Consulta el corpus documental de CIGOB en lenguaje natural. Respuestas fundamentadas con citas de fuentes.</p>
        <ul class="tool-features">
          <li>RAG sobre documentos de CIGOB</li>
          <li>Citas automaticas por documento</li>
          <li>Responde sobre estrategia, IA y gestion</li>
          <li>Powered by Claude (Anthropic)</li>
        </ul>
        <span class="tool-link">Abrir Bibliotecario &rarr;</span>
      </a>

```

- [ ] **Step 3: Sacar la fila de `README.md` raíz**

Quitar de la tabla `## Web pública`:

```markdown
| `web/bibliotecario.html` | Prototipo del Bibliotecario IA (RAG sobre corpus CIGOB) — **en desarrollo, aún no funcional**; la API key se ingresa en runtime, no se versiona |
```

- [ ] **Step 4: Commit**

```bash
git add web/index.html README.md
git commit -m "chore: saca el prototipo Bibliotecario IA del repo"
```

---

### Task 4: Verificación de la limpieza (antes de tocar nada de GitHub)

**Files:** ninguno nuevo — solo corridas de verificación sobre lo hecho en
Tasks 1-3.

- [ ] **Step 1: Suite de tests de `informe_coyuntura`**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python -m pytest tests -q
```

Expected: todo en verde. Si algo de `test_itcp.py` o
`test_descargar_series_cohesion.py` falla, es señal de que el path nuevo de
`VOTOMETRO_HTML` rompió algo — no asumir que es un test flaky, revisar el
path del Step 3 de la Task 1.

- [ ] **Step 2: Correr el colector de política (scoped — un solo cinturón tocado)**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB\projects\informe_coyuntura"
python scripts/politica.py
```

Expected: exit code 0 o 1 (fresh o mixed cache — ambos ok). Revisar en el
output que `votometro_ventaja_lla` no aparezca con warning de "archivo no
encontrado" — si `_cargar_votometro_html()` cae al fallback, tiene que
poder leer el archivo nuevo sin error.

- [ ] **Step 3: Confirmar que no queda ninguna referencia colgante**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
grep -rn "projects/votometro\|web/votometro.html\|web/bibliotecario.html\|actualizar_encuestas" --include="*.yml" --include="*.md" --include="*.html" --include="*.py" .
```

Expected: sin resultados (o resultados dentro de `docs/superpowers/` /
`backup/`, que están gitignored y no importan).

- [ ] **Step 4: Push**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git status --short
git pull --rebase
git push
```

---

### Task 5 (MANUAL — bloqueante, no automatizable): crear la organización

GitHub no tiene API pública para crear una organización nueva en una cuenta
personal (no-Enterprise) — es un paso exclusivo de la web. **Lo tiene que
hacer el usuario, no es ejecutable desde acá.**

- [ ] Ir a https://github.com/organizations/new
- [ ] Elegir plan **Free**
- [ ] Nombre de la organización: `fundacion-cigob`
- [ ] Completar el resto del wizard (email de contacto, etc.)
- [ ] Confirmar en el chat cuando esté creada, para retomar con la Task 6

---

### Task 6: Transferir y renombrar los repos a la organización

**Requiere que la Task 5 esté hecha.** Cada comando de transferencia es
difícil de deshacer (cambia el owner del repo) — **ejecutar solo tras
confirmación explícita del usuario en el momento**, no como parte de un
batch automático.

**Files:**
- Modify: `.github/workflows/pages.yml` (línea `external_repository`)
- Modify: `README.md`, `web/index.html`, `web/README.md` (URLs con el owner
  viejo)

- [ ] **Step 1: Transferir + renombrar el repo principal**

```bash
gh api repos/Juanpintoselso33/biblitotecario-ai/transfer -X POST \
  -f new_owner=fundacion-cigob \
  -f new_name=cigob-informe-coyuntura
```

Expected: JSON de respuesta con `"full_name":"fundacion-cigob/cigob-informe-coyuntura"`.

- [ ] **Step 2: Transferir el repo de deploy del dominio**

```bash
gh api repos/Juanpintoselso33/cigob-informe/transfer -X POST \
  -f new_owner=fundacion-cigob
```

Expected: JSON con `"full_name":"fundacion-cigob/cigob-informe"`.

- [ ] **Step 3: Verificar que el dominio custom sigue sirviendo con cert válido**

```bash
gh api repos/fundacion-cigob/cigob-informe/pages
```

Expected: `"cname":"informe.cigob.org"`,
`"https_certificate":{"state":"approved", ...}`, `"https_enforced":true` —
igual que antes de la transferencia. Si el estado cambió (ej.
`"pending_domain_unverified_at"` con valor, o `state` distinto de
`approved`), NO seguir — el DNS/cert necesita re-verificarse (ya pasó una
vez, ver historial del proyecto) y hay que resolverlo antes de la Task 7.

- [ ] **Step 4: Actualizar el remote local**

```bash
cd "C:\Users\trico\OneDrive\UBA\Analisis CIGOB"
git remote set-url origin https://github.com/fundacion-cigob/cigob-informe-coyuntura.git
git remote -v
```

Expected: `origin` apunta a la URL nueva (fetch y push).

- [ ] **Step 5: Actualizar el owner en `pages.yml`**

En `.github/workflows/pages.yml`, reemplazar:

```yaml
          external_repository: Juanpintoselso33/cigob-informe
```

por:

```yaml
          external_repository: fundacion-cigob/cigob-informe
```

- [ ] **Step 6: Actualizar URLs hardcodeadas de GitHub**

En `README.md` raíz, reemplazar todas las ocurrencias de
`https://github.com/Juanpintoselso33/biblitotecario-ai` (clone URL, link de
Pages) por `https://github.com/fundacion-cigob/cigob-informe-coyuntura`, y
`https://juanpintoselso33.github.io/biblitotecario-ai/` por la URL de Pages
nueva (confirmarla primero con `gh api repos/fundacion-cigob/cigob-informe-coyuntura/pages -q .html_url`).

En `web/index.html` (footer) y `web/README.md` (línea "URL:"), mismo
reemplazo de owner/URL.

- [ ] **Step 7: Commit y push**

```bash
git add .github/workflows/pages.yml README.md web/index.html web/README.md
git commit -m "chore: actualiza referencias al repo tras la migración a fundacion-cigob"
git push
```

- [ ] **Step 8: Disparar y verificar los workflows en el repo nuevo**

```bash
gh workflow run pages.yml --repo fundacion-cigob/cigob-informe-coyuntura
gh run list --repo fundacion-cigob/cigob-informe-coyuntura --limit 3
```

Esperar a que termine (`gh run watch <run-id> --repo fundacion-cigob/cigob-informe-coyuntura`)
y confirmar `completed`/`success`. Después:

```bash
gh api repos/fundacion-cigob/cigob-informe/pages -q '.https_certificate.state, .cname'
```

Expected: `approved`, `informe.cigob.org` — el sitio en producción no se
rompió.

- [ ] **Step 9: Verificar que el pipeline nocturno sigue teniendo permisos**

No se puede forzar el cron, pero sí confirmar que el workflow existe y está
activo en el repo nuevo:

```bash
gh workflow list --repo fundacion-cigob/cigob-informe-coyuntura
```

Expected: `data-pipeline.yml` y `pages.yml` aparecen como `active`. Avisar
al usuario para que revise el resultado del próximo cron (00:00 ART) — si
falla por permisos, el fix es re-chequear
`Settings → Actions → General → Workflow permissions` en el repo dentro de
la org (a veces una org nueva trae defaults más restrictivos que una cuenta
personal).

---

### Task 7: Sumar a los colaboradores no técnicos

**Requiere que la Task 6 esté confirmada como estable** (sitio andando,
pipeline corrido al menos una vez sin error) **y los usuarios de GitHub de
cada colaborador** (pedírselos al usuario si no los tengo).

**Files:**
- Modify: `docs/onboarding_colaboradores.md`

- [ ] **Step 1: Actualizar la guía con el repo/org nuevos**

En `docs/onboarding_colaboradores.md`, reemplazar toda referencia a
`biblitotecario-ai` por `fundacion-cigob/cigob-informe-coyuntura` (el paso
de invitación, el nombre del repo a elegir en el conector).

- [ ] **Step 2: Agregar cada colaborador con rol Read**

Por cada `<username>` que dé el usuario:

```bash
gh api repos/fundacion-cigob/cigob-informe-coyuntura/collaborators/<username> -X PUT -f permission=pull
```

Expected: `204 No Content` (invitación enviada) o `201` si ya la aceptó
directo.

- [ ] **Step 3: Commit y push de la guía actualizada**

```bash
git add docs/onboarding_colaboradores.md
git commit -m "docs: actualiza la guía de onboarding con el repo de la organización"
git push
```

---

## Self-review

- **Cobertura del spec:** org (Task 5), rename+transfer de ambos repos
  (Task 6), limpieza Votómetro/Bibliotecario preservando el fallback ITCP
  (Tasks 1-3), colaboradores no técnicos (Task 7, reusa el mecanismo ya
  diseñado en el spec anterior). Sin gaps.
- **Placeholders:** ninguno — todos los `<username>` son inputs explícitos
  a pedir en el momento, no "TBD".
- **Bloqueos explícitos:** Task 5 (manual, sin API), Task 6 Step 1-2
  (requiere confirmación en vivo antes de correr, es una operación
  destructiva sobre el owner del repo), Task 7 (requiere usernames reales).
