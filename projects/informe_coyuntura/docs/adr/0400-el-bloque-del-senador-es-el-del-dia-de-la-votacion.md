---
madr: 4
id: '0400'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [cohesion_bloque, alineamiento_senadores_prov, votos_sobre_bancas]
archivos: ['data/politica/pases_senadores.json', 'scripts/politica.py', 'scripts/descargar_series.py', 'tests/test_pases_senadores.py', 'tests/test_descargar_series_cohesion.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
relacionado: ['0376', '0401', '0402']
ambito: 'ITCP · votaciones del Senado · bloque de cada senador en cada acta'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0400 — El bloque del senador es el del día de la votación

## Contexto y planteo del problema

El portal de votaciones del Senado muestra, en todas las actas, el bloque que el senador
tiene HOY, no el que tenía el día en que votó. Las 325 actas del mandato bajadas el
28-oct-2026 dan a Luis Juez, Carmen Álvarez Rivero y Francisco Paoltroni como La
Libertad Avanza desde febrero de 2024 hasta septiembre de 2026, sin un solo cambio. Los
pases verificados en prensa:

- **Juez**: bloque PRO y luego monobloque Frente Cívico; integra el interbloque de LLA
  desde el 9-dic-2025 y entra al bloque el 23-feb-2026 (Ámbito, Perfil).
- **Álvarez Rivero**: pasa del bloque Frente PRO al de LLA el 4-nov-2025 (Hoy Día).
- **Paoltroni**: expulsado del bloque el 28-ago-2024 (BAE Negocios, Infobae), arma un
  monobloque y vuelve al bloque el 10-dic-2025, con la asunción de Patricia Bullrich como
  jefa (a24, Radio Rivadavia).

Tres indicadores leían ese bloque: la cohesión del Senado contaba a Juez y a Paoltroni
votando contra el bloque como disidencia interna; el alineamiento provincial los sacaba
de los senadores «de otro bloque» de Córdoba y Formosa; y los votos ajenos sobre las
bancas contaban nueve bancas propias en 2024 cuando eran siete.

## Factores de decisión

- Un indicador del bloque propio tiene que contar al bloque de ese día.
- El portal no publica la historia de bloques: hay que registrarla aparte, con fuente.
- La regla de [[0376]] y de la cohesión: el bloque, no el interbloque.

## Opciones consideradas

- **Registro versionado de pases, con fuente por tramo (elegida).**
- Sacar del cálculo a los senadores que cambiaron de bloque.
- Dejar el bloque del portal y declararlo como limitación.

## Decisión

`data/politica/pases_senadores.json` lista, para cada senador que cambió de bloque en el
mandato, los tramos `{senador, bloque, desde, hasta, fuente}`. `politica.py` lo aplica en
toda acta del Senado antes de contar (`filas_senado_a_la_fecha`): en la cohesión del
Senado (tarjeta y detalle anual), en el alineamiento provincial (tarjeta y detalle anual)
y en las bancas de LLA de `votos_sobre_bancas`. Un senador que no figura conserva el
bloque del acta. Juez cuenta en LLA desde el 23-feb-2026: el interbloque no es el bloque.
Diputados no cambia: el PDF de cada acta trae el bloque del día.

### Consecuencias

- `descargar_series.py` usa el mismo registro (llama a las mismas funciones) y vuelve a
  pedir los años cerrados cacheados con la versión anterior del detalle
  (`VERSION_DETALLE_ACTAS`); la caché de actas de `votos_sobre_bancas` pasa a la versión
  3 del Senado y se relee una vez.
- Recalculado en memoria con las actas del 28-oct: la cohesión compuesta, sin otro
  cambio, sube en los meses de 2024 y 2025 en que Juez o Paoltroni votaron distinto del
  bloque (ago-2025: de 90,3 a 98,1; el valor de hoy no cambia, 100). El alineamiento
  cambia poco salvo en jul-2025 (60,9 → 75,4) y ago-2025 (19,4 → 16,7); hoy sigue en
  56,5. `votos_sobre_bancas` sube unas décimas en todo el período (hoy 22,1 → 22,3; el
  Senado, 28,9 → 29,3).
- Un pase nuevo no se detecta solo: se agrega al registro con su fuente.
- La historia previa de otros gobiernos (anclas de [[0401]] y [[0402]]) usa el bloque
  del portal; queda declarado en las fichas.

### Confirmación

`tests/test_pases_senadores.py` fija las fechas de los tres pases, que el registro tenga
fuente y tramos que no se pisan, y que la cohesión, el alineamiento y las bancas de LLA
los usen. `tests/test_descargar_series_cohesion.py` prueba que un año cerrado de otra
versión se vuelve a pedir.

## Pros y contras de las opciones

- Registro: corrige el dato con fuentes verificables; hay que mantenerlo a mano.
- Sacar a los que cambiaron: pierde votos reales y cambia el universo de provincias.
- Declararlo: deja un error conocido en tres indicadores del índice.

## Más información

Fuentes en el propio registro. Análisis del 28-oct-2026 con las actas del portal del
Senado de 2016 a 2026.
