---
madr: 4
id: '0010'
estado: 'aceptado'
fecha: 2026-06-30
cinturon: 'macro'
indicadores: [iai, icip]
archivos: ['scripts/itcm.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'data/macro/patentamientos_comerciales.json', 'tests/']
ambito: '`scripts/itcm.py` · `scripts/macro.py` · `scripts/descargar_series.py` · `scripts/publicar.py` · `data/macro/patentamientos_comerciales.json` · `tests/` · web'
---

# ADR-0010 — Capítulo Inversión: IAI (físico) e ICIP (digital) como 6ª dimensión del ITCM

## Contexto y planteo del problema

Dos documentos proponen incorporar un capítulo de **inversión** al ITCM:
- **IAI — Índice Anticipador de Inversión** (`260629`): inversión física/tradicional =
  ISAC construcción (0,55) + bienes de capital importados (0,30) + patentamientos
  comerciales (0,15), en variación interanual. Umbral ±2%.
- **ICIP — Capitalización Inteligente** (`260630`): inversión digital/intangible =
  servicios tech/IA (0,40) + hardware hi-tech NCM (0,30) + productividad laboral
  (0,30). Pensado como lectura dual junto al IAI (la "trampa de la madurez":
  invertir en ladrillos sin digitalizarse).

## Opciones consideradas

- **±2% literal del doc.** Rechazada: no sobrevive a la volatilidad del dato.
- **Suavizar componentes (MA 3m)** o **medir relativo al EMAE.** Consideradas; el
  usuario eligió bandas anchas sobre el i.a. crudo (las bandas ya clampean el ruido).
- **Proxies gruesos** (total automotores; capítulo 85 NCM). Rechazados: diluyen lo que
  cada índice mide y el NCM está viejo.
- **Suscribir SIOMAA / extraer microdata NCM.** Pospuesto (costo/licencia indefinidos).

## Decisión

Nueva **6ª dimensión "Inversión" (12% del ITCM)** con dos indicadores compuestos:
IAI (0,6) e ICIP (0,4), ambos calculados en `macro.py` como promedios ponderados de
variaciones interanuales. Las 5 dimensiones previas se recortan en proporción
(26/24/16/11/11 + 12). Mayor crecimiento de inversión = menos tensión.

**Tres desvíos respecto de los docs, validados con datos reales:**

1. **Bandas anchas, no el ±2% de los docs.** Las series i.a. de inversión argentina
   se mueven ±30-180% por la base 2024-2025 (colapso + rebote); el ±2% daría señal
   saturada permanente. Bandas calibradas a la realidad conservando la lógica
   contracción/neutro/expansión:
   - IAI: `>10→100 · 2/10→80 · -2/2→60 · -10/-2→35 · <-10→10`. Hoy −4,2 → 35.
   - ICIP: `>20→100 · 5/20→80 · -5/5→60 · -20/-5→35 · <-20→10`. Hoy +8,2 → 80.

2. **IAI sin patentamientos comerciales por ahora (se ACUMULAN).** Renormalizado a
   ISAC 0,65 / BK 0,35. Ver "Fuentes que no existen" abajo.

3. **ICIP sin hardware hi-tech.** Renormalizado a servicios tech 0,57 / productividad
   0,43 (esta última = IPI/empleo, con empleo de la EIL como proxy de "horas").

### Consecuencias

- Macro **ITCM 65,0 → 63,3** (Moderadamente aflojado), **tensión 3,5 → 3,7**: la
  inversión física en contracción (IAI −4,2 → 35) agrega tensión; la digital la modera
  (ICIP +8,2 → 80). La divergencia física-vs-digital queda expuesta en el tablero.
- `data/macro/patentamientos_comerciales.json` se versiona y crece una fila por mes
  (la serie se completará sola ~mediados de 2027).
- Doble descarga del CSV DNRPA (~5 MB) por corrida de `macro.py`.
- Sparklines de IAI e ICIP (18 puntos, sin patentamientos). Tests pineados: 11
  indicadores en el índice; fixture EJEMPLO con iai/icip → ITCM 63,3.

## Más información

### Fuentes que NO existen como serie (investigadas a fondo)

El usuario pidió priorizar las fuentes difíciles; se comprobó que **no son
automatizables**, y no por esfuerzo sino por cómo se publica (o no) el dato:

- **Patentamientos comerciales:** ACARA/SIOMAA es un producto **comercial con login**.
  DNRPA (datos.jus.gob.ar) publica el desglose por tipo (CAMION/PICK-UP/UTILITARIO…)
  **solo del mes corriente** a nivel registro; el agregado histórico solo trae
  "Automotores" total (sin split). El patrón de URL para meses anteriores devuelve
  siempre el mes actual. → **Solución: acumulación.** Cada corrida de `macro.py`
  upserta el conteo comercial del mes en `data/macro/patentamientos_comerciales.json`
  (versionado). A los 13 meses, el IAI suma el 3er componente (0,55/0,30/0,15)
  automáticamente. Seed: 2026-05 = 12.652.
- **Hardware hi-tech (NCM 8471/8517/8542):** el NCM oficial en datos.gob.ar es **solo
  a 2 dígitos** (capítulo, demasiado amplio) y está ~16 meses desactualizado. Las
  posiciones a 8 dígitos solo viven en microdata bulk de Aduana, sin serie. → Se omite;
  el ICIP queda con sus 2 componentes disponibles.

### Fuentes operativas (validadas)

| Componente | Serie | Hoy (i.a.) |
|---|---|---|
| ISAC construcción | INDEC `33.2_ISAC_NIVELRAL` (i.a. del nivel) | ~−3% |
| Bienes de capital importados | INDEC ICA `74.3_IIBCA` (USD, i.a.) | −6,8% |
| Servicios tech | INDEC balanza `185.1_PAGO_SERVIICA` (i.a.) | +15,6% |
| Productividad | INDEC `453.1` IPI / `50.3` empleo EIL (i.a. del cociente) | −1,6% |
