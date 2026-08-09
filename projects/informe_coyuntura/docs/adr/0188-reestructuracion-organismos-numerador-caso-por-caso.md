---
madr: 4
id: '0188'
estado: 'aceptado'
fecha: 2026-08-09
cinturon: 'gestion'
indicadores: [reestructuracion_organismos]
continua: ['0185']
ambito: 'ITCG · `reestructuracion_organismos` · numerador (casos que cuentan)'
origen: 'ADR-0185 dejó declarado, sin resolver, un hallazgo de la lectura caso por caso que pidió CIGOB: "7 de los 18 documentos (39%) son ruido o corresponden a actos hoy sin efecto — un problema de calidad del numerador, no del denominador... Queda declarado para que alguien lo retome."'
---

# ADR-0188 — `reestructuracion_organismos`: el numerador cuenta solo cierres vigentes de organismos públicos, caso por caso

## Contexto y planteo del problema

ADR-0185 resolvió el problema de ETIQUETA de `reestructuracion_organismos`
(hablar solo de disolución/cierre, no de fusión/transformación) sin tocar el
CÁLCULO, y de paso hizo la lectura caso por caso de los 18 actos que pidió
CIGOB. Esa lectura encontró que el cálculo mismo tenía un problema distinto,
que quedó **declarado y sin resolver a propósito**, para no mezclar dos
correcciones en un mismo cambio: de los 18 documentos que la búsqueda de
InfoLeg `texto="disolucion"` cuenta desde dic-2023,

- **3 son falsos positivos**: la búsqueda de texto no distingue de qué habla
  la norma, solo si contiene la palabra.
- **4 son actos de un paquete de decretos que el Congreso rechazó** en
  agosto de 2025 — eran cierres genuinos en el momento en que se dictaron,
  pero dejaron de serlo.

Este ADR retoma ese hallazgo y lo resuelve: define qué cuenta, con qué
mecanismo, y qué pasa cuando aparece un caso todavía sin revisar.

## Factores de decisión

- CIGOB pidió explícitamente "ir caso por caso" (origen de ADR-0185). Un
  filtro de texto más estricto (agregar palabras prohibidas, exigir que
  "disolución" aparezca cerca de "organismo") seguiría siendo una heurística
  automática, no una revisión caso por caso — resolvería estos 7 casos
  concretos y dejaría el mismo riesgo abierto para el próximo falso positivo
  con otras palabras.
- Son dos problemas de naturaleza distinta y conviene no tratarlos con el
  mismo mecanismo:
  - **Falso positivo** = nunca fue un cierre de un organismo público. Es un
    error de alcance, permanente: no hay ningún hecho futuro que lo revierta
    ni lo confirme, solo hace falta leer la norma una vez.
  - **Rechazado por el Congreso** = SÍ fue un cierre genuino, y dejó de
    serlo por un acto posterior. Es un estado, no un error: el mismo tipo de
    hecho puede volver a ocurrir (Congreso rechaza un DNU) o revertirse (el
    Congreso podría en el futuro convalidar una reforma equivalente por ley).
- El precedente directo en este mismo cinturón es `privatizaciones`: fuente
  automática (Boletín Oficial) para DESCUBRIR candidatos +
  `detectar_novedades_privatizaciones()` que avisa sin clasificar + un
  registro CURADO (`privatizaciones.json`, `privatizaciones_fechas.json`)
  que el colector solo lee, con cada etapa respaldada por su norma. Ese
  patrón ya resuelve exactamente el problema de este ADR: cómo automatizar
  el descubrimiento sin automatizar el juicio.
- Perder la búsqueda automática de InfoLeg no es aceptable: es lo único que
  avisa cuando el Gobierno cierra un organismo nuevo. La corrección tiene
  que preservarla como mecanismo de DESCUBRIMIENTO.
- Toda exclusión tiene que quedar auditable —con su motivo y su norma—, no
  ser un número ajustado a mano sin rastro.
- Qué hacer con un hallazgo de la búsqueda que todavía nadie clasificó es una
  decisión de diseño explícita, no un default accidental: contarlo por
  defecto arriesga repetir exactamente el defecto que este ADR corrige (un
  candidato nuevo puede ser el próximo falso positivo); no contarlo arriesga
  subestimar el avance real hasta que alguien lo revise. Ver "Decisión".

## Opciones consideradas

- **Filtro de texto más estricto** (excluir "obra social", "sociedad civil",
  exigir coincidencia con un listado de organismos conocidos) — descartada:
  sigue siendo una heurística automática sobre palabras, el objetivo
  explícito que CIGOB pidió abandonar para este indicador. Además no
  resuelve el problema de los actos rechazados por el Congreso, que sí
  hablan de un organismo público real.
- **Ajustar el numerador a mano una sola vez** (de 18 a 11, sin dejar
  mecanismo) — descartada: resuelve el número de hoy y no dice nada sobre
  el próximo hallazgo de la búsqueda; la contaminación original volvería a
  ocurrir en silencio la primera vez que InfoLeg indexe una norma nueva con
  "disolución" que no sea un cierre válido.
- **Registro curado caso por caso (mismo patrón que `privatizaciones`) +
  InfoLeg como descubrimiento + lo no clasificado se avisa y no cuenta** —
  elegida.

## Decisión

`fetch_reestructuracion_organismos()` deja de usar `_infoleg_post()` (un
conteo agregado sobre un rango de fechas) y pasa a enumerar mes a mes con
`_infoleg_buscar_mes("disolucion", ...)` — la misma función que ya usan
`desregulacion_normativa` y `detectar_novedades_privatizaciones()`, elegida
por la misma razón: el buscador de InfoLeg no pagina de forma estable con un
rango largo, así que hay que pedirlo mes a mes.

Cada norma que la búsqueda encuentra se contrasta contra un registro
CURADO nuevo, `data/gestion/reestructuracion_organismos_normas.json`, que
el colector solo LEE (igual que `privatizaciones.json` — clasificar una
norma es juicio del analista, no algo que el código pueda inferir del
texto):

```json
"414868": {
  "estado": "excluido",
  "motivo": "rechazado_congreso",
  "titulo": "Decreto 461/2025",
  "detalle": "Disponía la disolución de la Dirección Nacional de Vialidad, ...
              Confirmado en vivo en InfoLeg (09-ago-2026), en la propia
              página del decreto: 'DECRETO RECHAZADO POR EL ARTICULO 1º DE
              LA RESOLUCION 94/2025 DE LA HONORABLE CAMARA DE DIPUTADOS ...
              ABROGADO CONFORME LO DISPUESTO POR ARTICULO 24 DE LA LEY N°
              26.122'. Los tres organismos siguen existiendo."
}
```

Tres estados posibles por norma:

- **`"vigente"`** → cuenta en el numerador.
- **`"excluido"`**, con `motivo` (`"falso_positivo"` o `"rechazado_congreso"`)
  y `detalle` con la evidencia → no cuenta, y queda en la card pública
  (`excluidas`) para que la exclusión sea auditable, no un número que
  desapareció sin rastro.
- **Ausente del registro** ("sin clasificar") → **no cuenta**, y la corrida
  lo avisa: un `[WARN]` en el log del colector y un campo `sin_clasificar`
  en la card, con el id, el título y el período de InfoLeg. Nunca se suma ni
  se descarta en silencio.

### Por qué "no cuenta" y no "cuenta" es el default más seguro

Sobre los 18 casos conocidos, contar por defecto lo no clasificado hubiera
significado seguir sumando los 3 falsos positivos y los 4 actos rechazados
hasta que alguien los revisara a mano — es decir, reproducir el defecto
exacto que motiva este ADR cada vez que aparezca un caso nuevo. No contarlo
por defecto tiene un costo distinto y menor: el avance publicado puede
quedar circunstancialmente por debajo del real durante el tiempo que tarda
alguien en clasificar un hallazgo nuevo, pero ese costo es visible (queda en
`sin_clasificar`, no oculto) y transitorio (se corrige agregando una entrada
al registro). Subestimar de forma visible y transitoria es preferible a
sobreestimar de forma invisible y permanente.

### HONESTIDAD SOBRE EL EFECTO

Este cambio mueve el ITCG publicado, y lo mueve en la dirección de mostrar
la reforma del Estado MENOS avanzada. Con los datos vigentes en
`output/cache/gestion.json` al momento de este ADR (recalculado con
`itcg.calcular_itcg()`, sin regenerar ningún snapshot):

| | antes (18 actos, sin revisar) | ahora (11 actos, caso por caso) |
|---|---:|---:|
| `reestructuracion_organismos` (avance) | 40,0% | **24,4%** |
| puntaje del indicador (interpolado) | 52,5 | **23,2** |
| `reforma_estado` (dimensión) | 88,1 | **80,8** |
| ITCG | 78,7 | **76,8** |

El ITCG baja 1,9 puntos y la dimensión `reforma_estado` baja 7,3 puntos. La
banda del ITCG ("Moderadamente aflojado") no cambia — 76,8 sigue en el mismo
tramo que 78,7. La dirección del cambio no es ambigua: hace que la agenda de
reformas del Estado se vea menos ejecutada, no más. Es el resultado correcto
si el numerador estaba inflado, y lo estaba: 7 de 18 documentos (39%) no
eran cierres vigentes de un organismo público en ningún sentido razonable.
La corrección no se ajustó buscando este resultado — se hizo la lectura
caso por caso primero (en ADR-0185, meses antes de saber que se iba a
actuar sobre ella) y el número cayó adonde cayó.

### Confirmación

Antes de tocar código se reprodujo la búsqueda de InfoLeg en vivo
(`_infoleg_buscar_mes("disolucion", anio, mes)` para los 33 meses entre
dic-2023 y ago-2026): devolvió exactamente los mismos 18 documentos que
ADR-0185 había leído a mano, con los mismos ids. Se volvió a bajar el texto
completo de cada uno de los 18 desde `verNorma.do?id=...` — no solo el
`norma.htm` de anexos, que devuelve 404 para las resoluciones de personal
— y se confirmó, con la propia página de InfoLeg y no por una fuente
secundaria, algo que ADR-0185 no había citado directamente: el campo
"Observaciones" del Decreto 461/2025 y de sus tres resoluciones de personal
derivadas (1044/2025, 1217/2025, 1240/2025) trae explícito
"RECHAZADO POR..." / "ABROGAD[O/A] POR EL ARTICULO N° DE LA RESOLUCION
1343/2025 DEL MINISTERIO DE ECONOMIA" — el propio InfoLeg, no una
reconstrucción externa, dice que esos actos están sin efecto. La
clasificación de ADR-0185 (11 vigentes / 3 falsos positivos / 4 rechazados)
se sostiene sin cambios frente a la fuente en vivo.

`python -m pytest tests/ -k reestructuracion` corre:
`test_gestion_reestructuracion.py::test_el_registro_curado_pinea_las_exclusiones`
(el registro tiene exactamente 18 normas, 11 vigentes y 7 excluidas —
3 falsos positivos + 4 rechazados por el Congreso — así que una edición que
borre una exclusión sin querer lo nota) y
`test_gestion_reestructuracion.py::test_lo_no_clasificado_no_cuenta_y_se_avisa`
(con `_infoleg_buscar_mes` simulado, una norma ausente del registro queda
afuera del conteo y aparece en `sin_clasificar`).

No se corrió el pipeline ni se regeneró ningún snapshot: `git status
--short` al cierre de esta sesión no tiene cambios en `output/`,
`web/src/data/` ni `data/historico/`.

## Pros y contras de las opciones

**Filtro de texto más estricto**

- Bueno: no requiere mantener un registro nuevo.
- Malo: sigue siendo la misma heurística automática que CIGOB pidió dejar
  de usar para este indicador; no resuelve el caso de los actos rechazados
  por el Congreso (que sí hablan de un organismo público real, así que
  ningún filtro de palabras los distingue de uno vigente).

**Ajuste manual único (18 → 11), sin mecanismo**

- Bueno: cero código nuevo.
- Malo: no dice nada sobre el próximo hallazgo de InfoLeg; la contaminación
  original se repite la primera vez que aparezca una norma nueva.

**Registro curado + InfoLeg como descubrimiento + lo no clasificado se avisa
(elegida)**

- Bueno: mismo patrón ya probado por `privatizaciones` en el mismo cinturón;
  cada exclusión queda con su motivo y su norma, auditable.
- Bueno: un hallazgo nuevo nunca se pierde (queda en `sin_clasificar`) ni se
  suma sin revisar.
- Malo: agrega un archivo más para mantener a mano; si nadie revisa
  `sin_clasificar` durante mucho tiempo, el avance publicado queda
  subestimado de forma visible pero no corregida.

## Más información

### Qué no cambia

El denominador (`ORGANISMOS_PLAN_TOTAL = 45`) no se toca — ADR-0185 ya lo
revisó a fondo en la misma ronda y decidió mantenerlo como convención
calibrada. Este ADR es exclusivamente sobre qué normas entran al numerador.

### Riesgo declarado: el registro no se revisa solo

Igual que `privatizaciones.json`, el registro es responsabilidad de un
analista. Si InfoLeg indexa una norma nueva con "disolución" y nadie la
clasifica, el indicador la deja fuera del conteo indefinidamente (visible en
`sin_clasificar`, pero sin vencimiento automático que fuerce su revisión) —
mismo tipo de limitación que ADR-0129 declaró para el detector de
privatizaciones.
