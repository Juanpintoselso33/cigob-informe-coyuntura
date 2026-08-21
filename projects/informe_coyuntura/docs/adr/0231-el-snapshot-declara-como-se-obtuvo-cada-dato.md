---
madr: 4
id: '0231'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'transversal'
archivos: ['scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/components/Metodologia.astro', 'tests/test_publicar.py']
relacionado: ['0211', '0220', '0227']
ambito: 'Campo `metodo_obtencion` del snapshot · badge de origen del dato · contador de la página de metodología'
origen: 'La web declaraba «Automático» sobre ocho datos que no avanzan sin una persona'
---

# ADR-0231 — El snapshot declara cómo se obtuvo cada dato

## Contexto y planteo del problema

`badgeEstado()` (`web/src/lib/datos.ts`) tenía dos salidas posibles para un
dato con valor: **«Estimación»** si era placeholder, y **«Automático»** para
todo lo demás. No era una lectura: era un `return` incondicional. Ocho
indicadores publicados salían rotulados «Automático» sin que ningún dato del
snapshot lo respaldara, y la página de metodología los contaba en su «N se
extraen automáticamente».

De esos ocho, ninguno es automático de punta a punta:

| Indicador | Qué hace la máquina | Qué no puede hacer sola |
|---|---|---|
| `apoyo_empresario` | baja los comunicados de AEA y UIA | codificar apoyo/crítica |
| `desafios_legislativos` | lee las actas de Diputados y Senado | resolver las actas ambiguas |
| `bloqueo_sostenido` | ídem, mismo registro | ídem |
| `reestructuracion_organismos` | detecta normas en InfoLeg | decidir cuáles cuentan |
| `fal_modernizacion_laboral` | sigue InfoLeg, el estado judicial y el registro de FCI | asentar el estado de la causa |
| `protocolo_antipiquetes` | levanta los monitoreos de Diagnóstico Político | clasificar el episodio |
| `velocidad_resolucion` | — | el anuario de la CSJN se releva a mano, una vez por año |
| `privatizaciones` | — | la etapa de cada proceso la asienta una persona |

El rótulo importa porque es lo único que el lector tiene para calibrar cuánto
pesa el criterio humano en un número. Un dato codificado por una persona y
presentado como extracción automática promete una objetividad que no hay.

La confusión de fondo es que **el badge no tenía de dónde leer**. `estado` del
snapshot es `placeholder` o nada; `desactualizado` dice que el fetch falló, no
cómo se obtiene el dato (ADR-0227); y la fuente es texto libre. La UI terminó
inventando el rótulo por descarte, que es el mismo antipatrón que
[[0220-la-ficha-se-ata-al-colector-y-al-adr]] arregló del lado de la ficha:
prosa publicada que afirma algo que nada verifica.

## Factores de decisión

- El contrato de los colectores **sí** es la automatización: el default correcto
  es «automático» y las excepciones son pocas y nombrables.
- Quien sabe cómo se obtiene un dato es el pipeline, no la capa de display. Una
  heurística en la web (por fuente, por `desactualizado`) volvería a inventar.
- Binario automático/manual no alcanza. `apoyo_empresario` no es carga manual
  —la detección y la descarga son automáticas— pero tampoco avanza sin una
  persona. Colapsarlo a «Carga manual» sería tan falso como «Automático», con
  el signo cambiado.
- El rótulo tiene que sobrevivir a los renombres de indicador, que en este
  proyecto son frecuentes.

## Opciones consideradas

- **Un campo `metodo_obtencion` en el snapshot, escrito por `publicar.py`,
  con default automático y una tabla de excepciones** — elegida.
- **Derivarlo en la web de la fuente o de `desactualizado`** — descartada: es
  la heurística que causó el problema, y `desactualizado` ya significa otra
  cosa (ADR-0227).
- **Que cada colector escriba su propia procedencia** — descartada por ahora:
  reparte la definición en cuatro archivos y la vuelve invisible de conjunto,
  que es justo lo que hace falta poder auditar de una mirada. Es la evolución
  natural si la lista crece.
- **Sólo dos valores, automático y manual** — descartada: ver arriba.

## Decisión

### 1. Tres valores, con un criterio escrito

`metodo_obtencion` acompaña a cada indicador del snapshot y vale:

- **`automatico`** — el valor viaja de la fuente a la card sin intervención.
- **`semiautomatico`** — la detección y la descarga son automáticas, pero
  **una clasificación humana es necesaria para que el valor avance**. El caso
  típico: lo inequívoco se resuelve solo y lo ambiguo espera triage (de ahí
  `pendientes_de_codificar`, `pendientes_triage`, `novedades_pendientes` en
  las cards).
- **`manual`** — no hay extractor: alguien releva y asienta el dato.

El default es `automatico`; las excepciones viven en
`METODO_OBTENCION_EXCEPCIONES` (`publicar.py`), en un solo lugar y con el
motivo al lado. `anotar_metodo_obtencion()` corre antes del scoring.

### 2. La web lee, no infiere

`badgeEstado()` pasa a devolver «Automático» · «Semiautomático» · «Carga
manual» · «Estimación» leyendo ese campo, y la página de metodología cuenta
las tres categorías en vez de afirmar que todo se extrae solo.

### Consecuencias

- Ocho cards cambian de rótulo y el contador de metodología baja: es el punto.
- Un indicador nuevo se publica como automático sin decir nada. Es el default
  correcto y, cuando no lo sea, hay que acordarse de anotarlo — ver
  «Limitaciones».
- El campo es del snapshot, así que queda archivado en BigQuery con cada
  corrida (ADR-0180) y se puede leer hacia atrás.

### Confirmación

`tests/test_publicar.py`, en tres capas que cubren cosas distintas:

- `test_el_snapshot_declara_la_procedencia_de_cada_indicador` — la función
  aplica el default y las ocho excepciones sobre un informe sintético.
- `test_ninguna_excepcion_de_procedencia_apunta_a_un_indicador_que_ya_no_existe`
  — una clave renombrada dejaría la excepción muerta y el dato volvería a
  badgearse «Automático» sin que nada avise. El snapshot publicado es el
  contrato.
- `test_el_snapshot_publicado_declara_la_procedencia_que_dictan_las_excepciones`
  — que el `informe.json` en disco esté efectivamente anotado. Sin esto,
  `anotar_metodo_obtencion()` podría dejar de llamarse en `main()` con los
  otros dos tests en verde.

## Más información

### Limitaciones de la guarda

Las tres capas vigilan la lista **hacia dentro**: que lo declarado sea cierto y
que ninguna entrada apunte al vacío. Ninguna la vigila **hacia fuera**. Si
mañana entra un colector con triage humano y nadie agrega su clave, el
indicador se publica como «Automático» y todo queda verde.

No hay señal automática que lo detecte: «esto necesita una persona» no está
escrito en ningún lado del código del colector de forma reconocible. El
disparador es el mismo que ADR-0220 le puso a la ficha —dar de alta un
indicador obliga a mirar esta lista— y por eso la tabla vive en un solo
archivo y no repartida en cuatro.

### Por qué no se reusó `desactualizado`

Es el error que ADR-0227 acababa de separar por escrito. `desactualizado` dice
que el fetch falló y se está sirviendo caché, o que el dato es de carga manual;
mezcla estado del pipeline con procedencia. La versión anterior de
`badgeEstado()` llegó a devolver «Carga manual» cuando el flag estaba
encendido, lo que hacía que un indicador automático con la fuente caída se
publicara como cargado a mano. `metodo_obtencion` no depende de si la corrida
de hoy anduvo.
