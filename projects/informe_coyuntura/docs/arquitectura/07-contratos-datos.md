# 07 — Contratos de datos

Los esquemas de los artefactos que cruzan fronteras entre componentes.
Regla: **la web solo lee `web/src/data/` (el snapshot)**; nadie edita esos
archivos a mano.

## `web/src/data/informe.json` — el snapshot

```jsonc
{
  "generado": "2026-07-04T...",
  "validacion_cruzada": {            // matriz 3×3 (raíz, la comparten los 3 cinturones)
    "filas": [ { "indice": "ITCM", "propio": "riesgo",
                 "riesgo": {"r": -0.74, "n": 30},
                 "merval": {"r": 0.64, "n": 30},
                 "icc":    {"r": 0.53, "n": 29} }, ... ],
    "titulo": "...", "sub": "...", "conclusion": "..."   // texto dinámico
  },
  "cinturones": {
    "macro": {
      "score": 4.2, "estado": "...",
      "itcm": { /* bloque paramétrico, ver abajo */ },
      "indicadores": { "<clave>": { /* indicador, ver abajo */ } }
    },
    "gestion":        { "itcg": {...}, ... },
    "vida_cotidiana": { "itvc": {...}, ... },
    "politica":       { ... },       // score directo, sin bloque paramétrico
    "espiritu_epoca": { ... }
  }
}
```

### El indicador publicado

```jsonc
{
  "valor": 28.0,                 // el titular de la card
  "unidad": "% de hogares víctimas (últimos 12 meses)",
  "fuente": "UTDT — Índice de Victimización (LICIP)",
  "fecha_dato": "2026-04",       // período del dato (no de la corrida)
  "detalle_txt": "...",          // aclaraciones: provisorio, contraste, doble ventana
  "desactualizado": false,       // true si el carry-forward superó el umbral
  "en_indice": true,             // integra la paramétrica (false = contexto)
  "dimension": "confianza",
  "indice_itvc": 102.1,          // B100 del componente (solo vida)
  "peso_efectivo": 0.045,        // peso final tras renormalización
  "aporte_score": 4.6,           // tensión 0-10 que aporta
  "aporte_formula": "...",       // cómo se calcula, en llano (va al modal)
  "aporte_nota": "..."           // winsorizado / base declarada / ajuste analista / contexto
}
```

### El bloque paramétrico (`itcm` / `itcg` / `itvc`)

```jsonc
{
  "valor": 90.7, "banda": "deterioro_moderado", "banda_legible": "...",
  "dimensiones": {
    "confianza": {
      "nombre": "Confianza y seguridad", "peso": 0.15, "puntaje": 103.8,
      "critica": false,          // flag ADR-0020: bajo umbral, el promedio no la compensa
      "indicadores": {
        "icc_utdt": { "peso": 0.45, "peso_efectivo": 0.0675,
                      "puntaje_banda": 97.1,     // sin override
                      "puntaje_aplicado": 97.1 } // vigente (= banda salvo ajuste)
      }
    }
  },
  "ajustes_aplicados": [],        // overrides del analista efectivamente usados
  "robustez": { "p05": 88.6, "p95": 92.1,        // Monte Carlo (ADR-0019/0031)
                "dominante": { "indicador": "...", "indice_sin": 98.2 } },
  "validacion": { /* par propio: serie propia vs ancla externa, r, n, plot */ }
}
```

## `web/src/data/series.json`

`{ "<clave>": [ { "fecha": "YYYY-MM-DD", "valor": 28.0 }, ... ] }` —
ordenada ascendente; **el último punto debe coincidir con el `valor` del
indicador** (invariante de diseño; si difiere, el colector y la serie se
desincronizaron). La web recorta a `SERIE_DESDE` (dic-2023) al presentar,
salvo `SERIE_COMPLETA`. Claves extra sin card (`inseguridad_snic`,
`itvc_*` rebasadas, bilaterales del TCRM) alimentan fichas y validación.

## `output/` — artefactos intermedios

- `cache/<cinturon>_<ts>.json`: crudo del colector (el ensamblador toma el
  más reciente por cinturón).
- `informe.json` / `informe.md`: ensamblado editorial (pre-scoring).
- `series/*.csv`: `fecha,valor` por indicador (+ metadatos de unidad/fuente
  en el registro de `descargar_series.py`).
- `validacion_externa.json`: series reconstruidas de los 3 índices + anclas
  externas + correlaciones (niveles, diferencias, lead-lag).
- `sensibilidad.json`, `interpolacion_sombra.json`: soportes de robustez.

## `data/` — stores y overrides (SÍ se editan, con criterio)

| Archivo | Forma | Regla |
|---|---|---|
| `*/ajustes_it{cm,cg,vc}.json` | `{ "<indicador>": { "puntaje": 80.0, "justificacion": "..." } }` | override del analista; se publica como nota; vacío = `{}` |
| `vida/itvc_baselines.json` | `{ "<ind>": { "valor": ..., "fuente": "..." } }` | base 4T-2023 SOLO para componentes sin serie automatizable |
| `vida/{snic,carne}_serie.json` | `{ "_meta": {...}, "anual"/"mensual": { "<per>": v } }` | acumulativo: descarga sana refresca |
| `vida/ivi_serie.json` | `+ "procesados": [urls]` | acumulativo por PDF; nunca reprocesa |
| `vida/sentimiento_serie.json` | `{ "_meta", "mensual" }` | **REEMPLAZO TOTAL** por corrida sana (escalas relativas no se mezclan) |
| `historico/indicadores.json` | `{ "<ind>": { "YYYY-MM": v } }` | lo escribe `publicar`; fallback de serie solo si no hay oficial |
| `gestion/*.json`, `politica/manuales.json`, `macro/*.json` | ad-hoc datado | todo dato manual lleva fecha y fuente |

## Convenciones transversales

- Fechas de series: `YYYY-MM-01` para mensuales (trimestrales al primer mes
  del período; anuales `YYYY-12-01`).
- `_meta.actualizado` en cada store: primera pregunta ante un dato viejo.
- Los caches y el snapshot los commitea el bot nocturno — un diff grande en
  `web/src/data/` tras un pull es normal.
