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

