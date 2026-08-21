---
madr: 4
id: '0045'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
parametros: ['BANDAS_ITCP["comisiones_caidas"]']
archivos: ['scripts/itcp.py', 'tests/test_itcp.py', 'web/src/lib/fichas.ts', 'scripts/gate_calidad.py']
relacionado: ['0058', '0059', '0061', '0064', '0081', '0167', '0168', '0171', '0225', '0226']
ambito: '`scripts/itcp.py` (`BANDAS_ITCP["comisiones_caidas"]`) · `tests/test_itcp.py` · `web/src/lib/fichas.ts` · `scripts/gate_calidad.py` (excepción G3 de votometro_ventaja_lla, hallazgo menor de la misma auditoría)'
---

# ADR-0045 — comisiones_caidas: recalibración de bandas ITCP (saturación en espejo)

## Contexto y planteo del problema

Quinta y última recalibración de la tanda del 2026-07-09, encontrada por la
auditoría adversarial indicador-por-indicador del cinturón político (todas
las cards reproducidas desde fuente cruda; todas las series recomputadas
con implementación independiente — cero errores de cálculo en los 12
indicadores).

`comisiones_caidas` (% de proyectos con dictamen de Orden del Día sin
sanción, ventana móvil 12m) tenía anclas 30/50/70/85 tomadas del diseño
conceptual ("20-30% es lo normal" según el doc de cinturón político). La
realidad de la métrica es otra: con ventana móvil de 12 meses, un dictamen
reciente casi nunca alcanza a sancionarse dentro de su propia ventana, así
que el piso ESTRUCTURAL observado es 94,7% y el rango real completo es
94,7–99,8 (32 puntos mensuales, dic-2023→jul-2026, media 98,2).

Resultado con las anclas viejas: **los 32 meses caían en la banda del piso
(>85 → 10)** — tensión máxima clavada, cero discriminación. Es la misma
patología que `cohesion_bloque` (ADR-0042), en espejo: aquél saturaba el
techo, éste el piso. La propia ficha metodológica pública ya declaraba la
saturación como limitación conocida ("el indicador satura en el tope y
pierde capacidad de discriminar la coyuntura") — estaba diagnosticada,
nunca accionada.

## Opciones consideradas

- **Dejar las anclas del doc** ("es la operacionalización institucional") —
  descartada: ADR-0036 ya estableció que la operacionalización del ITCP es
  editorial (el doc describe dimensiones, no fija anclas validadas), y la
  regla de proyecto (lanzamiento agosto 2026) prohíbe sentarse sobre
  bandas que se saben rotas. Cuatro precedentes idénticos el mismo día.
- **Cambiar la métrica en vez de las anclas** (p.ej. medir solo dictámenes
  con ≥6 meses de antigüedad, eliminando el sesgo de ventana) — descartada
  por ahora: cambia la definición pública del indicador a semanas del
  lanzamiento; las anclas recalibradas logran la discriminación sin tocar
  la semántica. Queda como mejora posible post-lanzamiento.

## Decisión

Anclas nuevas: **96 / 97 / 98 / 99** (menor = mejor, tramos extremos
abiertos, ADR-0021), chequeadas contra los 32 puntos reales: 5/3/5/10/9
por banda, todas pobladas. Números redondos, mismo estilo que las otras
cuatro recalibraciones del día (ADR-0038/0039/0042/0043).

Efecto material: el valor vigente (97,7%) pasa de puntuar 10 (piso plano) a
~60 (interpolado) — la dimensión "poder legislativo" y el ITCP suben en
consecuencia (~3 puntos de índice, tensión del cinturón ~3,3 → ~2,9). No es
maquillaje: es dejar de imputar tensión máxima permanente por comparar la
métrica contra un rango (20-85%) que la metodología de la fuente hace
inalcanzable por construcción.

**Hallazgo menor de la misma auditoría, mismo commit**:
`votometro_ventaja_lla` tenía la misma fragilidad G3 ya corregida dos veces
hoy para otros indicadores (card anclada a HOY vs. serie anclada a fin de
mes — hoy difieren 0,1pp y pasan la tolerancia de casualidad; una encuesta
nueva a mitad de mes los separa más). Excepción G3 agregada con el mismo
fundamento documentado que cohesion_bloque/cohesion_bloque_senado/
alineamiento_senadores_prov.

### Consecuencias

- Los 5 indicadores con banda propia del ITCP recalibrados o validados hoy
  quedan todos discriminando sobre rangos reales: alineamiento (ADR-0038),
  cohesión Senado (ADR-0039), cohesión Diputados (ADR-0042), protestas
  CABA (ADR-0043), comisiones caídas (este ADR); adhesión RIGI validada
  sin cambio (ADR-0044). Ninguna banda del índice queda saturada contra
  datos reales.
- El salto del ITCP (~67 → ~70) queda registrado en este ADR como cambio
  metodológico, no como mejora de coyuntura — el histórico reconstruido de
  validación externa se regenera con las bandas nuevas en el mismo commit
  (validacion_externa.py + sensibilidad.py re-corridos, regla nueva del
  camino scoped en CLAUDE.md).
