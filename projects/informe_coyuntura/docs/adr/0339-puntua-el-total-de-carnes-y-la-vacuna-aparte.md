---
madr: 4
id: '0339'
estado: 'aceptado'
fecha: 2026-09-24
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [consumo_carnes_total, consumo_carne_vacuna, consumo_carnes_otras]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/gate_calidad.py', 'scripts/procedencia_anclas.py', 'scripts/descargar_series.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
supersede: ['0322']
relacionado: ['0216', '0217']
ambito: 'Cinturón vida cotidiana · ITCIS · qué carnes puntúan'
origen: 'Revisión de Luis del 23-sep-2026: «la idea era tener un indicador con las tres carnes sumadas y aparte el indicador de la carne como aspiracional; quedó por un lado aviar y porcina y por otro vacuna». Juan eligió el total más la vacuna aparte, mitad y mitad del peso.'
---

# ADR-0339 — Puntúan el total de las tres carnes y, aparte, la vacuna

## Contexto y planteo del problema

El apunte del 15-sep pedía «sumar el indicador de carne vacuna por separado».
ADR-0322 lo leyó como partir el total en dos —vacuna por un lado, aviar y
porcina por el otro— para que la vacuna no contara dos veces. El equipo quería
otra cosa: conservar el total de las tres carnes y **sumar** la vacuna como
indicador aspiracional, porque es el corte que el consumo argentino toma como
referencia y hoy está en su mínimo.

## Factores de decisión

- El total mide acceso a carne en general; la vacuna, el consumo aspiracional.
  Son dos preguntas distintas.
- Que la vacuna entre dos veces —dentro del total y sola— es el efecto buscado,
  no un error: le da peso propio al corte aspiracional.
- «O integra el índice o no es card» (ADR-0216): aviar + porcina no puede quedar
  como card si deja de puntuar.

## Opciones consideradas

1. Dejar vacuna + aviar/porcina (ADR-0322).
2. Total que puntúa y vacuna como dato dentro de su card.
3. Total y vacuna puntuando, mitad y mitad del mismo peso.

## Decisión

**Opción 3.** Puntúan `consumo_carnes_total` y `consumo_carne_vacuna`, con
0,0196 cada uno en la dimensión de ingresos y consumo antes de las cesiones
(1,53 % interno después de ellas, 0,43 % del ITCIS cada uno). Es el mismo 0,0392
que ya tenían entre las dos carnes: ningún otro componente cambia de peso, y la
dimensión sigue sumando exactamente 1,0. `consumo_carnes_otras` deja de puntuar
y de ser card; su nivel viaja dentro de la card del total (`otras_kg`), que es la
que cuenta la composición.

### Consecuencias

- Las dos series ya existían (faena del INDEC por categoría, base 100 = 4T-2023),
  así que la serie histórica del ITCIS se recalcula sin series nuevas.
- La ficha de aviar + porcina queda como histórica, con el registro del cambio.

### Confirmación

`tests/test_publicar.py` (componentes y pesos del ITCIS),
`tests/test_series_dimensiones.py` (card = serie) y
`tests/test_la_ficha_no_se_queda_atras.py`.
