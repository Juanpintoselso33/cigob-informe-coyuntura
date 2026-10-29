---
madr: 4
id: '0412'
estado: 'aceptado'
fecha: 2026-10-29
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [ocupacion_eph]
archivos: ['scripts/vida_cotidiana/collectors/padron_arca.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'tests/test_padron_arca.py']
relacionado: ['0383', '0389']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Empleo'
origen: 'Decisión de Juan del 29-oct-2026: un dato que no puntúa no va dentro de la tarjeta ni de la descripción de otro indicador.'
---

# ADR-0412 — El padrón de ARCA se guarda y no se publica

## Contexto y planteo del problema

ADR-0389 sumó a la explicación de `ocupacion_eph` una oración con los
empleadores inscriptos en ARCA, un dato que no puntúa. El resultado fue una
tarjeta que mezclaba la tasa de empleo, que sí integra el índice, con un conteo
que no, y una ficha pública con las cifras del padrón y sus salvedades.

## Factores de decisión

- Un dato que no puntúa no va dentro de la tarjeta de otro indicador.
- ARCA reemplaza el archivo cada semana y no conserva historia: si no se guarda
  ahora, no se recupera.
- Ninguna cifra del padrón en la ficha pública.

## Opciones consideradas

- **Guardar todos los meses y no publicar (elegida).**
- Seguir mostrándolo dentro de la tarjeta.
- Dejar de descargarlo.

## Decisión

La tarjeta de `ocupacion_eph` queda sólo con la tasa de empleo. El colector
`padron_arca.py` sigue corriendo en cada corrida de vida cotidiana y el registro
mensual `data/vida/arca_empleadores.json` se sigue versionando, sin CUIT
individuales. `publicar.py` ya no lee el resultado del colector; la función que
sumaba la oración se reemplaza por una que sólo restaura la oración de la tasa si
el INDEC no contestó (y descarta la del padrón de los snapshots viejos). La ficha
pierde la transformación y la limitación que describían el padrón y suma una
entrada en `cambios`.

Si más adelante el padrón puntúa, entrará con un ADR propio y card o componente
propios, no como oración de otra tarjeta.

### Consecuencias

- El sitio no muestra nada del padrón; el archivo mensual sigue creciendo.
- Los snapshots anteriores conservan la oración vieja; la próxima corrida la
  reemplaza.

### Confirmación

`tests/test_padron_arca.py` verifica que la tarjeta no menciona el padrón, que el
registro se sigue escribiendo y que un INDEC caído restaura sólo la tasa.

## Pros y contras de las opciones

- Guardar y no publicar: la historia se acumula sin ruido en la tarjeta.
- Mostrarlo: informa, pero contradice la regla de que lo que no puntúa no entra
  dentro de otra tarjeta.
- Dejar de descargarlo: se pierde una historia que ARCA no conserva.

## Más información

ADR-0389 queda como registro del origen del colector y del registro mensual.
