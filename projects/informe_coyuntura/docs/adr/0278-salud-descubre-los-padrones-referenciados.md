---
madr: 4
id: '0278'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [libertad_opcion_salud]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'tests/test_sss_archivos_vigentes.py']
relacionado: ['0016', '0272']
ambito: 'Actualidad y correspondencia temporal de los padrones de salud'
origen: 'Auditoría integral contra el portal de estadísticas SSS'
---

# ADR-0278 — Salud descubre los padrones referenciados por el portal

## Contexto y planteo del problema

Los nombres fijos respondían correctamente pero terminaban en marzo (RNAS) y
enero (RNEMP). El portal referenciaba archivos con sufijo `.14.08`, ambos con
datos hasta junio. RNAS tenía enlace activo; RNEMP conservaba `blank:#` delante
de la URL, aunque el archivo público respondía y contenía el padrón revisado.

## Factores de decisión

- Una respuesta HTTP exitosa no demuestra actualidad del archivo.
- La tarjeta y la serie deben descubrir y leer los mismos archivos.
- La referencia inactiva y las fechas distintas deben quedar explícitas.

## Opciones consideradas

- Cambiar a otro nombre fijo: vuelve a quedar obsoleto en una nueva edición.
- Leer sólo enlaces activos: perdería RNEMP sin explicar la referencia existente.
- Descubrir referencias del portal, validar el archivo y declarar su estado.

## Decisión

Se buscan referencias que correspondan al padrón y año dentro de la ruta
oficial. Se admiten sufijos numéricos; varias referencias distintas para el
mismo padrón y año producen advertencia por ambigüedad, sin elegir por orden
HTML. Una referencia con `blank:#` se identifica como inactiva: que su archivo
sea accesible no se presenta como prueba de publicación activa.

La tarjeta y la serie comparten el descubrimiento. Un fallo del archivo
referenciado no habilita un retorno silencioso al archivo fijo viejo. Se
conserva el resultado previo marcado como desactualizado. Sólo se consulta el
año anterior cuando el portal no referencia el actual.

El denominador de la tarjeta no puede corresponder a un mes posterior al RNAS.
Se publican ambas fechas. Junio resulta de 2.754.461 beneficiarios derivados a
65 prepagas y 8.332.458 usuarios RNEMP: 33,1%, frente al 31,8% anterior.

## Pros y contras de las opciones

Recupera actualidad y revisiones históricas sin cambiar bandas ni pesos. La
razón sigue combinando registros distintos; con rezagos desiguales no equivale
a una medición simultánea. La referencia RNEMP inactiva conserva una salvedad
de publicación que el monitor debe mostrar, aunque pueda verificar el archivo.

## Más información

[Portal SSS](https://www.argentina.gob.ar/sssalud/estadisticas).
URLs, fechas y hashes quedan en la auditoría del 8-sep-2026. Los tests verifican
sufijos, referencias inactivas, ambigüedad, fallo de archivo y ausencia de
denominador futuro, además del acuerdo entre tarjeta y serie.
