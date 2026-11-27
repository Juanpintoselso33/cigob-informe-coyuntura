---
madr: 4
id: '0444'
estado: 'aceptado'
fecha: 2026-11-27
cinturon: 'transversal'
archivos: ['scripts/archivo.py', '../../.github/workflows/mensual.yml', 'tests/test_archivo.py']
modifica: ['0359']
relacionado: ['0347', '0348', '0443']
ambito: 'Publicación mensual · el mes publicado queda con los datos que había el día en que salió'
origen: 'Pedido de Luis (24, 25 y 27-nov-2026): «mantener el atraso de los indicadores en el mismo nivel que la publicación anterior». Aprobado por Juan el 27-nov-2026.'
---

# ADR-0444 — El mes publicado queda con los datos del día en que salió

## Contexto y planteo del problema

Desde ADR-0359, el mes publicado (rama `mensual`, monitor.cigob.org) y sus fotos de `/archivo/` se rearman en
cada push. Se usa el código de hoy y las series de hoy cortadas por período (`fecha[:7] <= mes`). Con ese corte,
todo dato del mes que llega después de publicarlo entra igual. Por ejemplo, el informe de octubre salió el
29-oct y semanas después ya tenía el IPC de octubre (12-nov) y el EMAE de octubre (diciembre).

El atraso de cada edición dependía entonces de cuándo se miraba. Luis pidió que fuera siempre el mismo, y para
eso el día de publicación tiene que fijar también los datos (estudio en `docs/261127_dia_de_publicacion/`).

Además, la etiqueta `mensual-AAAA-MM` iba en la última corrida nocturna del mes (`mensual.elegir`). No iba en
el día en que se publicaba.

## Factores de decisión

- Que cada edición lleve los datos que había al publicarla, ni uno más.
- Que se siga leyendo con el método vigente (ADR-0359).
- Que un indicador nuevo no deje a los meses viejos sin card.

## Opciones consideradas

1. Cortar además por existencia: sólo entran los puntos de serie que ya existían en el commit de la
   publicación, con el valor de hoy.
2. Tomar los datos crudos tal como estaban en la publicación (el modo `desde="corrida"`).
3. Dejarlo como estaba.

## Decisión

**Opción 1.** `archivo._cortar` recibe el commit de la publicación (`congelado_en`):

- **Ese commit:** la etiqueta `mensual-AAAA-MM`. Mientras se publica todavía no existe la etiqueta, y lo pasa
  el workflow en `ARCHIVO_CONGELAR_EN`.
- **Series:** en cada CSV de `output/series/`, de los indicadores que ya estaban ese día, sólo quedan los meses
  que ya tenían dato. Va por mes y no por fecha, porque el punto del mes en curso lleva el día de la última
  observación (por ejemplo, 29-oct) y al cerrarse pasa a fin de mes (31-oct). Lo mismo para
  `web/src/data/series.json` y `data/historico/indicadores.json`.
- **Cards:** salen del último punto de esas series, así que también quedan como el día de la publicación.
- **Valor de cada punto:** es el de hoy. Así entran el método vigente y las revisiones de la fuente, pero no
  datos nuevos.
- **Indicadores que no existían al publicar:** quedan con su serie de hoy cortada al mes.

En `mensual.yml`, la etiqueta pasa a ponerse en `main` tal como está al apretar «publicar» (`git rev-parse
HEAD`). `mensual.elegir` queda sólo para comprobar que el mes está cerrado y para la foto de las cards exentas
de G3.

### Consecuencias

- monitor.cigob.org (octubre, etiqueta del 29-oct) y la foto de septiembre (etiqueta del 30-sep) vuelven a
  los datos que tenían al publicarse. Pierden lo que entró después, como el IPC y el resultado fiscal de
  octubre.
- Junio, julio y agosto no tienen etiqueta y siguen como antes.
- Un valor revisado por la fuente después de la publicación sí cambia la edición. Se acepta porque es el mismo
  dato del mismo mes.
- Un mes publicado antes de terminar (octubre, el 29-oct) toma el valor de fin de mes de los indicadores que
  ya tenían dato de ese mes: entran las votaciones del 30 y del 31. Con la publicación en el mes siguiente
  (estudio del día de publicación), el mes ya está cerrado y esto no pasa.

### Confirmación

`tests/test_archivo.py`:

- `test_el_mes_publicado_queda_congelado_como_el_dia_que_salio` prueba un dato llegado después (afuera), un
  indicador nuevo (adentro, cortado al mes), el valor de hoy y los tres archivos. Rompiendo el filtro, la
  prueba falla.
- `test_sin_etiqueta_ni_publicacion_en_curso_no_se_congela`.

## Pros y contras de las opciones

- **Opción 1.** A favor: el atraso queda fijo y se mantiene el método de hoy. En contra: un punto revisado
  después cambia el valor de la edición.
- **Opción 2.** En contra: con cambios de definición, el mes salía con métricas viejas. Pasó el 7-oct con
  junio, y por eso ADR-0359 dejó ese modo.
- **Opción 3.** En contra: el atraso dependía del día en que se mirara.

## Más información

El estudio del día de publicación está en `docs/261127_dia_de_publicacion/README.md`.
