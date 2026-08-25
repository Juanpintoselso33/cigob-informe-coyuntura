---
madr: 4
id: '0255'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [judicializacion]
archivos: ['scripts/itcp.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'tests/test_constructos_no_prometen_de_mas.py']
relacionado: ['0168', '0245']
ambito: 'Cinturón política · ITCP · `judicializacion` · por qué sale del score hasta tener un universo de causas'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «el corpus no identifica causas contra el PEN ni políticas de su agenda»'
---

# ADR-0255 — El corpus de SAIJ no identifica al Ejecutivo

## Contexto y planteo del problema

`judicializacion` publicaba **1,57%** bajo el rótulo **«Judicialización de la
agenda»**, y aportaba 4,6 sobre 10 de tensión al ITCP.

El número son **114 sumarios que mencionan «medida cautelar» sobre 7.273
publicados** por SAIJ en jurisdicción federal y nacional. Ese corpus es
jurisprudencia general: **no identifica causas contra el Poder Ejecutivo ni
contra políticas de su agenda**. Una cautelar en un juicio entre privados cuenta
exactamente igual que una que suspende un decreto.

Hay dos problemas superpuestos y conviene separarlos, porque sólo uno es
arreglable con un rótulo:

1. **La unidad es el sumario, no la causa.** Un mismo expediente puede generar
   varios sumarios y varios no generar ninguno; el sumario es una decisión
   editorial de la base.
2. **El universo no está acotado al Ejecutivo.** Este es el que rompe el
   constructo: por más que se afine la búsqueda de la frase, el denominador
   sigue siendo «lo que SAIJ publicó», que no tiene relación con la agenda de
   gobierno.

El indicador ya sabía algo de esto: publica proporción y no conteo justamente
porque el volumen que la base publica varía por razones editoriales —se
quintuplica entre 2016 y 2021—. Esa precaución es correcta y no alcanza: corrige
el denominador contra sí mismo, no contra el fenómeno.

## Factores de decisión

- **Un porcentaje sobre un corpus que no contiene el fenómeno no lo mide**, por
  más limpio que sea el conteo.
- **Aportaba tensión alta** (4,6/10) sobre una inferencia que no se sostiene.
- **La fuente tiene además un problema conocido de acceso**: SAIJ bloquea por IP
  a los runners casi todas las noches, así que el indicador ya venía
  refrescándose a mano.

## Opciones consideradas

- **A — Renombrarlo** a «Densidad de menciones cautelares en sumarios SAIJ» y
  dejarlo puntuando.
- **B — Sacarlo del score** y conservarlo como seguimiento hasta rediseñarlo.
- **C — Construir el universo de causas** contra actos o políticas del Ejecutivo.

## Decisión

**Opción B**, con el rótulo corregido de todos modos.

Sale del ITCP por el mecanismo de
[[0245-suspender-libera-el-peso-y-el-indice-renormaliza-solo]]: libera su 20% de
la dimensión de Poder Judicial, y `cobertura_judicial`, `velocidad_resolucion` y
`paralisis_denuncias` absorben el hueco en proporción, sin que se toque la tabla
de pesos.

La opción A es la que la auditoría plantea como mínima, y acá no alcanza. Un
rótulo honesto —«densidad de menciones cautelares en sumarios SAIJ»— describe
bien el dato, pero **para puntuar hay que decidir en qué dirección**: más
menciones cautelares en la jurisprudencia general, ¿es peor gobierno? La
pregunta no tiene respuesta fundada, y es el mismo razonamiento por el que
`sentimiento_digital` salió en la Entrega 2
([[0248-el-volumen-de-busquedas-no-tiene-valencia]]). Renombrar movería el
problema del título al signo.

El rótulo se corrige igual —pasa a «Densidad de menciones cautelares en sumarios
SAIJ»— porque el indicador se sigue relevando y su serie se sigue publicando.

**Condición de reingreso**: un universo de causas contra actos o políticas del
Poder Ejecutivo, con unidad **caso/expediente** —no sumario—, deduplicación,
estado procesal y corte temporal declarado.

### Consecuencias

- La dimensión de Poder Judicial pasa de cuatro componentes a tres. El ITCP
  **sube** —el indicador aportaba tensión alta— y eso hay que leerlo como lo que
  es: se dejó de puntuar una inferencia sin respaldo, no bajó la conflictividad
  judicial.
- Con ésta son **cuatro** los indicadores fuera del score en política junto con
  `apoyo_empresario`, más los cinco de contexto previos.
- El bloqueo por IP de SAIJ deja de afectar al índice: el indicador que dependía
  de esa fuente ya no puntúa.

### Confirmación

`tests/test_constructos_no_prometen_de_mas.py` y
`tests/test_suspension_libera_el_peso.py`:

- no puntúa, no pesa y no se muestra;
- los otros tres de la dimensión absorben su peso **en proporción**;
- el rótulo ya no dice que mide la agenda del Ejecutivo;
- la condición de reingreso exige causas contra el Ejecutivo y unidad de
  expediente, no de sumario.

## Pros y contras de las opciones

### A — Renombrar y dejarlo puntuando

- Bueno, porque conserva la serie continua dentro del índice.
- Malo, porque puntuar exige un signo y el signo no está fundado: más cautelares
  en la jurisprudencia general no dice nada sobre el gobierno.

### B — Sacarlo del score

- Bueno, porque deja de puntuar una inferencia que el corpus no sostiene.
- Malo, porque la dimensión de Poder Judicial queda con tres componentes y más
  concentrada en la cobertura de vacantes.

### C — Construir el universo de causas

- Bueno, porque es la medición que el nombre prometía.
- Malo, porque exige identificar demandado, materia y estado procesal por
  expediente: es un proyecto de datos, no una corrección.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_politica.md`.
