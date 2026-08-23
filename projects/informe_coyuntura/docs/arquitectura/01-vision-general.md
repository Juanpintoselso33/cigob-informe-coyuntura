# 01 — Visión general

## Qué es

Sistema automatizado que produce el **Informe de Coyuntura CIGOB**: un tablero
público que sigue la situación argentina a través de
**cuatro cinturones** de indicadores, con actualización nocturna sin
intervención manual.

Los cinturones vienen del marco Matusiano (Triángulo de Gobierno) adoptado por
el CIGOB:

| Cinturón | Slug | Puntuación |
|---|---|---|
| Situación macroeconómica | `macro` | **ITCM** paramétrico |
| Gestión / reformas | `gestion` | **ITCG** paramétrico |
| Vida cotidiana | `vida_cotidiana` | **ITVC-B100** |
| Política | `politica` | **ITCP** paramétrico |

Espíritu de época fue el quinto cinturón hasta que salió del tablero
(ADR-0205). El conteo de indicadores por cinturón se mueve con cada alta o
baja, así que no se repite acá: la tabla del
[README del proyecto](../../README.md) lo lleva y la cuenta viva la publica la
propia página de metodología.

Cada cinturón publica un **score de tensión 0-10** (mayor = más tensión) y el
sitio los agrega en un panel global.

## Las cuatro paramétricas

- **ITCM** (macro): 6 dimensiones (26/24/16/11/11/12), con anclas e
  interpolación. Estabilidad monetaria combina IPC, REM, IDM y presión
  de dolarización de carteras con pesos internos 40/25/25/10. Esta última mide
  un constructo latente con observable por régimen: brecha CCL/A3500 suavizada
  antes de abril de 2025 y compras netas de personas sobre M2 privado desde la
  apertura (ADR-0055).
- **ITCG** (gestión): avance de la transformación del Estado, 5 dimensiones
  (35/25/15/15/10), 0-100 con bandas por indicador.
- **ITVC-B100** (vida): índice de seguimiento con base 100 = 4T-2023
  (arranque del mandato); cada componente es un rebase de su serie, sin
  bandas. Tensión = 5 − (ITVC − 100) × 0,2. Los componentes se winsorizan
  asimétricamente —techo 140, sin piso (ADR-0033)— salvo los exentos.
- **ITCP** (política): 7 dimensiones con bandas por indicador (ADR-0036). La
  política dejó de puntuarse por score directo.

El detalle de agregación está en [03 — Motor paramétrico](03-motor-parametrico.md).

## Principios de diseño

1. **La app deployada es la fuente de verdad.** Los documentos metodológicos
   de origen son read-only; cuando la metodología evoluciona, cambia el
   código (scripts, ponderaciones, datos) y se documenta la decisión como ADR.
2. **Toda decisión no trivial es un ADR** (`docs/adr/`, más de 230):
   rediseños de indicadores, criterios de familia (ragged edge, ADR-0030),
   tratamiento de outliers (ADR-0033), fuentes descartadas con evidencia.
3. **Todo indicador automatizado reconstruye su serie hacia atrás** — mínimo
   desde dic-2023 — y su último punto coincide con el valor del titular.
4. **Fuentes oficiales o de referencia, con resiliencia**: cada fuente frágil
   tiene un store persistente en `data/` que amortigua apagones (ver
   [02 — Pipeline](02-pipeline-datos.md#stores-resilientes)).
5. **Registro institucional en todo texto público**: lenguaje llano sí,
   coloquial no; y **cero jerga interna** — ningún número de ADR ni ID de
   serie aparece en la web (vara: "¿lo publicaría un diario serio?").
6. **Honestidad metodológica sobre cosmética**: las crisis no se recortan
   (se señalizan como dimensión crítica), las limitaciones se declaran en la
   ficha del indicador (error muestral, base declarada, mes provisorio), y
   los booms no compran compensación ilimitada (techo de winsorización).

## Mapa del repo

```
projects/informe_coyuntura/
├── scripts/            # colectores + motor + publicación (ver 02 y 03)
│   └── vida_cotidiana/ # colector modular con collectors/ por fuente
├── data/               # stores persistentes y overrides del analista
├── output/             # artefactos intermedios: cache/, series/, informe.json
├── web/                # sitio Astro (ver 04)
├── tests/              # pytest: motor paramétrico, fuentes y reconciliación
└── docs/
    ├── adr/            # decisiones (más de 230)
    └── arquitectura/   # esta carpeta
```

Los workflows de CI viven en la **raíz del repositorio padre**
(`.github/workflows/`), no dentro de `projects/informe_coyuntura/` — ver
[05 — Operaciones](05-operaciones.md).
