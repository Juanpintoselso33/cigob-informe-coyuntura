# 05 — Operaciones y deploy

Los workflows viven en la **raíz del repo padre** (`.github/workflows/`).

## Los tres workflows

### `data-pipeline.yml` — el nocturno (cron 03:00 UTC, ~medianoche AR)
La corrida completa sin manos:
1. Colectores de los cinco cinturones (tolerantes a falla individual).
2. `generar_informe.py` (ensambla) → `descargar_series.py` (series + stores)
   → `validacion_externa.py` (store de validación) → `publicar.py` (scoring
   + snapshot).
3. **Gates de calidad** — si fallan, el run se corta acá y producción sigue
   sirviendo el snapshot anterior (que pasó su gate):
   - `gate_calidad.py` (G1 estructura · G2 frescura con tope por indicador y
     presupuesto de carry-forward ≤40% por cinturón · G3 invariante
     serie↔titular con excepciones declaradas · G6 cero jerga interna);
   - `pytest tests/ -q` (G4 reconciliación paramétrica de los tres índices y
     el score global · G5 la robustez Monte Carlo encierra el valor).
4. Build Astro doble: default (`/informe`) y `DEPLOY_TARGET=dominio`
   (base `/`) → push del build del dominio al repo `cigob-informe`
   (cname informe.cigob.org).
5. Commit del snapshot + caches + stores a `main` (bot). Por eso las
   sesiones de trabajo largas suelen terminar con un `git pull --rebase`
   contra lo que el bot commiteó a la madrugada.

Los topes de frescura y las excepciones del G3 se calibran en
`scripts/gate_calidad.py` (cabecera del archivo); al cambiar la semántica
card/serie de un indicador (ej. pulso vs canasta), declarar la excepción ahí
con su motivo.

### `pages.yml` — deploy on-push
En cada push a `main`: build dual + Votómetro, publica a GitHub Pages del
repo y al repo del dominio (`external_repository: Juanpintoselso33/cigob-informe`).

### `piquetes-poll.yml` — poll liviano (15:00 y 21:00 UTC)
Corre `piquetes_poll.py` (alertas de manifestaciones) sin la pipeline entera.

## Secrets (GitHub Actions)

`ACLED_USERNAME/PASSWORD`, `ACLED_UBA_USERNAME/PASSWORD`,
`BA_TRANSPORTE_*`, `PRESUPUESTO_ABIERTO_TOKEN`. En local viven en `.env`
(gitignored). Sin el token de Presupuesto Abierto existe el plan B por ZIPs
del repositorio del MECON (sin auth, pesado).

## Deploy y verificación — el ritual completo

1. Build local dual si se tocó la web (`DEPLOY_TARGET=dominio` y default).
2. Commit **solo de archivos relevantes** + push a `main` (mensajes largos:
   `git commit -F` o here-string).
3. `gh run watch` del "Deploy to GitHub Pages" — ojo: a veces engancha el run
   anterior; verificar por SHA.
4. El repo `cigob-informe` corre su "Publish Pages". Falla frecuente:
   **"Deployment failed, try again later"** — es transitorio de GitHub, se
   resuelve con `gh run rerun` (a veces pega en los dos repos a la vez).
5. **Verificar producción con marcadores ÚNICOS del cambio** (un texto o
   número que solo exista en la versión nueva). Lección documentada: buscar
   una fecha genérica dio falso positivo (matcheaba la fecha del REM).
   El CDN puede tardar unos minutos; cache-bust con `?cb=<random>`.
6. Si Pages queda colgado: commit trivial a `gh-pages` lo destraba
   (el destrabador ya está horneado en los workflows).

## Troubleshooting conocido

| Síntoma | Causa | Remedio |
|---|---|---|
| Indicador no se actualiza tras "regenerar" | `generar_informe.py` solo ensambla | correr el colector del cinturón primero |
| IdC en cero o viejo | rate-limit del BCRA (triple descarga) | memo `_IDC_BASE_MEMO` ya lo amortigua; reintentar |
| Serie de inseguridad/IVI/sentimiento vacía | host caído (cloud-snic) o 429 (Trends) | el store sirve la última buena; verificar `_meta.actualizado` |
| Matriz de validación "vieja" | réplica de `validacion_externa.py` desalineada de un ADR nuevo | actualizar `COMPONENTES`/`BASES_PROPIAS`/`ITVC_TECHO` y recorrer |
| Conflicto de rebase en `informe.json`/caches | commit nocturno del bot | `checkout --theirs` + regenerar con la cadena manual |
| Pages "Deployment failed, try again later" | transitorio GitHub | `gh run rerun`, esperar CDN |
| El nocturno cortó en "Gate de calidad" | el snapshot salió roto o viejo (el gate hizo su trabajo) | leer las líneas `[FALLA]` del log; producción quedó en el snapshot anterior, arreglar la causa y re-dispatchar |

## Convenciones de trabajo

- Al terminar una tarea: **commit + push a main** (deploy incluido) — el
  repo no acumula trabajo local.
- Tests verdes antes de push: `python -m pytest tests/ -q` (40).
- Cambios visuales: screenshot local (Playwright contra el build del
  dominio servido con MIME correcto) y comparación contra una card aprobada
  ANTES de pushear.
- Decisión metodológica nueva → ADR en `docs/adr/` + fila en su README +
  recalibrar tests con el engine.
