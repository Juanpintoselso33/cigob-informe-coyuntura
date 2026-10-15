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
tres maneras según el servidor que atienda — completa, vacía (`count` 0) o
recortada. Medido el 15-oct con diez pedidos frescos por serie: el EMAE vino 7
veces con 271 filas y 3 con 167; la faena vacuna, 6 veces vacía. La misma URL
repetida devuelve la misma respuesta, buena o mala, así que repetir el pedido no
alcanza. Como la card y la serie de un indicador se piden en momentos distintos,
cada una puede caer en un servidor distinto, y el gate las encuentra desparejas.
El gate hizo bien en frenar: un recorte silencioso publicaría una serie corta.

## Factores de decisión

- No publicar una lectura a medias, sin congelar la corrida por una API que
  contesta bien la mayoría de las veces.
- Un solo lugar: había diez llamadas directas a la API repartidas en los
  colectores.
- No comerse el tope de tiempo de la corrida si la API está colgada.

## Opciones consideradas

1. Reintentar sólo cuando la respuesta viene vacía.
2. Pedir hasta que dos lecturas de la misma URL coincidan.
3. Varias lecturas, cada una con un parámetro propio que la manda a un servidor
   al azar, y quedarse con la de más filas.
4. Guardar el largo de cada serie y rechazar una lectura más corta que la anterior.

## Decisión

Opción 3, en `scripts/datos_gob.py` (`get`), por donde pasan las diez llamadas:
se juntan tres lecturas no vacías (hasta ocho pedidos) y gana la de más filas,
porque un servidor roto puede quitar filas pero no agregarlas. Si todas vienen
vacías, la última, y el colector sigue como antes (cache o error). Un error de
red se reintenta una sola vez, para no comerse el tope de tiempo de la corrida.
La 1 no detecta el recorte; la 2 se confirmaba con la caché (probada: devolvió
dos veces el EMAE de 167 filas); la 4 necesita estado entre corridas y falla
cuando una serie se revisa hacia atrás.

### Consecuencias

- Buena: una respuesta vacía o recortada no llega a la card ni a la serie.
- Mala: cada pedido a la API se hace al menos tres veces.

### Confirmación

`tests/test_datos_gob_lecturas.py`: una lectura vacía o recortada no se
devuelve, cada lectura es un pedido distinto, la red caída se reintenta una vez.
