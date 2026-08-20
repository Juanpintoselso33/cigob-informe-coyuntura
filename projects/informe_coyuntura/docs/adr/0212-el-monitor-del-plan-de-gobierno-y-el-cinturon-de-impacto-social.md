---
madr: 4
id: '0212'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'transversal'
archivos: ['config.py', 'web/src/lib/datos.ts', 'web/src/lib/fichas.ts', 'scripts/publicar.py', 'scripts/manual_cinturon.py', 'scripts/fichas/generar.py', 'tests/test_siglas_publicas.py']
supersede_parcialmente: ['0190']
relacionado: ['0018', '0189']
ambito: 'Nombre público del producto, del cuarto cinturón y de su índice'
origen: 'Devolución de Luis Babino sobre el artifact de agosto, agosto de 2026'
---

# ADR-0212 — El producto es el Monitor del Plan de Gobierno y el cuarto cinturón es Impacto social

## Contexto y planteo del problema

[[0190-renombrar-los-indices]] dejó registrado que las siglas de los cuatro
índices no dicen qué miden y chocan con las de la UTDT, y **paró la decisión a
propósito**: los nombres nuevos son una decisión editorial de la Fundación, no
técnica. Quedó en `propuesto`, con tres cosas por definir y una instrucción
provisoria: *"mientras tanto, no se acuñan siglas nuevas con el mismo
patrón"*.

En agosto de 2026 llegó la primera de esas tres definiciones. La devolución
editorial sobre el artifact renombró dos cosas de cara al lector:

- el producto, de **Informe de Coyuntura** a **Monitor del Plan de Gobierno**;
- el cuarto cinturón, de **Vida cotidiana** a **Impacto social**, con lo que su
  índice pasa a llamarse *Índice de Tensión del Cinturón de Impacto Social*.

El renombre del cinturón no es cosmético: cambia lo que el cinturón declara
medir. "Vida cotidiana" describe un objeto —el bolsillo y la calle—; "Impacto
social" describe una **capacidad del proyecto de gobierno**, la de ser validado
en las urnas. Es el mismo movimiento que ya había hecho el marco al ordenar los
otros tres por capacidad (sustentabilidad intertemporal, validación normativa,
cumplimiento de compromisos).

La devolución mantuvo la sigla ITVC. Eso fue un descuido, no una decisión: una
sigla que se expande a "Vida Cotidiana" sobre un índice llamado "Impacto
Social" obliga al lector a saber de antemano que son la misma cosa, que es
exactamente el problema que ADR-0190 vino a nombrar.

## Factores de decisión

- **El identificador técnico no es el nombre público.** Es el primer factor que
  ya listaba ADR-0190, y sigue valiendo: renombrar de cara al lector no obliga
  a renombrar claves de JSON, columnas de BigQuery ni nombres de módulos.
- **El histórico de BigQuery se acumula por `generated_at`.** Una serie
  renombrada sin migrar parte el archivo en dos y nadie se entera hasta que
  alguien grafica el período completo.
- **Renombrar una sigla de cuatro deja el set a medias**, pero esperar a las
  cuatro deja publicado un cinturón cuyo nombre y cuya sigla no coinciden.
- **La prosa nombra la sigla literal.** Está escrita en unas cien cadenas entre
  fichas, metodología y los textos que `publicar.py` escribe al snapshot; un
  renombre siempre deja alguna suelta, y eso no lo detecta ningún gate.

## Opciones consideradas

1. Renombrar sólo la capa pública: etiqueta del cinturón y sigla del índice.
2. Renombrar también los identificadores técnicos y migrar BigQuery.
3. Renombrar la etiqueta del cinturón y conservar ITVC.
4. Esperar a que la Fundación defina las cuatro siglas juntas.

## Decisión

**Opción 1**, que es la opción 1 de ADR-0190 aplicada a este índice.

- **Público**: `Vida cotidiana` → `Impacto social`; `ITVC` → **`ITCIS`**
  (Índice de Tensión del Cinturón de Impacto Social, que respeta el patrón
  ITC+inicial de ITCM/ITCG/ITCP, patrón que ITVC justamente rompía);
  `Informe de Coyuntura` → `Monitor del Plan de Gobierno`.
- **Técnico, sin cambios**: la clave `vida_cotidiana`, la clave `itvc`, el
  módulo `scripts/itvc.py`, las constantes `DIMENSIONES_ITVC`/`BANDAS_ITVC`, la
  URL `/vida/`, el id de ficha `/metodologia/itvc/` y las tablas de BigQuery
  siguen exactamente igual.

La sigla pública se **declara en dos lugares y nada más**:
`config.SIGLAS_PUBLICAS` para lo que escribe Python al snapshot, y
`web/src/lib/datos.ts::indiceDe` para lo que arma la web. Las otras tres siguen
pendientes de la definición editorial que ADR-0190 espera; cuando lleguen, son
una línea en cada uno de esos dos lugares y el resto es prosa.

### Consecuencias

- Queda una **divergencia declarada** entre lo que dice la página (`ITCIS`,
  Impacto social) y lo que dicen las claves, los ADR y las tablas (`itvc`,
  `vida_cotidiana`). Es el costo aceptado de la opción 1 y ADR-0190 ya lo tenía
  anotado: quien trabaje en el código traduce, quien lee la página no.
- El archivo histórico de BigQuery **sigue siendo una sola serie comparable**.
  Ese era el riesgo caro y no se corrió.
- La colisión ITCG ↔ ICG (UTDT) **sigue abierta**, y es el problema más serio
  de los dos que ADR-0190 nombra. Este ADR no la toca.
- El texto que `publicar.py` escribe al snapshot cambió, así que **no alcanza
  con cambiar el código**: hasta que no corre `publicar.py`, la página sigue
  publicando el nombre viejo en esa prosa.

### Confirmación

`tests/test_siglas_publicas.py` recorre toda la capa de display de la web —
comentarios incluidos, porque un comentario que nombra otra cosa que la página
hace traducir mal al próximo que lo lea — y **el snapshot publicado**, y falla
si aparece cualquiera de los nombres retirados. Que mire el snapshot y no el
código fuente es deliberado: es lo que obliga a correr el pipeline después de
tocar la prosa. Lleva una excepción explícita, "Monitor de la Vida Cotidiana",
que es el nombre propio de un documento de mayo de 2026 y no una etiqueta.

## Pros y contras de las opciones

**1. Sólo la capa pública.** A favor: resuelve lo que ve el lector, que es lo
que se pidió; sin riesgo sobre el histórico; reversible. En contra: deja la
divergencia permanente entre página y claves.

**2. Público y técnico.** A favor: una sola nomenclatura en todos lados. En
contra: toca más de 180 ADR, el snapshot, los tests, `output/` versionado y
BigQuery, con un paso irreversible en el archivo. Es una migración, y no había
razón para pagarla ahora.

**3. Etiqueta sí, sigla no.** A favor: es literalmente lo que volvió del
editor. En contra: publica un índice llamado "Impacto Social" bajo una sigla
que se expande a "Vida Cotidiana". Es el descuido que este ADR corrige.

**4. Esperar a las cuatro.** A favor: un solo cambio, coherente. En contra: la
definición editorial de las otras tres no tiene fecha, y mientras tanto cada
edición publicada fija más las siglas viejas — el propio ADR-0190 dice que el
costo sube con el tiempo.

## Más información

- [[0018-itvc-parametrica-vida-cotidiana]] define la paramétrica del cinturón,
  y su número sigue siendo la referencia: los ids de ADR no se renumeran.
- [[0189-si-no-puntua-no-se-muestra]] dejó asentado que el ITCG es un índice de
  avance y no de coyuntura — la otra mitad del problema de nombres que sigue
  sin resolverse.
