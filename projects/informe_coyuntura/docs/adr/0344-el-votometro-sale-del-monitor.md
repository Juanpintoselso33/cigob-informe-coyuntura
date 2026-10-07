---
madr: 4
id: '0344'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'politica'
indice: 'ITCP'
indicadores: [votometro_ventaja_lla]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/panel_validacion.py', 'scripts/validacion_externa.py', 'scripts/gate_calidad.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
relacionado: ['0126', '0312', '0330', '0345']
ambito: 'Cinturón política · ITCP · sale `votometro_ventaja_lla` y con él la dimensión «imagen y voto»'
origen: 'Reunión del 6-oct-2026 sobre el Monitor (punto 5 de docs/261006_reunion_pendientes.md): «sacar el Votómetro de todos los cinturones». Juan, 7-oct: el Votómetro es otro producto.'
---

# ADR-0344 — El Votómetro sale del Monitor

## Contexto y planteo del problema

El Votómetro (`votometro_ventaja_lla`, ventaja de La Libertad Avanza sobre el
peronismo en intención de voto) era la única card de la dimensión «imagen y voto»
del índice político, con el 7 % del peso. La reunión del 6-oct-2026 decidió
sacarlo del Monitor: el Votómetro pasa a ser un producto aparte de CiGob. Además
llevaba dos meses y medio sin dato nuevo (última edición, 22-jul-2026: +4,3 pp).

## Factores de decisión

- El cinturón político mide capital político, no popularidad (marco de Matus):
  el Votómetro era la excepción declarada.
- Una dimensión sin indicadores no puede quedar en el índice (las pruebas exigen
  pesos internos que sumen 1).
- Repartir el peso sin alterar el orden relativo entre las dimensiones que quedan.

## Opciones consideradas

1. Borrar la dimensión y repartir su 7 % en proporción entre las seis restantes.
2. Dejar la dimensión vacía y que el motor la renormalice cada mes.
3. Reemplazar el Votómetro por otro indicador de imagen.

## Decisión

**Opción 1**, el mismo procedimiento inverso que ADR-0330 usó dentro del poder
legislativo: las seis dimensiones restantes se dividen por 0,93.

| Dimensión | Antes | Ahora |
|---|---|---|
| Poder legislativo | 0,21 | 0,2258 |
| Alianzas territoriales | 0,19 | 0,2043 |
| Cohesión interna | 0,15 | 0,1613 |
| Conflicto social | 0,10 | 0,1075 |
| Poder judicial | 0,15 | 0,1613 |
| Sector privado | 0,13 | 0,1398 |

Sale todo lo del Votómetro: el colector y su parser, la banda (ADR-0312), la
serie, la procedencia de anclas, el HTML de respaldo y su test. Sale también
`clima_electoral`, la misma serie usada como referencia del panel de validación
(tenía dos puntos y nunca llegó al mínimo de doce para correlacionar). La ficha
del indicador se conserva como ficha histórica, con la entrada de la baja.

### Consecuencias

- El índice político sube de 71,2 a 73,8 (tensión de 2,9 a 2,6) con los datos
  del 7-oct-2026: el Votómetro puntuaba 37,2, bastante debajo del resto.
- El Monitor pasa a tener 66 cards hasta que entre la confianza en el Gobierno
  (ADR-0345), que vuelve a dejarlo en 67.
- La serie del índice político se reconstruye sin el Votómetro en toda su
  historia: el cambio no es sólo del mes.

### Confirmación

Las pruebas del ITCP verifican que los pesos de las dimensiones sumen 1 y el
orden de las seis; `test_fichas_pesos.py` cruza la leyenda de la ficha con los
pesos publicados.

## Pros y contras de las opciones

### Opción 1 — Borrar y repartir

- Bien: deja el diseño explícito, como ADR-0330.
- Mal: cambia el número publicado del índice.

### Opción 2 — Dimensión vacía

- Bien: el motor ya la saltea.
- Mal: deja en el diseño una dimensión que no mide nada.

### Opción 3 — Reemplazarlo

- Mal: contradice que el índice mida capital político y no popularidad.

## Más información

- ADR-0312: la banda del Votómetro.
- ADR-0330: el procedimiento de reparto proporcional.
