---
madr: 4
id: '0407'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [privatizaciones, concesiones_infraestructura]
archivos: ['data/gestion/privatizaciones.json', 'data/gestion/privatizaciones_fechas.json', 'scripts/gestion.py', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'tests/test_gestion_privatizaciones_novedades.py', 'tests/test_gestion_adr0405_0407.py']
relacionado: ['0016', '0101', '0129', '0244', '0405', '0406']
ambito: 'ITCG · dimensión Privatizaciones e inversión · cartera de `privatizaciones`'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de los dobles conteos del cinturón de gestión.'
---

# ADR-0407 — Corredores Viales sale de la cartera de privatizaciones

## Contexto y planteo del problema

La cartera de `privatizaciones` promediaba nueve empresas, entre ellas Corredores
Viales (etapa 3). Su privatización es la concesión por peaje de la red vial (Decreto
97/2025): la Red Federal de Concesiones, que `concesiones_infraestructura` ya mide en
km adjudicados dentro de la misma dimensión. Los mismos actos —por ejemplo la Res. ST
80/2025, que adjudicó los tramos Oriental y Conexión— subían los dos indicadores a la
vez. Las fichas lo declaraban desde hoy como `dobleUso`.

## Factores de decisión

- Un hecho, un indicador.
- El indicador de concesiones mide la red con más detalle (km por etapa) que una etapa
  0-4.

## Opciones consideradas

- **Sacar Corredores Viales de la cartera (elegida).**
- Mantenerla y declarar el doble conteo.
- Sacar el indicador de concesiones y dejar Corredores Viales.

## Decisión

Corredores Viales sale de `empresas` en `privatizaciones.json` y en
`privatizaciones_fechas.json`; su último registro y sus transiciones quedan en
`fuera_de_cartera`, con el motivo. El detector de novedades del Boletín Oficial deja
de buscarla. La serie entera se recalcula con ocho empresas. Los `dobleUso` de las dos
fichas pasan a decir que ya no comparten hechos.

### Consecuencias

- Con las etapas de octubre de 2026 el avance pasa de 55,6 % a 53,1 % y su puntaje, de
  75,6 a 73,1. Junto con [[0406]], la dimensión Privatizaciones e inversión pasa de
  78,0 a 70,9.
- `concesiones_infraestructura` no cambia de valor.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_gestion_adr0405_0407.py` verifica que Corredores Viales no esté en la
cartera, ni en las transiciones, ni en los términos del detector, y que la serie
reproduzca la tarjeta.

## Pros y contras de las opciones

- Sacarla: elimina el doble conteo; la cartera pierde la única empresa vial, que el
  otro indicador mide mejor.
- Mantenerla: transparente pero sigue contando dos veces.
- Sacar concesiones: perdería el detalle por km.

## Más información

[[0405]] y [[0406]] son las otras dos decisiones de la misma revisión del cinturón.
