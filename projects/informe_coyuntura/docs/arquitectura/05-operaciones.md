# 05 — Operaciones y deploy

Los workflows viven en la **raíz del repo padre** (`.github/workflows/`).

## Los dos workflows

### `data-pipeline.yml` — el nocturno (cron 03:00 UTC, ~medianoche AR)
La corrida completa sin manos:
1. Colectores de los cuatro cinturones (tolerantes a falla individual).
2. `generar_informe.py` (ensambla) → `descargar_series.py` (series + stores)
   → `validacion_externa.py` (store de validación) → `publicar.py` (scoring
   + snapshot).
3. **Gates de calidad** — si fallan, el run se corta acá y producción sigue
   sirviendo el snapshot anterior (que pasó su gate):
   - `gate_calidad.py` (G1 estructura · G2 frescura con tope por indicador y
     presupuesto de carry-forward ≤40% por cinturón · G3 invariante
     serie↔titular con excepciones declaradas · G6 cero jerga interna);
   - `pytest tests/ -q` (G4 reconciliación paramétrica de los cuatro índices y
     el score global · G5 la robustez Monte Carlo encierra el valor).
4. Commit del snapshot + caches + stores a `main` (bot). Por eso las
   sesiones de trabajo largas suelen terminar con un `git pull --rebase`
   contra lo que el bot commiteó a la madrugada. **Ese push es el que
   despliega**: el build lo hace Vercel, no el workflow.
5. `bigquery_export.py` espeja la corrida en el archivo histórico (ADR-0180).

Los topes de frescura del dato (`MAX_DIAS`) y del fetch (`DIAS_SIN_FETCH`) se
calibran en `config.py`, no en el gate: los comparte con `publicar.py`, que
marca `desactualizado` en el snapshot, y una política con dos dueños se
desincroniza en silencio. Las excepciones del G3 y los topes propios de la
serie (`G3B_MAX_DIAS`) siguen en la cabecera de `scripts/gate_calidad.py`; al
cambiar la semántica card/serie de un indicador (ej. pulso vs canasta),
declarar la excepción ahí con su motivo.

> **GitHub Pages se retiró en julio de 2026** y con él `pages.yml`. El sitio
> lo construye **Vercel** en cada push a `main` (Root Directory =
> `projects/informe_coyuntura/web`); no hay workflow de deploy en este repo.
> La URL de producción que se verifica está en el
> [README del proyecto](../../README.md#web-pública).

### `piquetes-poll.yml` — poll liviano (15:00 y 21:00 UTC)
Corre `piquetes_poll.py` (alertas de manifestaciones) sin la pipeline entera.

## Secrets (GitHub Actions)

`ACLED_USERNAME/PASSWORD`, `ACLED_UBA_USERNAME/PASSWORD`,
`BA_TRANSPORTE_*`, `PRESUPUESTO_ABIERTO_TOKEN`. En local viven en `.env`
(gitignored). Sin el token de Presupuesto Abierto existe el plan B por ZIPs
del repositorio del MECON (sin auth, pesado).

## Deploy y verificación — el ritual completo

1. Si se tocó la web, ejecutar un único build local con `npm run build`.
2. Commit **solo de archivos relevantes** + push a `main` (mensajes largos:
   `git commit -F` o here-string). Una rama de feature no despliega nada.
3. Esperar el deploy de Vercel del SHA que se acaba de pushear y confirmar
   que quedó READY; si falló, inspeccionar el log del build antes de
   decidir si corresponde corregir o reintentar.
4. **Verificar producción con marcadores ÚNICOS del cambio** (un texto o
   número que solo exista en la versión nueva). Lección documentada: buscar
   una fecha genérica dio falso positivo (matcheaba la fecha del REM).
   El CDN puede tardar unos minutos; cache-bust con `?cb=<random>`.

## Troubleshooting conocido

| Síntoma | Causa | Remedio |
|---|---|---|
| Indicador no se actualiza tras "regenerar" | `generar_informe.py` solo ensambla | correr el colector del cinturón primero |
| IdC en cero o viejo | rate-limit del BCRA (triple descarga) | memo `_IDC_BASE_MEMO` ya lo amortigua; reintentar |
| Serie de inseguridad/IVI/sentimiento vacía | host caído (cloud-snic) o 429 (Trends) | el store sirve la última buena; verificar `_meta.actualizado` |
| Matriz de validación "vieja" | réplica de `validacion_externa.py` desalineada de un ADR nuevo | actualizar `COMPONENTES`/`BASES_PROPIAS`/`ITVC_TECHO` y recorrer |
| Conflicto de rebase en `informe.json`/caches | commit nocturno del bot | `checkout --theirs` + regenerar con la cadena manual |
| Falla el deploy | error de build o infraestructura | inspeccionar el log del build de Vercel (o del workflow, si es el nocturno); corregir la causa o reintentar solo si es una falla transitoria confirmada |
| El nocturno cortó en "Gate de calidad" | el snapshot salió roto o viejo (el gate hizo su trabajo) | leer las líneas `[FALLA]` del log; producción quedó en el snapshot anterior, arreglar la causa y re-dispatchar |

## Convenciones de trabajo

- Al terminar una tarea: **commit + push a main** (deploy incluido) — el
  repo no acumula trabajo local.
- Tests verdes antes de push: `python -m pytest tests/ -q`.
- Cambios visuales: screenshot local (Playwright contra el build servido
  con MIME correcto) y comparación contra una card aprobada ANTES de
  pushear.
- Decisión metodológica nueva → ADR en `docs/adr/` + fila en su README +
  recalibrar tests con el engine.
