---
madr: 4
id: '0190'
estado: 'aceptado'
fecha: 2026-08-09
cinturon: 'transversal'
archivos: ['scripts/publicar.py', 'scripts/panel_validacion.py', 'tests/test_siglas_publicas.py']
relacionado: ['0012', '0013', '0018', '0189', '0237']
superado_parcialmente_por: ['0212']
ambito: 'Nombres y siglas de los cuatro índices paramétricos'
origen: 'Editor, 2026-08-09: "quedan pendiente renombrar los índices, quedaron con nombres poco indicativos de lo que son, además muy parecidos a los de la Di Tella."'
---

# ADR-0190 — Renombrar los índices: las siglas no dicen qué miden y chocan con las de la UTDT

## Contexto y planteo del problema

Los cuatro índices paramétricos se llaman **ITCM**, **ITCP**, **ITCG** e
**ITVC**: Índice de Tensión del Cinturón de Macroeconomía, de Política, de
Gestión y de Vida Cotidiana. Las siglas se acuñaron con la primera
paramétrica y nunca se revisaron.

Hay dos problemas distintos, y el segundo es peor que el primero.

**No dicen qué miden.** Las cuatro comparten prefijo y se diferencian en la
última letra, así que hay que saber de antemano cuál es cuál; ninguna sugiere
su contenido. Y "tensión" tampoco describe a todas por igual: el ITCG mide
avance de las propuestas de gobierno —cuánto se cumplió—, que no es tensión en
el mismo sentido que el ITCM.

**Se confunden con los índices de la UTDT, que el informe usa adentro.** No es
un parecido lejano: el propio informe publica tres indicadores de la
Universidad Torcuato Di Tella —el Índice de Confianza del Consumidor (ICC), el
de Victimización (LICIP) y el nowcast de pobreza— y hasta hace poco también el
Índice de Confianza en el Gobierno (**ICG**). *ICG* e *ITCG* difieren en una
letra, son ambos índices, y conviven en la misma página. Un lector que
encuentra los dos no tiene cómo saber que uno es propio y el otro es de un
tercero.

El costo de no resolverlo crece: cada informe, cada ficha y cada documento que
sale a CIGOB fija más las siglas actuales.

## Factores de decisión

- **Los identificadores técnicos no son los nombres públicos.** Renombrar de
  cara al lector no obliga a renombrar claves de JSON, columnas de BigQuery ni
  nombres de módulos, y conviene no mezclar las dos cosas.
- **El costo del renombre técnico sí es alto.** `itcm`/`itcg`/`itcp`/`itvc`
  aparecen como claves del snapshot, nombres de módulo, prefijos de tests,
  campos de `output/` versionado y tablas en BigQuery, además de citarse en
  más de 180 ADR. Un renombre completo es una migración, no una edición.
- **Lo que se rompe en silencio es lo caro.** El histórico de BigQuery se
  acumula por `generated_at`: si cambia el nombre de una serie sin migrar lo
  anterior, la serie vieja y la nueva quedan como dos cosas distintas y nadie
  se entera hasta que alguien grafica el período completo.
- **La distinción propio / de terceros es lo urgente.** Que un índice no diga
  en su sigla qué mide es incómodo; que se confunda con uno ajeno es un
  problema de atribución.

## Opciones consideradas

1. Renombrar solo lo público (títulos, fichas, web), dejando intactas las
   claves técnicas.
2. Renombrar público y técnico a la vez, con migración de BigQuery y del
   histórico.
3. Conservar las siglas y agregar un subtítulo descriptivo en cada aparición.
4. No hacer nada.

## Decisión

**Cerrado el 2026-08-20.** Los dos problemas se resuelven, y ninguno por la vía
que este ADR había imaginado.

**El de atribución —el más serio— se resuelve nombrando al dueño, no
renombrando lo propio.** El riesgo real nunca fue la sigla en sí: era que un
lector encontrara `ICG` e `ITCG` juntos y no supiera cuál es nuestro. Se
audita dónde aparece el ajeno y se corrige ahí:

- el texto del contraste del ITCG decía *"la confianza en el gobierno (ICG UTDT)
  diverge del ITCG"*, poniendo las dos siglas a una letra en la misma oración.
  Ahora escribe el ajeno entero —*"el Índice de Confianza en el Gobierno de la
  Universidad Torcuato Di Tella —un índice ajeno, no nuestro—"*— y deja el
  propio como la única sigla de la frase;
- la etiqueta del panel pasa de `Confianza en el Gobierno (ICG)` a
  `Confianza en el Gobierno (ICG de la UTDT)`: el dueño va pegado a la sigla y
  no sólo en la columna de al lado, que es lo que este ADR pedía en su tercer
  punto pendiente.

`tests/test_siglas_publicas.py` lo vuelve estructural: falla si el snapshot
publica una sigla de tercero —`ICG`, `LICIP`— sin su dueño en el mismo texto.

**El de "no dicen qué miden" lo resuelve la portada, no la sigla.** Desde
[[0213-la-portada-dice-que-mide-cada-cinturon]] el lector tiene en pantalla qué
mide cada uno de los cuatro antes de ver un número. Una sigla de cuatro letras
nunca iba a poder decir "capacidad de validar las normas que el proyecto
necesita"; una frase sí, y ya está publicada.

**Por lo tanto ITCM, ITCP e ITCG se conservan.** No queda nada por definir. El
único renombre que se hizo es el del cuarto, y no fue por este ADR: fue porque
el cinturón cambió de nombre y su sigla tenía que seguirlo
([[0212-el-monitor-del-plan-de-gobierno-y-el-cinturon-de-impacto-social]]).

### Lo que se descartó, y por qué

Renombrar los tres restantes costaba una migración —o una divergencia
permanente entre página, claves, ADR y BigQuery— para comprar legibilidad que
la portada ya entrega gratis. Y el `ITCG` sigue siendo, literalmente, el Índice
de Tensión del Cinturón de Gestión: el nombre es correcto, lo que fallaba era
que el ajeno se publicaba sin dueño.

---

**Registro del estado anterior (parcial, 2026-08-20).**
[[0212-el-monitor-del-plan-de-gobierno-y-el-cinturon-de-impacto-social]] tomó la
**opción 1** —renombrar sólo lo público— para **uno** de los cuatro: el cinturón
de vida cotidiana pasó a llamarse *Impacto social* y su índice, de `ITVC` a
`ITCIS`, con las claves técnicas, la URL y BigQuery intactos. Llegó junto con la
primera de las tres definiciones que este ADR esperaba: la Fundación nombró ese
cinturón.

Sigue pendiente lo demás, y en particular **lo más caro de los dos problemas que
este ADR nombra: la colisión de ITCG con el ICG de la UTDT**, que el propio
informe publica. Renombrar uno de cuatro no la toca. ITCM, ITCG e ITCP esperan.

El texto que sigue es el planteo original y vale tal cual para esos tres.

---

**Pendiente (redacción original, 2026-08-09).** Este ADR queda en `propuesto`
para dejar registrado el problema
y que no se pierda; la decisión requiere definir antes tres cosas:

1. **Los nombres nuevos**, que es una decisión editorial de CIGOB, no técnica.
   En particular hay que resolver si el de gestión sigue llamándose "tensión"
   cuando mide avance.
2. **Si el renombre alcanza a los identificadores técnicos** o se queda en la
   capa visible. La opción 1 se puede hacer en una tarde; la 2 es una
   migración con un paso irreversible en BigQuery.
3. **Cómo se marca lo propio frente a lo de terceros** en la página, más allá
   de la sigla — hoy la fuente aparece en la ficha, pero no en la tarjeta.

Mientras tanto, no se acuñan siglas nuevas con el mismo patrón.

### Consecuencias

- Cada documento que salga hasta que esto se resuelva sigue fijando las siglas
  actuales, así que el costo de cambiarlas sube con el tiempo. Es una razón
  para tratarlo pronto, no para apurar una decisión mal tomada.
- Si se elige la opción 2, hay que planificar la migración del histórico de
  BigQuery **antes** de tocar cualquier nombre.

## Pros y contras de las opciones

**1. Solo lo público.** A favor: resuelve lo que ve el lector, que es el
problema reportado; sin riesgo sobre los datos ni sobre el histórico;
reversible. En contra: deja una divergencia permanente entre lo que dice la
página y lo que dicen las claves, los ADR y las tablas — quien trabaje en el
código tiene que traducir mentalmente.

**2. Público y técnico.** A favor: una sola nomenclatura en todos lados. En
contra: toca >180 ADR, el snapshot, los tests, `output/` versionado y BigQuery;
el paso de BigQuery es el riesgoso, porque una serie renombrada sin migrar
parte el histórico en dos sin que falle nada.

**3. Subtítulo descriptivo.** A favor: costo casi nulo, se puede hacer ya. En
contra: no resuelve la colisión con la UTDT, que es el problema más serio de
los dos; agrega texto a una página que ya tiene demasiado.

**4. No hacer nada.** A favor: cero trabajo. En contra: el problema de
atribución queda, y empeora cada vez que se publica.

## Más información

- Los tres indicadores de la UTDT que hoy conviven con nuestras siglas:
  `icc_utdt` (Índice de Confianza del Consumidor), `inseguridad` (LICIP) y
  `pobreza_nowcast`, todos en vida cotidiana.
- [ADR-0189](0189-si-no-puntua-no-se-muestra.md) — deja asentado que el ITCG
  es un índice de AVANCE y no de coyuntura, que es justamente lo que su nombre
  actual no transmite.
