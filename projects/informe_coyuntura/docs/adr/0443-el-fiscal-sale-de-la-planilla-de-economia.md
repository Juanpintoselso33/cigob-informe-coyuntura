---
madr: 4
id: '0443'
estado: 'aceptado'
fecha: 2026-11-27
cinturon: 'transversal'
indicadores: [resultado_primario, gasto_funcionamiento, ipc_alimentos]
archivos: ['scripts/imig_hacienda.py', 'scripts/ipc_indec.py', 'scripts/datos_gob.py', 'tests/test_ipc_indec.py', 'scripts/macro.py', 'scripts/gestion.py', 'scripts/descargar_series.py', 'tests/test_imig_hacienda.py', 'web/src/lib/fichas.ts']
relacionado: ['0187', '0403', '0414', '0444']
ambito: 'Fuentes · el último mes del resultado primario y del gasto de funcionamiento sale de la planilla de Economía'
origen: 'Estudio del día de publicación (docs/261127_dia_de_publicacion), aprobado por Juan el 27-nov-2026.'
---

# ADR-0443 — El último mes fiscal sale de la planilla de Economía

## Contexto y planteo del problema

El resultado primario (macro) y el gasto de funcionamiento (gestión) se leen de la API de datos.gob.ar, que
copia el Informe Mensual de Ingresos y Gastos (IMIG) de Hacienda con semanas de atraso:

| Mes | Comunicado de Economía | Entró al Monitor |
|---|---|---|
| Julio de 2026 | 18-ago | 3-sep |
| Septiembre de 2026 | 16-oct | 15-nov |
| Octubre de 2026 | 16-nov | al 27-nov la API seguía en septiembre |

Con el día de publicación del mes que se estudió, entre el 21 y el 25 del mes siguiente, el fiscal tiene que
estar adentro, y por la API no llega.

## Factores de decisión

- Que el dato entre la noche del comunicado.
- No coser dos fuentes que digan cosas distintas.
- Que una falla de la planilla no deje al indicador sin dato.

## Opciones consideradas

1. Completar la serie de la API con los meses que ya trae la planilla de Economía.
2. Pasar todo a la planilla.
3. Seguir con la API.

## Decisión

**Opción 1.** `scripts/imig_hacienda.py` hace lo siguiente:

1. Sigue el enlace del último mes en la página de información estadística de Hacienda. Los nombres de archivo
   no siguen ninguna regla y el formato varía: `.xlsx`, `.zip` o `.rar`.
2. Abre el IMIG: suelto, o dentro del `.zip` junto con el de base caja.
3. Lee la hoja «Mensualizacion», que trae el año en curso.
4. Suma a la serie de la API los meses posteriores a su último dato.

Si en un mes que tienen las dos los números difieren en más de 0,1 %, no se usa la planilla. Tampoco se usa si
el archivo es un `.rar` o no se puede leer. En esos casos queda la API, con un aviso en el log.

La historia sigue saliendo de la API, porque la planilla trae sólo el año en curso. Lo usan el colector de
macro, el de gestión y `descargar_series.py`, con el mismo enganche que `indec_actividad.py` para el IPI y el
ISAC.

### Consecuencias

- El fiscal llega entre el día 16 y el 18 del mes siguiente, no después del 15 del subsiguiente.
- Octubre de 2026 cambia las dos cards:

  | Indicador | Antes (con septiembre) | Con octubre |
  |---|---|---|
  | Resultado primario | 6,19 % de la recaudación | 6,53 % |
  | Gasto de funcionamiento | −27,8 % real | −28,2 % real |

- Si Economía cambia el armado del archivo, la planilla deja de leerse y se vuelve al atraso de la API sin
  romper nada. El aviso queda en el log, no en Slack.

### Confirmación

`tests/test_imig_hacienda.py` prueba:

- la lectura de la hoja;
- el IMIG dentro del `.zip`;
- el rechazo del `.rar`;
- el último mes de la página;
- que se completa sin pisar la API;
- que no se cose si no coinciden;
- que una falla vuelve a la API.

Verificado el 27-nov-2026 contra la API: agosto y septiembre son idénticos en las tres filas (resultado primario,
salarios y otros gastos de funcionamiento). Octubre da un resultado primario de $1.931.156 millones, el del
comunicado del 16-nov.

## Pros y contras de las opciones

- **Opción 1.** A favor: el dato llega el día del comunicado y la historia no cambia. En contra: un lector más
  que mantener.
- **Opción 2.** En contra: la planilla trae sólo el año en curso y no alcanza para la base 2023 ni para las
  anclas.
- **Opción 3.** En contra: el atraso es de hasta un mes.

## Más información

El estudio del día de publicación está en `docs/261127_dia_de_publicacion/README.md`.

### Las demás demoras del estudio

El estudio encontró otros cinco datos que entraron tarde. Se revisó cada uno:

| Dato | Estado |
|---|---|
| IPC general de septiembre | Resuelto el 20-oct (`b6981e6b`): se completa con la planilla del INDEC. Octubre entró el día de la publicación. |
| EMAE de agosto | Resuelto el 2-nov (`5cf9049a`, ADR-0417): sale de la API del propio INDEC. Septiembre entró al día siguiente. |
| Pobreza de la Di Tella de septiembre | Resuelto el 12-nov (`a5bfcd75`): el lector se adaptó al formato nuevo del informe. |
| Comercio exterior de julio | Desde agosto entra al día siguiente del INDEC: lee el cuadro original vigente (`ica.py`). |
| IPC de alimentos de septiembre | Seguía abierto y se arregla acá. Ver abajo. |

El IPC de alimentos (impacto social) se leía sólo de la API de datos.gob.ar. En octubre llegó a tiempo de
casualidad, pero septiembre había entrado tres semanas después del INDEC. Se le suma el mismo respaldo que tiene
el IPC general: `ipc_indec.py` lee también la fila «Alimentos y bebidas no alcohólicas» del bloque «Total
nacional» de la planilla, y `datos_gob.get` completa con ella la serie `146.3_IALIMENNAL_DICI_M_45`. Rige la
misma regla de no coser: el último mes de la API tiene que coincidir con la planilla.
