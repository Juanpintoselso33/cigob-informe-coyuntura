---
madr: 4
id: '0396'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'transversal'
indice: 'ITCM · ITCG · ITCP · ITCIS'
indicadores: [ratio_dnu, jornadas_individuales_no_trabajadas_12m, reservas_bcra, saldo_comercial_12m, desregulacion_normativa, tasa_homicidios, tasa_robos, pobreza_nowcast, inseguridad]
archivos: ['scripts/publicar.py', 'scripts/parametrica.py', 'tests/test_adr0396_lectura_rotulos_tablas.py']
relacionado: ['0181', '0182', '0327', '0393']
ambito: 'Semáforo · lectura en palabras · tablas de colores · rótulos de base'
origen: 'Revisión de la tarjeta de DNU (lectura «verde» con semáforo amarillo), de la de jornadas no trabajadas (tabla sin rojo) y de los rótulos de base de la vida cotidiana, 28-oct-2026.'
---

# ADR-0396 — La lectura sale del valor crudo y las tablas de color cierran

## Contexto y planteo del problema

Tres defectos del motor de publicación, verificados contra el snapshot:

1. **Una tarjeta decía dos colores.** `ratio_dnu` publicaba «está en verde» en la
   lectura y amarillo en el semáforo (1,094, a 0,01 del corte). La lectura usaba la
   tensión redondeada a un decimal y el semáforo la cruda (ADR-0181).
2. **Rótulos de base falsos.** Homicidios y robos se anclan en la mediana de su serie
   ([[0327]]) y pobreza en el 2º semestre de 2023, pero el texto decía «vs 4T-2023».
   La victimización conservaba el rótulo «ene-2024» pese a [[0393]].
3. **Tablas de color sin su último tramo.** Para los tramos abiertos,
   `umbrales_en_unidad` evaluaba el color a «corte ± 1» en unidades crudas; como el
   puntaje se redondea a un decimal, en variables de miles o millones el punto caía
   pegado al corte y el tramo extremo se fusionaba con el vecino.

## Decisión

- La lectura en palabras (`aporte_lectura`) se calcula con la misma tensión sin
  redondear que decide el color, en los cuatro cinturones.
- Rótulos: homicidios y robos «vs la mediana de la serie 2000-2025 (100 = igual que la
  mediana histórica)»; pobreza «vs el 2º semestre de 2023»; victimización usa el
  default (promedio del 4T-2023).
- Los tramos abiertos se evalúan a un paso proporcional al ancho de las anclas, no a
  una unidad fija. Cambian tres tablas por la misma falla y una por el rojo faltante:
  `reservas_bcra` (rojo bajo 1.250), `saldo_comercial_12m` (rojo bajo −12.500),
  `desregulacion_normativa` (rojo bajo 3.400) y `jornadas_individuales_no_trabajadas_12m`
  (rojo desde 8,85 M). Ningún color de ningún valor cambia: sólo la tabla publicada.
- El «¿por qué este color?» muestra los cortes con la precisión del indicador y los
  números del millar para arriba con separador de miles y sin «,0».

### Consecuencias

Las tablas de color y los textos de cuatro/nueve tarjetas cambian en la próxima
corrida. Los puntajes, pesos e índices no se tocan.

### Confirmación

`tests/test_adr0396_lectura_rotulos_tablas.py`.
