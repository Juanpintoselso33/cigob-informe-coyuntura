# Informe de Coyuntura

Colectores de datos para los cinco cinturones del marco CIGOB-Matus (Macro, Político, Vida Cotidiana, Gestión y Espíritu de Época) y generador del informe periódico.

## Estado actual (junio 2026)

| Cinturón | Indicadores totales | Automáticos | Carga manual | Sin fuente |
|---|---|---|---|---|
| Vida Cotidiana | 14 + 1 manual | 14 | 1 | 0 |
| Macro | 11 (7 en el ITCM + 4 contexto) | 11 | 0 | 0 |
| Político | 9 | 7 | 2 | 0 |
| Gestión | 16 (14 en el ITCG + 2 contexto) | 13 | 3 | 0 |
| Espíritu de Época | 3 (v1, proxies compartidos) | 3 | 0 | 0 |

Macro y gestión se puntúan con índices paramétricos 0–100 de dimensiones ponderadas
(**ITCM**, ver `docs/cinturon_macro.md`, y **ITCG**, 5 dimensiones 35/25/15/15/10 del
doc 260702 — ver `docs/adr/0013-itcg-parametrica-gestion.md`; motor común en
`scripts/parametrica.py`); el resto promedia tensiones 0–10. El score global pondera
los cinco cinturones por fase del mandato (`config.py`: fase temprana 20% parejo;
consolidación 25/25/20/15/15, según la ponderación temporal del Marco Conceptual).

Documento de referencia con detalle por indicador: [`docs/260523_proyecto_pais_estado_extraccion.md`](docs/260523_proyecto_pais_estado_extraccion.md).

## Instalación

```bash
git clone https://github.com/Juanpintoselso33/biblitotecario-ai.git
cd biblitotecario-ai/projects/informe_coyuntura
pip install -r requirements.txt
```

Para el orquestador completo de vida cotidiana:

```bash
pip install -r scripts/vida_cotidiana/requirements.txt
```

## Ejecución de los colectores

Desde la carpeta `projects/informe_coyuntura/`:

```bash
python scripts/macro.py                    # 11 indicadores macro
python scripts/politica.py                 # 7 auto + 2 manual
python scripts/gestion.py                  # ITCG: 13 auto + 3 manual
python scripts/vida_cotidiana/main.py      # 8 fuentes, ~32 datapoints
python scripts/espiritu_epoca.py           # 3 proxies (corre después de vida y política)
```

Cada colector corre de forma independiente. No es necesario correrlos todos.

## Generación del informe

```bash
python scripts/generar_informe.py
```

## Web pública

La página pública del informe vive en `web/` (app Astro) y se publica en
`https://juanpintoselso33.github.io/biblitotecario-ai/informe/`. Replica el
observatorio de klipea (CSS propio de CIGOB) y se alimenta del snapshot de datos.

Ciclo de actualización:

```bash
# 1. correr los colectores y regenerar el informe
python scripts/generar_informe.py
# 2. armar el snapshot que consume la web (web/src/data/{informe,series}.json)
python scripts/publicar.py
# 3. (opcional) previsualizar local
cd web && npm install && npm run build && npm run preview
# 4. commit del snapshot + push a main → GitHub Actions buildea y deploya
```

`scripts/publicar.py` enriquece el cinturón de vida cotidiana (3 → 13 indicadores
desde `scripts/vida_cotidiana/data/`), agrupa las series en `series.json` y
sanitiza rutas locales en los campos `fuente`. El deploy (`.github/workflows/pages.yml`)
corre `npm ci && npm run build` antes de publicar. Detalle de diseño en
`docs/specs/2026-05-29-informe-coyuntura-web-design.md`.

## Outputs

| Archivo | Descripción |
|---|---|
| `output/cache/macro.json` | Último fetch válido del cinturón macro |
| `output/cache/politica.json` | Último fetch válido del cinturón político |
| `output/cache/gestion.json` | Último fetch válido del cinturón gestión |
| `output/cache/espiritu_epoca.json` | Último fetch válido del cinturón espíritu de época |
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
│   ├── 260523_proyecto_pais_estado_extraccion.md  # estado actual — leer primero
│   ├── cinturon_espiritu_epoca.md
│   ├── cinturon_gestion.md
│   ├── cinturon_macro.md
│   ├── cinturon_politica.md
│   ├── cinturon_vida_cotidiana.md
│   └── archivo/                           # borradores pre-rediseño
├── output/                               # outputs VERSIONADOS (ver nota abajo)
│   ├── cache/                            # último fetch válido por cinturón (fallback CI)
│   ├── informe.json / informe.md        # reporte generado
│   └── series/                           # CSVs de series por cinturón
└── scripts/
    ├── espiritu_epoca.py                  # 3 proxies del humor social (v1)
    ├── generar_informe.py
    ├── gestion.py                         # 15 indicadores (ITCG)
    ├── itcg.py                            # bandas y fórmula del ITCG gestión
    ├── itcm.py                            # bandas y fórmula del ITCM macro
    ├── parametrica.py                     # motor común de los índices paramétricos
    ├── macro.py                           # 11 indicadores (ITCM)
    ├── politica.py                        # 9 indicadores
    ├── vida_cotidiana.py                  # puente legacy al orquestador global
    └── vida_cotidiana/
        ├── main.py                        # orquestador completo (14+ datapoints)
        ├── collectors/                    # bcra, indec_series, utdt_icc, cafam, ciccra, snic, salud, trends
        ├── config.py
        ├── data/                          # outputs crudos del orquestador (versionados)
        └── requirements.txt
```

> **Outputs versionados:** `output/` y `scripts/vida_cotidiana/data/` se versionan
> (no están en `.gitignore`) para que un colaborador tenga el reporte y los datos ya
> generados sin correr los colectores. Se regeneran corriendo los scripts; el pipeline
> diario (CI) los actualiza. Lo único que NO se versiona son deps/caches
> (`node_modules/`, `__pycache__/`) y el build web (`web/informe/`, lo regenera el CI).

## Onboarding rápido

1. Leer `docs/260523_proyecto_pais_estado_extraccion.md` para el panorama completo de indicadores, fuentes y estado.
2. Leer el archivo `docs/cinturon_*.md` del cinturón en el que se vaya a trabajar.
3. Correr los cinco scripts para verificar que las fuentes respondan.
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
