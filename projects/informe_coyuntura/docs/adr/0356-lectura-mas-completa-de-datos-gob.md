---
madr: 4
id: '0356'
estado: 'aceptado'
fecha: 2026-10-15
cinturon: 'transversal'
archivos: ['scripts/datos_gob.py', 'scripts/macro.py', 'scripts/gestion.py', 'scripts/politica.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/vida_cotidiana/collectors/indec_series.py', 'scripts/vida_cotidiana/collectors/trabajo_independiente.py', 'scripts/vida_cotidiana/collectors/motorizacion.py', 'scripts/vida_cotidiana/collectors/indec_supermercados.py', 'tests/test_datos_gob_lecturas.py']
ambito: 'Colectores · lecturas de la API de series de datos.gob.ar'
origen: 'Cuatro corridas nocturnas caídas del 12 al 15-oct-2026'
---

# ADR-0356 — De datos.gob.ar vale la lectura más completa de varias

## Contexto y planteo del problema

Del 12 al 15-oct-2026 la corrida nocturna no publicó cuatro noches seguidas. La
primera se cortó por tiempo (la API no contestaba); las otras tres las frenó el
gate con fallas distintas cada noche: card ≠ serie en cinco indicadores de
macro, gestión e impacto social, y anclas del panel de impacto social sin el
4T-2023. Ningún indicador cambia de cálculo con esta decisión.

La causa es la API de series de datos.gob.ar: contesta 200 con la misma serie de
maneras distintas según el servidor que atienda — completa, vacía (`count` 0) o
recortada, a veces con filas vacías intercaladas. Medido el 15-oct: el EMAE vino
3 de 10 veces con 167 filas (103 vacías) en vez de 271, la faena vacuna 6 de 10
vacía, y hay series que ningún servidor devuelve enteras («otros gastos de
funcionamiento» del IMIG, 28 de 128 filas, hasta 2018). La misma URL repetida
devuelve la misma respuesta, buena o mala. Como la card y la serie de un indicador
se piden en momentos distintos, cada una cae en un servidor distinto y el gate las
encuentra desparejas. Hizo bien en frenar: con «otros gastos» recortado, la serie
de gasto de funcionamiento de agosto se calculaba sólo con salarios (−49,9).

Lo que no está roto es el catálogo, que con `metadata=full` dice cuántas filas tiene
cada serie (`time_index_size`), ni el CSV oficial de cada distribución, que las trae
todas (el de salarios coincide con la API al decimal).

## Factores de decisión

- No publicar una lectura a medias, sin congelar la corrida por una API que
  contesta bien la mayoría de las veces.
- Un solo lugar: había diez llamadas directas a la API repartidas en los
  colectores.
- No comerse el tope de tiempo de la corrida si la API está colgada.

## Opciones consideradas

1. Reintentar sólo cuando la respuesta viene vacía.
2. Pedir hasta que dos lecturas de la misma URL coincidan.
3. Varias lecturas a servidores al azar y quedarse con la de más filas.
4. Aceptar sólo la lectura con todas las filas que declara el catálogo y, si no
   llega, leer el CSV oficial.

## Decisión

Opción 4, en `scripts/datos_gob.py` (`get`), por donde pasan las diez llamadas.
Cada lectura lleva un parámetro propio (si no, contesta la misma respuesta);
hasta seis lecturas, y la primera completa gana. Si ninguna lo es, la respuesta se
arma desde el CSV de la distribución (`downloadURL`, columna `title`) con la misma
forma, orden y límite que la de la API. Un pedido de varias series (las quince
sectoriales del EMAE) se parte en pedidos de una y se vuelve a armar. Sin catálogo
en la respuesta, rige la opción 3. Un error de red se reintenta una sola vez, para
no comerse el tope de tiempo de la corrida.

La 1 no detecta el recorte; la 2 se confirmaba con la caché (devolvió dos veces el
EMAE de 167 filas); la 3 no alcanza cuando ningún servidor tiene la serie entera.

### Consecuencias

- Buena: una respuesta vacía o recortada no llega a la card ni a la serie.
- Buena: series que la API ya no servía enteras vuelven a estar al día (la faena
  vacuna llega a agosto de 2026; por la API, a junio).
- Mala: mientras la API siga así, varios pedidos por serie y algunos CSV por corrida.

### Confirmación

`tests/test_datos_gob_lecturas.py`: una lectura vacía o recortada no se
acepta, cada lectura es un pedido distinto, sin lectura completa se usa el CSV,
varias series se piden de a una, la red caída se reintenta una vez.
