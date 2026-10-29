---
madr: 4
id: '0389'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [ocupacion_eph]
archivos: ['scripts/vida_cotidiana/collectors/padron_arca.py', 'scripts/vida_cotidiana/padron_arca_backfill.py', 'scripts/vida_cotidiana/main.py', 'scripts/publicar.py', 'data/vida/arca_empleadores.json', '.github/workflows/data-pipeline.yml', 'web/src/lib/fichas.ts']
relacionado: ['0383', '0412']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Empleo'
origen: 'Reunión del 26-oct-2026 (Luis Babino): «el padrón de ARCA de inscriptos como empleadores, incluidos los que no tienen personal a cargo», como complemento de la ocupación de la EPH. Decisión de Juan del 27-oct-2026: guardar la cantidad todos los meses, mostrarla dentro de la explicación de ocupacion_eph sin puntuar, y puntuar recién con 12 meses de historia.'
---

# ADR-0389 — El padrón de empleadores de ARCA acompaña a la ocupación

## Contexto y planteo del problema

ADR-0383 dejó afuera el padrón de ARCA por creer que no tenía serie pública
reproducible. Sí hay un archivo público: ARCA publica un zip con un registro por
CUIT, sin nombres, con la marca de empleador, que reemplaza cada semana. No
conserva los anteriores, pero el Internet Archive guardó cinco copias contables
(ago-2014 y mar-2015, sin nombres la segunda; jun-2020, abr-2021 y ago-2024, con
nombres), de las que se pueden contar los mismos campos. Hay copias de 2011-2012
en otro formato que no se usan: no está verificada la posición de la marca.

## Factores de decisión

- Que el dato sea reproducible por cualquiera, sin guardar CUIT ni nombres.
- No puntuar con una serie que todavía no existe: «o integra el índice o no es
  card», y por eso va dentro de la explicación de `ocupacion_eph`, no como card.
- No inventar una base del mandato: no hay copia de dic-2023.

## Opciones consideradas

- **Dato dentro de la explicación de `ocupacion_eph`, sin puntuar (elegida).**
- Card propia que no puntúa (descartada por la regla de las cards).
- Puntuar ya con los cuatro puntos disponibles (descartada: no hay serie mensual).

## Decisión

**Qué se cuenta.** CUIT con la marca de empleador activa (posición 19 del
registro), tengan o no personal declarado. Se desglosa en personas jurídicas
(CUIT 30/33/34), personas humanas y, de estas, monotributistas; se cuenta
también la marca en blanco (CUIT sin datos consistentes) y el total de CUIT.

**Cómo.** `collectors/padron_arca.py` baja el zip en streaming a un temporal, lo
cuenta por bloques y lo borra. Valida el largo del registro, el CUIT numérico y
una proporción plausible de empleadores; si no cierra, falla con un error claro
y el pipeline sigue con lo guardado. Nunca se guarda un CUIT.

**Registro.** `data/vida/arca_empleadores.json`: un valor por mes, el del último
archivo visto en el mes, con su fecha de archivo. Se commitea en el paso
«Commitear snapshot + caches a main». Semilla: oct-2026 (archivo del 24-oct) más
cinco puntos del Wayback (`padron_arca_backfill.py`, que cualquiera puede correr
para verificarlos).

**Dónde se ve.** En el detalle de la card `ocupacion_eph`, con el desglose y la
variación contra el punto anterior. Con los datos de hoy: de ago-2024 a oct-2026
los empleadores bajan 41.210 (−7,5 %), casi todo en personas humanas
(259.344 a 220.950); las jurídicas bajan poco (293.713 a 290.897). La marca en
blanco bajó de 275.007 a 48.391, por lo que una limpieza del padrón puede mover
los conteos; el texto lo advierte.

**Condición para puntuar.** 12 meses de registro mensual (desde oct-2026), con
ADR propio. Hasta entonces no entra a ningún índice ni cambia pesos.

### Consecuencias

- Es una marca de inscripción, no de empleo efectivo.
- Los puntos del Wayback no son una serie mensual y no tienen base del mandato:
  sirven de contexto, no de comparación contra 2023.
- Si ARCA cambia el formato, el colector falla en voz alta y el registro queda
  como estaba.

### Confirmación

`tests/test_padron_arca.py`: parser con fixture de líneas con CUIT cambiados,
rechazo de un formato roto, un valor por mes, y el texto de la card.

## Más información

Fuente: https://www.afip.gob.ar/genericos/cInscripcion/archivoCompleto.asp
(archivo sin nombres). Relevamiento del 27-oct-2026.
