---
madr: 4
id: '0210'
estado: 'aceptado'
fecha: 2026-08-18
cinturon: 'transversal'
archivos: ['config.py', 'scripts/gate_calidad.py', 'scripts/generar_informe.py']
relacionado: ['0133', '0191']
ambito: 'Gate G2 · flags del snapshot · indicadores que se refrescan a mano por política'
origen: 'judicializacion avisaba carry-forward todas las noches con el dato de un día'
---

# ADR-0210 — Un caché esperable no es carry-forward

## Contexto y planteo del problema

`politica.judicializacion` se refresca **a mano**: SAIJ bloquea por IP el rango
de egreso de los runners de GitHub. Eso ya está diagnosticado y decidido en
[[0191-frescura-del-fetch-y-no-solo-del-dato]], que le dio una ventana de 45
días sin fetch antes de que G2b corte la publicación.

Pero el resto del sistema no se enteró de esa decisión. Con el dato refrescado
hace **un día**, el pipeline igual producía:

    [AVISO] G2 politica: 1/18 en carry-forward
    flags: ["desactualizado:politica:judicializacion"]

Todas las noches, indefinidamente. El problema no es el ruido en sí: es que un
aviso que suena siempre deja de leerse, y ahí adentro se pierden los que sí
importan. Es la misma clase de falso positivo que
[[0133-una-fuente-demorada-no-tira-abajo-el-pipeline]] separó de una falla real,
sólo que un nivel más arriba — ya no "la fuente falló" sino "la fuente falla
como decidimos que falle".

Confirmado el 18-ago-2026 contra un runner: los cuatro variantes de header dan
403, incluido un User-Agent de browser completo. No es cuestión de headers y no
hay fuente oficial alternativa, así que el refresco manual no es un parche
temporal — es el régimen.

## Factores de decisión

- Un aviso tiene que significar "andá a mirar". Si suena siempre, no significa
  nada.
- Callar esto no puede callar una fuente que se rompe de verdad.
- El criterio del gate y el de los `flags` del snapshot no pueden discrepar.
- Nada de esto puede cambiar lo que ve el lector del sitio.

## Opciones consideradas

1. **Dejarlo como está** y acostumbrarse al aviso diario.
2. **Sacar `judicializacion` del conteo de carry-forward**, por nombre.
3. **Tolerancia por tiempo para todos**: nadie avisa hasta N días de caché.
4. **Tolerancia sólo para quien la tiene declarada**, y mientras esté adentro.

## Decisión

### 1. La exención pide ventana declarada Y estar adentro

`config.cache_es_esperable(indicador, dias_sin_fetch)` devuelve True sólo si el
indicador tiene entrada propia en `DIAS_SIN_FETCH` **y** su `obtenido_en` está
dentro de esa ventana. Un indicador sin entrada usa el default y sigue avisando
desde el primer día.

Es la opción 4. La 3 se descartó por lo que costaría: bajarle la guardia a todo
habría dejado muda por dos semanas una caída real, que es exactamente cómo se
perdió `sentimiento_digital` el 9-jul-2026. La 2 resuelve el caso y no la clase,
y deja el criterio escrito en el nombre de un indicador.

**Una entrada en `DIAS_SIN_FETCH` ahora declara dos cosas a la vez**: hasta
cuándo se tolera, y que este indicador anda por caché a propósito. No hacía
falta una tabla nueva: tener la entrada YA era esa declaración.

### 2. La tabla se muda a `config.py`

Vivía en `gate_calidad.py`. Ahora la consumen dos: el gate y
`generar_informe.py`, que arma los `flags`. Una política con dos dueños se
desincroniza — el mismo motivo por el que
[[0207-la-serie-comparable-es-una-vista-no-un-backfill]] mantiene los pesos en
un solo lado. El gate la sigue usando bajo sus nombres viejos
(`G2B_MAX_DIAS`), que ahora son alias.

### 3. Sin sello no hay ventana

`obtenido_en` ausente o ilegible → sin exención. Son los indicadores manuales y
los derivados de series, que no tienen fetch propio que medir y no pueden
reclamar una ventana que nadie les midió.

### 4. El sitio no cambia

Sólo se tocan el aviso del gate y los `flags` del snapshot, que son operativos
—los `flags` no los lee la web, sólo el archivo en BigQuery. El campo
`desactualizado` de cada indicador queda intacto, y con él la etiqueta del
modal que ve el lector.

### Consecuencias

- El pipeline nocturno deja de avisar por `judicializacion` mientras esté
  dentro de sus 45 días. Verificado: a 1 y a 30 días el gate sale limpio; a 60
  vuelve el aviso **y G2b falla**, que corta la publicación.
- `flags` queda vacío en las corridas normales, así que un flag en
  `corridas.flags` de BigQuery vuelve a ser una señal y no ruido de fondo.
- Agregar un indicador a `DIAS_SIN_FETCH` ahora tiene más peso que antes: no
  sólo corre el tope de G2b, también lo saca del aviso diario. Se agrega cuando
  el refresco manual es la política, no para tapar una fuente inestable.

### Confirmación

`tests/test_gate_cache_esperable.py`: el borde exacto (45 adentro, 46 afuera),
que sin declaración no hay exención, que sin sello tampoco, que pasada la
ventana vuelve a avisar y además corta, y que el gate y `generar_informe`
consumen el mismo objeto y no dos copias.

## Pros y contras de las opciones

- **Dejarlo**: cero código; entrena a ignorar los avisos.
- **Excluir por nombre**: resuelve el caso, no la clase.
- **Tolerancia para todos**: silencio parejo; enmascara caídas reales.
- **Ventana declarada** (elegida): el silencio es explícito y acotado; exige
  acordarse de declararla al agregar un indicador de refresco manual.

## Más información

- [[0191-frescura-del-fetch-y-no-solo-del-dato]] — `obtenido_en` y G2b.
- [[0133-una-fuente-demorada-no-tira-abajo-el-pipeline]] — el mismo corte, un
  nivel más abajo.
