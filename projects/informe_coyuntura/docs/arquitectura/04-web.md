# 04 — Web

## Stack

**Astro estático** (sin backend): la web importa el snapshot congelado
(`web/src/data/informe.json` + `series.json`) que dejó `publicar.py`. Cada
deploy es una foto completa y verificable.

```
web/src/
├── pages/
│   ├── index.astro        # panel global (5 cinturones, tensión)
│   └── [slug].astro       # página por cinturón: tiles, modales, robustez,
│                          #   validación externa y matriz cruzada
├── components/            # Hero, TensionPanel, IndicadorTile/Row/Modal,
│                          #   Evolucion, Sparkline, Metodologia, ...
├── lib/
│   ├── datos.ts           # acceso al snapshot + reglas de presentación
│   ├── charts.ts          # ApexCharts: timeChart / multiTimeChart
│   ├── formulas.ts        # fórmulas KaTeX en lenguaje llano, por indicador
│   ├── descripciones.ts   # qué es / qué aporta / frecuencia, por indicador
│   └── math.ts, sparkline.ts
└── data/                  # SNAPSHOT (no editar a mano)
```

## Reglas de presentación (en `datos.ts`)

- **Recorte de series**: los modales muestran desde `SERIE_DESDE`
  (dic-2023, pedido editorial: la historia relevante es el mandato).
  Excepciones en `SERIE_COMPLETA` (hoy: `protestas_caba`, cuya razón de ser
  es comparar contra la era pre-mandato).
- Etiquetas legibles (`LABELS`), unidades cortas y largas por indicador.

## Gráficos (`charts.ts`)

- **Área con polaridad** (`POLARIDAD_SIGNO`): verde del lado bueno del cero,
  rojo del malo, por indicador (+1 = subir es bueno). Dos modos:
  - serie que **cruza el cero**: degradé partido EXACTO en el cero — el corte
    se calcula sobre la caja de la serie (no del eje) y el eje se clava con
    paso "lindo" {1, 2, 2.5, 5, 10}×10^k para que el cero caiga en un tick;
  - serie **de un solo lado**: se tiñe entera del color de ese lado (ej.
    gasto real siempre negativo = todo zona verde).
  - Opacidades 0,36 lejos del cero → 0,16 junto al cero (menos de eso se
    lava y parece un resplandor).
- `multiTimeChart`: comparadas (ej. TCRM bilateral Brasil/EEUU/China) con
  línea de referencia (`refY`, ej. mediana histórica).

## Modales de indicador (`IndicadorModal.astro`)

Ficha completa por indicador: último valor, unidad, dimensión y peso,
frecuencia, fuente, "qué aporta", **cómo se construye** (fórmula KaTeX +
leyenda), **cómo incide en el score** (gauge de tensión + fórmula de
agregación con notas de winsorización / base declarada / ajustes del
analista) y la evolución histórica.

## Reglas editoriales (no negociables)

1. **Registro institucional**: lenguaje llano y didáctico, jamás coloquial.
   Vara: "¿lo publicaría un diario serio?"
2. **Cero jerga interna**: ningún número de ADR, ID de serie ni nombre de
   variable en texto visible (`grep -r "ADR-\d" web/src` debe dar 0 en
   texto público).
3. Las limitaciones se declaran en la ficha, en llano: "mes provisorio",
   "base declarada ene-2024", "error muestral ±3%", "winsorizado".
4. Cards nuevas: familia visual completa + respiración interna, y
   **screenshot comparado contra una card aprobada ANTES de pushear**.

## Build dual

El sitio se compila dos veces (ver [05 — Operaciones](05-operaciones.md)):
`DEPLOY_TARGET=dominio` (base `/`, sale a `web-dominio/` para
informe.cigob.org) y default (base `/informe`, para GitHub Pages del repo).
