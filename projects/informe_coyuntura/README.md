# Monitor del Plan de Gobierno

Colectores de datos para los cuatro cinturones publicados del marco CIGOB-Matus (Macro, Política, Impacto Social y Gestión) y generador del informe periódico. Espíritu de Época salió del tablero el 14 de agosto de 2026.

## Estado actual (agosto 2026)

| Cinturón | Indicadores publicados | Automáticos | Semiautomáticos | Carga manual |
|---|---:|---:|---:|---:|
| Impacto Social | 18 | 18 | 0 | 0 |
| Macro | 17 | 17 | 0 | 0 |
| Política | 18 | 14 | 3 | 1 |
| Gestión | 14 | 10 | 3 | 1 |

Los cuatro cinturones se puntúan con índices paramétricos de dimensiones ponderadas
(**ITCM**, diseño original en `docs/archivo/cinturon_macro.md` — superado por los
ADRs 0009/0010/0021/0022/0053/0055, versión vigente en `scripts/itcm.py`, y **ITCG**, 5
dimensiones 35/25/15/15/10 del
doc 260702 — ver `docs/adr/0013-itcg-parametrica-gestion.md`; motor común en
`scripts/parametrica.py`). ITCM, ITCP e ITCG usan una escala 0–100; el ITCIS es
base 100 = 4T-2023. El score global pondera los cuatro cinturones por fase del
mandato (`config.py`: fase temprana 25% parejo; consolidación 29/29/24/18).

Detalle por indicador —qué mide, fuente, transformaciones, límites—: las fichas
metodológicas de [`output/fichas/`](output/fichas), que `scripts/fichas/generar.py`
regenera desde `web/src/lib/fichas.ts` y el snapshot. El relevamiento fundacional de
fuentes, [`docs/260523_proyecto_pais_estado_extraccion.md`](docs/260523_proyecto_pais_estado_extraccion.md),
describe el estado a mayo de 2026 y se conserva como histórico.

**Documentación de arquitectura** (cómo funciona el sistema de punta a punta —
pipeline, motor paramétrico, web, operaciones): [`docs/arquitectura/`](docs/arquitectura/README.md).
Las decisiones de diseño y metodología están en [`docs/adr/`](docs/adr/README.md).

## Instalación

```bash
git clone https://github.com/Fundacion-CIGOB/cigob-informe-coyuntura.git
cd cigob-informe-coyuntura/projects/informe_coyuntura
uv venv --python 3.12
uv pip install --python .venv/bin/python -r requirements.txt
```

Para el orquestador completo de vida cotidiana:

```bash
uv pip install --python .venv/bin/python -r scripts/vida_cotidiana/requirements.txt
```

## Ejecución de los colectores

Desde la carpeta `projects/informe_coyuntura/`:

```bash
.venv/bin/python scripts/macro.py
.venv/bin/python scripts/politica.py
.venv/bin/python scripts/gestion.py
.venv/bin/python scripts/vida_cotidiana/main.py
.venv/bin/python scripts/vida_cotidiana.py   # puente legacy, después de main.py
```

Cada colector corre de forma independiente. No es necesario correrlos todos.

## Generación del informe

```bash
.venv/bin/python scripts/generar_informe.py
```

## Web pública

La página pública del informe vive en `web/` (app Astro) y se publica en
`https://cigob-informe-coyuntura.vercel.app/`. Replica el
observatorio de klipea (CSS propio de CIGOB) y se alimenta del snapshot de datos.

Ciclo de actualización:

```bash
# 1. correr los colectores y regenerar el informe
.venv/bin/python scripts/generar_informe.py
# 2. armar el snapshot que consume la web (web/src/data/{informe,series}.json)
.venv/bin/python scripts/publicar.py
# 3. (opcional) previsualizar local
cd web && npm install && npm run build && npm run preview
# 4. commit del snapshot + push a main → Vercel buildea y deploya
# 5. espejar la corrida en el archivo histórico de BigQuery (ADR-0180)
.venv/bin/python scripts/bigquery_export.py
```

El paso 5 lo hace solo el pipeline nocturno, pero **una corrida manual no**: las
tablas de snapshot se acumulan por `generated_at`, así que lo que no se sube ese
día se pierde del archivo y no se puede reconstruir. Es idempotente — re-correr
la misma corrida no duplica.

`scripts/publicar.py` enriquece el cinturón de impacto social desde los artefactos
de `scripts/vida_cotidiana/data/`, agrupa las series en `series.json` y
sanitiza rutas locales en los campos `fuente`. Vercel construye la app Astro
desde `web/` con cada push a `main`. Detalle de diseño en
`docs/specs/2026-05-29-informe-coyuntura-web-design.md`.

## Outputs

| Archivo | Descripción |
|---|---|
| `output/cache/macro.json` | Último fetch válido del cinturón macro |
| `output/cache/politica.json` | Último fetch válido del cinturón político |
| `output/cache/gestion.json` | Último fetch válido del cinturón gestión |
| `scripts/vida_cotidiana/data/vida_cotidiana_*.json` | Output del orquestador de vida cotidiana |
| `output/informe.json` | Informe completo, schema v1.1.0 |
| `output/informe.md` | Informe markdown para Drive y reunión |

## Exit codes de los colectores

| Código | Significado |
|---|---|
| 0 | Todos los indicadores son datos frescos |
| 1 | Mezcla: algunos frescos, algunos del cache |
| 2 | Todos los indicadores vienen del cache (fallo total de fuentes) |

## Estructura del proyecto

```
projects/informe_coyuntura/
├── README.md                              # este archivo
├── requirements.txt                       # dependencias generales
├── data/
│   ├── gestion/manuales.json              # fallback Gestión (insumos del ITCG)
│   ├── gestion/privatizaciones.json       # etapas 0-4 por empresa (Ley Bases, BO)
│   ├── gestion/ajustes_itcg.json          # overrides del analista sobre el ITCG
│   ├── macro/ajustes_itcm.json            # overrides del analista sobre el ITCM
│   └── politica/manuales.json             # fallback Político
├── docs/
│   ├── 260520 Proyecto País...docx        # documento base de los 4 cinturones
│   ├── 260523_proyecto_pais_estado_extraccion.md  # relevamiento de fuentes, mayo 2026
│   ├── arquitectura/                      # arquitectura del sistema (flujo, contratos, operación)
│   ├── adr/                               # decisiones metodológicas
│   └── archivo/cinturon_*.md              # diseño original, sólo histórico
├── output/                               # outputs VERSIONADOS (ver nota abajo)
│   ├── cache/                            # último fetch válido por cinturón (fallback CI)
│   ├── informe.json / informe.md        # reporte generado
│   └── series/                           # CSVs de series por cinturón
└── scripts/
    ├── generar_informe.py
    ├── gestion.py                         # colector del cinturón de gestión
    ├── itcg.py                            # bandas y fórmula del ITCG gestión
    ├── itcm.py                            # bandas y fórmula del ITCM macro
    ├── parametrica.py                     # motor común de los índices paramétricos
    ├── macro.py                           # colector del cinturón macro
    ├── politica.py                        # colector del cinturón político
    ├── vida_cotidiana.py                  # puente legacy al orquestador global
    └── vida_cotidiana/
        ├── main.py                        # orquestador completo de impacto social
        ├── collectors/                    # bcra, indec_series, utdt_icc, cafam, ciccra, snic, salud, trends
        ├── config.py
        ├── data/                          # outputs crudos del orquestador (versionados)
        └── requirements.txt
```

> **Outputs versionados:** `output/` y `scripts/vida_cotidiana/data/` se versionan
> (no están en `.gitignore`) para que un colaborador tenga el reporte y los datos ya
> generados sin correr los colectores. Se regeneran corriendo los scripts; el pipeline
> diario (CI) los actualiza. Lo único que NO se versiona son deps/caches
> (`node_modules/`, `__pycache__/`) y el build web (`web/dist/`, que Astro
> regenera en cada build).

## Onboarding rápido

1. Leer `docs/260523_proyecto_pais_estado_extraccion.md` para el panorama completo de indicadores, fuentes y estado.
2. Leer los ADRs del cinturón en el que se vaya a trabajar (`docs/adr/README.md`)
   y el motor paramétrico correspondiente (`scripts/itcm.py`, `itcg.py`, `itcp.py`,
   `parametrica.py`). `docs/archivo/cinturon_*.md` es el diseño original
   pre-implementación — superado por los ADRs, no refleja el estado actual.
3. Correr los cuatro colectores y el orquestador de impacto social para verificar que las fuentes respondan.
4. Inspeccionar los outputs en `output/cache/*.json` (cada uno tiene indicadores, score y metadatos de extracción).

## Documentación en Word (institucional)

Los archivos `docs/*.md` se convierten a `.docx` con identidad visual CIGOB (logo, paleta institucional, header, footer y paginación) mediante pandoc + un template propio.

Para regenerar todos los `.docx` desde sus `.md`:

```powershell
cd docs/template
./build_all_docx.ps1
```

Detalles del sistema de templates en `docs/template/README.md`.

## Patrones técnicos consolidados

- **Sesión POST en InfoLeg** (usado en `politica.py:fetch_ratio_dnu` y tres colectores de `gestion.py`): GET a la home para obtener `jsessionid`, extraer URL de acción del formulario con regex, POST con parámetros. La búsqueda es OR sobre tokens (no exacta); para aislar normas específicas usar vocabulario técnico exclusivo (ejemplo: "VPU" para RIGI).
- **CKAN HCDN** (3 indicadores en `politica.py`): `q=` realiza búsqueda full-text por tokens, no substring. Filtros con caracteres acentuados fallan por encoding; filtrar siempre del lado Python con `.lower()`.
- **datos.gob.ar series**: `https://apis.datos.gob.ar/series/api/series/?ids=<id>&format=json&limit=N&sort=desc`.
- **BCRA API v4.0**: requiere `verify=False` y `urllib3.disable_warnings()`. Los datos vienen en orden descendente; `detalle[0]` es el dato más reciente.

## Dependencias clave

```
requests>=2.31.0
xlrd==1.2.0          # Para leer .xls OLE2 (UTDT ICC). No usar xlrd>=2.0
beautifulsoup4>=4.12
pdfplumber>=0.10.0
pytrends>=4.9.2
```
