# Skill: Informe de Coyuntura — Mantenimiento y Operación

> Actualizado 2026-08-14. Este skill es un resumen operativo de orientación
> rápida, **no la fuente de verdad** — para detalle de metodología/pesos/
> bandas de un indicador puntual, siempre confirmar contra `README.md`,
> `docs/adr/` (decisiones vigentes, inmutables) y los tests (`tests/*.py`
> fijan el comportamiento exacto). Los `docs/archivo/cinturon_*.md`/`.docx`
> (movidos ahí el 2026-07-12) son specs de diseño READ-ONLY (pre-implementación),
> no se mantienen — la app deployada y el código son la fuente de verdad operativa.

## Cuándo usar este skill

Cuando el usuario pide: correr el informe, actualizar datos de coyuntura,
agregar/recalibrar un indicador de un cinturón, entender cómo funciona un
colector o el motor de scoring, o diagnosticar por qué un dato está
desactualizado o un score no cierra.

---

## Los cuatro cinturones del tablero

| Cinturón | Motor de scoring | Script de tablas | Doc/ADR de referencia |
|---|---|---|---|
| Macro | ITCM (índice paramétrico 0-100, 6 dimensiones) | `scripts/itcm.py` | `docs/adr/0021`, `0022`, y la serie de ADRs de macro (0001-0010) |
| Gestión | ITCG (paramétrico, 5 dimensiones) | `scripts/itcg.py` | `docs/adr/0013`, `0021`, `0023` |
| Vida cotidiana | ITVC-B100 (índice rebaseado, 100 = prom. 4T-2023) | `scripts/itvc.py` | `docs/adr/0018`, `0024` |
| Política | ITCP (paramétrico, 5 dimensiones estilo Matus) | `scripts/itcp.py` | `docs/adr/0036`, `0037`, `0038` |

**Espíritu de época salió del tablero el 2026-08-14 (ADR-0205).** Tenía un solo
indicador y aun así pesaba 20% del global. `scripts/espiritu_epoca.py` se borró
junto con su paso del workflow nocturno; `indice_intencion_migratoria` ya no se
publica y su serie queda congelada en el archivo histórico. Ojo con dos cosas: el
**marco conceptual CIGOB-Matus sigue teniendo** ese cinturón (lo que se retiró es
la operacionalización, no la categoría), y la serie de `score_global` en BigQuery
tiene una **discontinuidad en esa fecha** — no se restateó hacia atrás, así que
toda comparación con ediciones previas tiene que decir de qué lado del cambio
está. Quedan restos inertes en el árbol (`output/cache/espiritu_epoca.json`,
`output/fichas/`, `__pycache__`): no son señal de que el cinturón siga vivo.

Los cuatro comparten el **motor paramétrico común**
`scripts/parametrica.py`: bandas por indicador (low exclusivo/high
inclusivo), **puntaje INTERPOLADO entre anclas** (no escalonado — ver
`docs/adr/0021`), renormalización de pesos ante indicadores faltantes,
overrides del analista con vencimiento (`data/<cinturon>/ajustes_*.json`).
Tensión del cinturón = `(100 − índice) / 10`.

El score global pondera los cuatro cinturones por **fase del mandato**. Los pesos
vigentes son los de `config.py` (`PESOS_FASE_TEMPRANA` /
`PESOS_FASE_CONSOLIDACION`) — leerlos ahí, no de memoria.

---

## Estructura real del proyecto (verificar con `ls scripts/` si cambió)

```
projects/informe_coyuntura/
  config.py                    ← pesos por fase del mandato
  scripts/
    macro.py / itcm.py         ← colector + tablas del cinturón macro
    politica.py / itcp.py      ← colector + tablas del cinturón político
    gestion.py / itcg.py       ← colector + tablas del cinturón gestión
    vida_cotidiana.py          ← puente legacy al orquestador
    vida_cotidiana/main.py     ← orquestador real (bcra, indec_series, utdt_icc,
                                  cafam, ciccra, snic, salud, trends)
    itvc.py                    ← tablas del cinturón vida cotidiana
    parametrica.py             ← motor común (bandas, interpolación, overrides)
    descargar_series.py        ← backfill histórico → output/series/*.csv
    generar_informe.py         ← arma output/informe.json + informe.md
    publicar.py                ← snapshot para la web (web/src/data/{informe,series}.json)
    validacion_externa.py      ← contraste con fuentes externas (ICC, EPU, etc.)
    sensibilidad.py            ← Monte Carlo de robustez → output/sensibilidad.json
    gate_calidad.py            ← gate G3/G6 que bloquea el snapshot si algo no cierra
    bigquery_export.py         ← espeja la corrida en BigQuery (aguas abajo, ADR-0180)
    ga4_dimensiones.py         ← sincroniza las dimensiones personalizadas de GA4
  data/<cinturon>/
    manuales.json              ← fallback de indicadores sin fuente automatizable
    ajustes_<sigla>.json       ← overrides del analista (con vencimiento)
  output/
    cache/<cinturon>.json      ← último fetch válido (fallback CI)
    informe.json / informe.md  ← reporte generado
    series/                    ← CSVs históricos
    sensibilidad.json
  docs/
    adr/                       ← decisiones de diseño/metodología (SE MANTIENE)
    archivo/cinturon_*.md      ← specs de diseño (READ-ONLY, no se mantienen)
    260523_proyecto_pais_estado_extraccion.md  ← panorama de indicadores/fuentes
  web/                          ← app Astro pública (lee web/src/data/*.json)
```

`output/` y `scripts/vida_cotidiana/data/` están **versionados a propósito**
(no son "ruido generado" descartable) — un colaborador debe tener el
reporte ya generado sin correr los colectores. El pipeline nocturno de CI
(`.github/workflows/data-pipeline.yml`, 00:00 ART) los regenera solo.

---

## Cómo correr el informe completo

**Dos preparaciones sin las cuales la corrida miente** (detalle en `CLAUDE.md`):

1. **No hay `python` pelado en esta Mac.** El venv es
   `projects/informe_coyuntura/.venv` (uv, Python 3.12). Los bloques de abajo
   llaman `.venv/bin/python` explícitamente; `source .venv/bin/activate` también
   sirve si preferís un `python` pelado.
2. **Exportar las credenciales**: `set -a; source ./.env; set +a`. Sin ellas los
   colectores fallan auth y **caen a caché en silencio**: la corrida termina, el
   gate pasa, y publicás datos de ayer creyendo que son frescos.

Cada paso lee lo que escribió el anterior — correrlos de a uno y esperar a que
termine, no lanzarlos en paralelo ni encadenarlos a ciegas.

```bash
cd projects/informe_coyuntura
.venv/bin/python scripts/macro.py
.venv/bin/python scripts/politica.py
.venv/bin/python scripts/gestion.py
.venv/bin/python scripts/vida_cotidiana/main.py
.venv/bin/python scripts/vida_cotidiana.py   # puente legacy — corre después de main.py
.venv/bin/python scripts/descargar_series.py
.venv/bin/python scripts/validacion_externa.py
.venv/bin/python scripts/generar_informe.py
.venv/bin/python scripts/publicar.py         # snapshot para la web
.venv/bin/python scripts/gate_calidad.py     # G1-G3/G6
.venv/bin/python -m pytest tests -q          # G4-G5 (gate_calidad pasando NO implica esto)
.venv/bin/python scripts/bigquery_export.py  # archivo histórico en BigQuery (ADR-0180)
```

El orden canónico es el de `.github/workflows/data-pipeline.yml` — si diverge,
gana el workflow.

El export a BigQuery lo hace solo el nocturno; **una corrida manual no**. Las
tablas de snapshot se acumulan por `generated_at`, así que la corrida que no se
sube ese día se pierde del archivo. Es idempotente.

**Y falta el último paso, que es el que importa: pushear a `main` y verificar la
URL de producción.** Ver "Terminar el trabajo" al final de este archivo.

Validar con lo más angosto posible en vez de correr todo:
`.venv/bin/python -m pytest tests/ -k <algo>`, o un colector individual si el
cambio es puntual.

### Exit codes de los colectores

| Código | Significado |
|---|---|
| 0 | Todos los indicadores del cinturón son datos frescos |
| 1 | Mezcla: algunos frescos, algunos del cache |
| 2 | Todos vienen del cache (fallo total de fuentes) |

---

## Diagnóstico rápido

| Síntoma | Causa probable | Dónde mirar |
|---|---|---|
| Dato desactualizado en output | Colector falló y usó cache | Correr el colector individual, ver el `[WARN]` en stdout |
| Score de un indicador parece "saturado" (siempre 100 o siempre 10) | Anclas de banda mal calibradas o punto fuera de rango real | `BANDAS_ITC*` del script de tablas del cinturón + buscar si hay un ADR de recalibración reciente |
| El snapshot publicado no cierra con el score esperado | `publicar.py` puede estar leyendo un `output/cache/*.json` desactualizado (no se re-corrió el colector después de un cambio de tablas/bandas) | Re-correr el colector del cinturón tocado ANTES de `publicar.py` |
| CKAN HCDN da 0 resultados con filtro exacto | `q=` es full-text por tokens, no substring; filtros con tildes fallan por encoding | Filtrar del lado Python con `.lower()` en vez de depender del filtro remoto |
| Sesión InfoLeg / Senado falla | Requiere GET inicial (jsessionid/cookies) antes del POST de búsqueda | Ver el patrón de sesión en `politica.py`/`gestion.py` (varios colectores lo comparten) |
| BCRA API error | Requiere `verify=False` + `urllib3.disable_warnings()`; datos en orden descendente | `detalle[0]` es el dato más reciente |
| `git push` a main rechazado | El pipeline nocturno (bot) ya commiteó | `git pull --rebase origin main`; conflictos típicos en `output/cache/*.json`/`informe.json` — local gana si tiene el cambio de código nuevo, remoto gana si es solo dato más fresco |

---

## Para agregar o recalibrar un indicador

1. Elegir el cinturón: los cuatro del tablero (macro/gestión/vida cotidiana/política) entran a su índice paramétrico (ITCM/ITCG/ITVC/ITCP).
2. Si es paramétrico: agregar/ajustar la banda en `BANDAS_ITC*` del script de tablas (`itcm.py`/`itcg.py`/`itvc.py`/`itcp.py`) — anclas con low exclusivo/high inclusivo, tramos extremos abiertos (`INF`/`-INF`) salvo que haya una razón explícita para uno finito.
3. Implementar `fetch_<indicador>()` en el colector del cinturón, agregarlo a `INDICADORES_ESPERADOS` y al diccionario de indicadores/dimensiones.
4. Escribir el test que fija el comportamiento (bandas + wiring) ANTES de dar por terminado — este proyecto es TDD estricto, ver cualquier `tests/test_itc*.py` como molde.
5. Si hay backfill posible, seguir el patrón de `descargar_series.py` (serie anual o mensual con caché persistente por período — ver `_serie_cohesion_cacheada` o el patrón de `alineamiento_senadores_prov` como ejemplo reciente de backfill mensual con ventana rolling).
6. Documentar la decisión como ADR nuevo en `docs/adr/` (numeración siguiente + entrada en `docs/adr/README.md`) — es obligatorio para toda decisión de metodología en este proyecto, no opcional.
7. Actualizar labels/unidades/descripciones/fichas en `web/src/lib/` (`datos.ts`, `descripciones.ts`, `fichas.ts`) si el indicador es nuevo o cambia de umbral — la web es pública y esos textos NO llevan números de ADR (decisión editorial).

---

## Terminar el trabajo: el entregable es la web, no el commit

El proyecto existe para mostrar datos en una página. **Un número que está en un
commit y no en la página no está entregado.** La cadena es completa o no vale:

    código → snapshot (`web/src/data/informe.json`) → `npm run build`
           → **push/merge a `main`** → deploy de Vercel
           → **abrir la URL de producción y LEER el número ahí**

- Vercel deploya **cada push a `main`**: `https://cigob-informe-coyuntura.vercel.app/`
  (con `?cb=<n>` para saltear caché). Las URL por-deploy `…-<hash>.vercel.app`
  tienen login-wall, así que no sirven para mostrarle nada al usuario.
- **Una rama de PR es invisible.** Si el usuario espera ver el cambio, hay que
  mergear a `main`. Si hay razón para no mergear, decirlo por adelantado y
  explícito ("queda en el PR, NO se ve en la web hasta mergear") — nunca reportar
  "pusheado" y dejar que lo descubra mirando una página igual.
- Verificar una capa intermedia no autoriza a decir "listo": que el valor esté en
  `output/validacion_externa.json`, o en el snapshot, o que el build pase, son
  todos pasos **necesarios e insuficientes**. Un valor puede calcularse y
  guardarse en el JSON intermedio mientras `publicar.py` nunca lo lleva a la
  página.
- PR largo = caro: el cron commitea snapshots generados a `main` todas las
  noches, así que una rama sin mergear acumula conflictos en
  `output/cache/*.json`, `output/series/*.csv` y `web/src/data/*.json`. Se
  resuelven tomando el dato fresco del cron y **re-corriendo el pipeline**, no
  eligiendo un lado a mano.

Falla verificada 30-jul-2026: una sesión entera de trabajo (pobreza al ITVC, dos
componentes saliendo, 10 URL de fichas rotas, el cambio de ancla de validación
del ITCM) se reportó commit por commit como "pusheado", toda sobre una rama de
PR. `main` no tenía nada y la web estaba idéntica.