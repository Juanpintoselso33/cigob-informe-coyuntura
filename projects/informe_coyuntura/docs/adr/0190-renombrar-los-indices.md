---
madr: 4
id: '0190'
estado: 'propuesto'
fecha: 2026-08-09
cinturon: 'transversal'
relacionado: ['0012', '0013', '0018', '0189']
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

**Pendiente.** Este ADR queda en `propuesto` para dejar registrado el problema
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
