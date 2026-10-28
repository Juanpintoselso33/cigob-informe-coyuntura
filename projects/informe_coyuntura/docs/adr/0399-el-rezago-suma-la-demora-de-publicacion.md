---
madr: 4
id: '0399'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [jornadas_individuales_no_trabajadas_12m, produccion_legislativa, conflictividad_nacional]
parametros: ['REZAGO_MESES_ITCP']
archivos: ['scripts/itcp.py', 'scripts/publicar.py', 'tests/test_itcp.py', 'web/src/lib/fichas.ts', 'docs/adr/0092-el-informe-declara-su-propio-rezago.md']
modifica: ['0092']
relacionado: ['0092', '0353', '0372', '0397']
ambito: 'ITCP · tarjeta «Rezago del índice» · regla de REZAGO_MESES_ITCP'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0399 — El rezago suma la demora de publicación

## Contexto y planteo del problema

La tarjeta de rezago del índice político ([[0092-el-informe-declara-su-propio-rezago]])
pondera, por peso efectivo, de cuándo es la situación que describe cada componente. La
regla de ADR-0092 era el centroide de la ventana —6 meses para una de 12— y decía que
los valores «se derivan del diseño de cada ventana, no se estiman».

En la práctica la regla se aplicaba de dos maneras. A las transferencias se les sumaba
el mes y medio del IPC ([[0353-armonia-federal-a-doce-meses-moviles]], 7,5 meses); a la
producción legislativa, la conflictividad y las jornadas no trabajadas, no. Las
jornadas tienen la ventana corrida tres meses (el dato de octubre de 2026 es el de
julio): describen la situación de hace nueve meses, no seis.

## Factores de decisión

- Una sola regla para todas las ventanas de 12 meses.
- Que la tarjeta no subestime cuán vieja es la foto.

## Opciones consideradas

- **Rezago = 6 + demora media de publicación, redondeado a 0,5 (elegida).**
- Mantener el centroide puro y sacar la demora de las transferencias.

## Decisión

Para toda ventana de 12 meses, **rezago = 6 + demora media de publicación de la fuente**,
redondeado a 0,5 meses. La demora es una estimación —la distancia típica entre el último
mes con dato y la consulta—, no un dato de diseño, y así lo dice ahora ADR-0092.

| indicador | antes | ahora | demora |
|---|---|---|---|
| `jornadas_individuales_no_trabajadas_12m` | 6 | 9 | ~3 meses de la planilla de Trabajo |
| `transferencias_no_automaticas` | 7,5 | 7,5 | ~1,5 del IPC |
| `conflictividad_nacional` | 6 | 7 | ~1: el mes en curso queda afuera |
| `produccion_legislativa` | 6 | 6,5 | ~0,5: meses completos del catálogo |
| ventanas que llegan hasta hoy (comunicados de cámaras, decretos, vetos, actas) | 6 | 6 | ninguna |

Los componentes que no son ventanas de 12 meses (cohortes, anuarios, stocks, ventanas
de 90 días) no cambian. El texto de la tarjeta lo explica: «más lo que tarda su fuente
en publicar».

### Consecuencias

- Con los pesos del snapshot del 28-oct-2026, el rezago promedio del índice pasa de 5,1
  a 5,3 meses. Las proporciones de pulso inmediato (36 %) y estructural (7 %) no cambian.
- No cambia ningún valor ni puntaje: es la lectura de la tarjeta.

### Confirmación

`tests/test_itcp.py::test_rezago_de_doce_meses_suma_la_demora_de_publicacion` fija los
cuatro valores, las ventanas que quedan en 6 y el redondeo a 0,5.

## Pros y contras de las opciones

- Sumar la demora: la tarjeta dice de cuándo es la foto de verdad; a cambio, la demora
  es una estimación y hay que revisarla si la fuente cambia de calendario.
- Centroide puro: sale sólo del diseño, pero subestima los componentes con fuentes
  lentas y obliga a quitar a las transferencias un mes y medio real.
