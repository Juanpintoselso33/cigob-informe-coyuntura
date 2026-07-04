# 02 — Pipeline de datos

## El flujo completo

```mermaid
flowchart LR
    subgraph Fuentes
        F1[INDEC / BCRA / MECON<br/>datos.gob.ar / apis.datos]
        F2[UTDT · CICCRA · CAFAM<br/>SNIC · ACLED · Trends]
        F3[Yahoo Finance · ArgentinaDatos<br/>Presupuesto Abierto · HCDN]
    end
    subgraph Colectores
        C1[macro.py]
        C2[gestion.py]
        C3[vida_cotidiana/main.py]
        C4[politica.py]
        C5[espiritu_epoca.py]
    end
    Fuentes --> Colectores
    Colectores -->|escriben| CACHE[(output/cache/*.json)]
    CACHE --> GEN[generar_informe.py<br/>SOLO ENSAMBLA]
    GEN --> INF[(output/informe.json)]
    F1 --> SER[descargar_series.py]
    F2 --> SER
    SER --> CSV[(output/series/*.csv)]
    SER <--> STORES[(data/*/[..]_serie.json<br/>stores resilientes)]
    CSV --> VAL[validacion_externa.py]
    VAL --> VSTORE[(output/validacion_externa.json)]
    INF --> PUB[publicar.py<br/>scoring paramétrico + snapshot]
    CSV --> PUB
    VSTORE --> PUB
    PUB --> WEB[(web/src/data/<br/>informe.json + series.json)]
```

**Regla de oro del pipeline:** `generar_informe.py` **no refresca nada** —
solo ensambla los caches que dejaron los colectores. Si un indicador no se
actualiza, el sospechoso es su colector, no el generador. Para actualizar un
cinturón a mano hay que correr su colector primero (ej.
`python scripts/macro.py`) y recién después la cadena.

## Cadena de actualización manual

```bash
python scripts/macro.py                 # (o gestion.py / vida_cotidiana/main.py / etc.)
python scripts/generar_informe.py       # ensambla output/informe.json
python scripts/descargar_series.py      # series oficiales + derivadas
python scripts/validacion_externa.py    # refresca el store de validación
python scripts/publicar.py              # scoring + snapshot web/src/data
python -m pytest tests/ -q              # 40 tests deben quedar verdes
```

## Colectores

| Script | Cinturón | Particularidades |
|---|---|---|
| `scripts/macro.py` | macro | BCRA (memo anti rate-limit del IdC), INDEC, MECON, planilla ITCRM |
| `scripts/gestion.py` | gestión | Presupuesto Abierto (token), Boletín Oficial, ACLED (sonda auto-destrabante con credenciales UBA), Diagnóstico Político |
| `scripts/vida_cotidiana/main.py` | vida | modular: `collectors/{bcra,cafam,ciccra,indec_series,salud,snic,trends,utdt_icc,manual}.py`, config central en `config.py` |
| `scripts/politica.py` | política | HCDN datos abiertos, encuestas |
| `scripts/espiritu_epoca.py` | espíritu | comparte ICC y sentimiento con vida |

Cada colector escribe `output/cache/<cinturon>_<timestamp>.json`; el
ensamblador toma el más reciente. Si una fuente falla, `publicar.py` hace
**carry-forward** del indicador desde el snapshot anterior (el dato previo con
su fecha, nunca un hueco).

## `descargar_series.py` — las series de presentación

Reconstruye la serie histórica de cada indicador (obligación de diseño:
mínimo desde dic-2023) y produce los CSV de `output/series/` que alimentan
los modales de la web. Dos familias:

- **Oficiales**: series de las APIs (INDEC/BCRA/etc.) tal cual, con la misma
  transformación que el indicador (ej. recaudación = media móvil 3m del i.a.
  real, ADR-0029).
- **Derivadas**: reconstrucciones propias (brecha salario/CBT por mes común,
  I_EC de endeudamiento, rebases B100 del ITVC, IVI desde PDFs, canasta
  mensual de Trends).

### Criterio ragged edge (ADR-0030)

Los indicadores de FAMILIA (varios insumos con distinto rezago) titulan al
último mes **común** de todos los insumos, con el dato fresco declarado como
provisorio en el detalle. Nada de imputaciones.

## Stores resilientes

Patrón estándar para fuentes frágiles: **descarga sana → refresca el store;
falla → sirve del store** (la web nunca pierde la serie). Viven en `data/`:

| Store | Fuente | Particularidad |
|---|---|---|
| `data/vida/snic_serie.json` | SNIC (cloud-snic) | el host sufre apagones de días; sembrado desde git |
| `data/vida/ivi_serie.json` | LICIP-UTDT (PDFs) | URLs por hash: descubre los nuevos desde el listado y acumula (ADR-0032) |
| `data/vida/sentimiento_serie.json` | Google Trends | **reemplazo TOTAL** por corrida sana: escalas de corridas distintas nunca se mezclan (ADR-0034) |
| `data/vida/carne_serie.json` | CICCRA | serie PM-12m acumulada |
| `data/gestion/*.json` | ACLED, DP, fechas de hitos | incluye datos manuales datados |
| `data/macro/*.json` | reservas netas, patentamientos | |

## Histórico y fallback

`data/historico/indicadores.json` acumula el valor mensual de cada indicador
en cada corrida. `publicar.fusionar_historico` lo inyecta como serie SOLO
para indicadores sin serie oficial (<2 puntos) — las series con store nunca
caen ahí. Los overrides del analista viven en `data/*/ajustes_*.json`
(puntaje + justificación, se publican como nota en el modal).
