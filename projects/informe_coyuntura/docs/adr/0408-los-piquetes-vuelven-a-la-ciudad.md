---
madr: 4
id: '0408'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [protocolo_antipiquetes]
archivos: ['data/gestion/dp_piquetes.json', 'data/gestion/manuales.json', 'scripts/gestion.py', 'scripts/descargar_series.py', 'scripts/itcg.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_piquetes_detector.py', 'tests/test_serie_piquetes_anio_cerrado.py', 'tests/test_gestion_adr0405_0407.py']
supersede: ['0405']
relacionado: ['0025', '0294', '0366', '0395']
ambito: 'ITCG · dimensión Reforma social y orden · universo de `protocolo_antipiquetes`'
origen: 'Decisión de Juan del 28-oct-2026: estaba decidido mantener la Ciudad de Buenos Aires, y ADR-0405 la cambió por el total del país.'
---

# ADR-0408 — Los piquetes vuelven a la Ciudad de Buenos Aires

## Contexto y planteo del problema

[[0405]] pasó `protocolo_antipiquetes` de la Ciudad de Buenos Aires al total nacional de
cortes de Diagnóstico Político. Juan ya había decidido mantener la Ciudad, y el cambio
se hizo contra esa decisión. Además, la tarjeta y la ficha no decían con claridad que la
fuente es una consultora privada, y el estado judicial del protocolo tenía que
verificarse otra vez.

Estado judicial verificado el 28-oct-2026:

- Dic-2025: el juez federal Martín Cormick declaró nula la Res. 943/2023 en el amparo del
  CELS; el Gobierno apeló con efecto suspensivo y el protocolo se siguió aplicando.
- 31-mar-2026: la Sala III de la Cámara Nacional de Apelaciones en lo Contencioso
  Administrativo Federal (jueces Fernández y Morán, expediente CAF 48198/2023) revocó la
  nulidad y declaró legítima la resolución
  (https://www.palabrasdelderecho.com.ar/articulo/6652/Protocolo-antipiquetes-revocaron-la-declaracion-de-nulidad-y-validaron-la-medida).
- May-2026: la misma Sala concedió en parte el recurso extraordinario del CELS (cuestión
  federal sí, arbitrariedad no), lo que lleva el caso a la Corte Suprema
  (https://www.mdzol.com/politica/2026/5/19/la-corte-suprema-debera-decidir-la-constitucionalidad-del-protocolo-antipiquetes-1954403.html).
  No se encontró un pronunciamiento de la Corte.

El protocolo está vigente. La nota de `docs/pendientes-monitor.md` («anulado en primera
instancia y apelado») estaba desactualizada; la otra («la Cámara revocó la nulidad») es
correcta.

## Factores de decisión

- Respetar la decisión previa de Juan sobre el universo del indicador.
- Conservar la regla del año cerrado de [[0395]].
- Que la tarjeta y la ficha digan qué tipo de fuente es y en qué estado está el protocolo.

## Opciones consideradas

- **Volver a la Ciudad y conservar los totales nacionales como contexto (elegida).**
- Mantener el total nacional de [[0405]].

## Decisión

El indicador vuelve a medir la Ciudad: reducción = (1 − cortes en la Ciudad del último
año cerrado / 931) × 100, con la base 2023 estimada desde la participación publicada y
declarada así. Las bandas no se mueven (las mismas de [[0405]], convención declarada). La
serie sigue la regla de [[0395]]. Los diez totales nacionales verificados se quedan en
`data/gestion/dp_piquetes.json` como contexto, sin puntuar. La fuente de la tarjeta dice
«consultora privada», y la ficha declara las limitaciones de la fuente, que el universo
es la Ciudad y el estado judicial fechado. Los piquetes salen de `METODO_NUEVO_DESDE` en
`publicar.py`: vuelven al alcance de sus meses viejos.

### Consecuencias

- Con los datos de octubre de 2026 la tarjeta vuelve de 52,7 % (país, 2025) a 74,2 %
  (Ciudad, 2025) y su puntaje, de 77,2 a 99,0. Reforma social y orden, de 90,9 a 99,6; el
  índice de gestión, de 78,6 a 79,5.
- La serie vuelve de 27,2 (2025) / 52,7 (2026) a 52,7 / 74,2.
- El respaldo de `manuales.json` vuelve a 74,2.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_gestion_adr0405_0407.py` fija que la tarjeta y la serie usan la Ciudad, que
la fuente dice «consultora privada», que la ficha registra el estado judicial y que los
textos no dicen «país»; `tests/test_serie_piquetes_anio_cerrado.py` y
`tests/test_piquetes_detector.py` fijan los valores de la Ciudad.

## Pros y contras de las opciones

- Ciudad: es lo decidido y tiene la serie que se publicó desde julio; la base 2023 es
  estimada y el universo es menor que el del protocolo, las dos cosas declaradas.
- País: universo del protocolo y base contada, pero contradice una decisión tomada.

## Más información

[[0025]] creó el indicador; [[0294]] declaró la base estimada; [[0366]] puso el estado
judicial en la tarjeta; [[0395]] fijó el año cerrado; [[0405]] queda superado.
