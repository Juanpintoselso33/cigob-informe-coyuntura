---
madr: 4
id: '0093'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'politica'
indicadores: [alianzas_territoriales, alineamiento_senadores_prov, iaf_transferencias]
ambito: 'ITCP · dimensión `alianzas_territoriales` · textos públicos de `alineamiento_senadores_prov` e `iaf_transferencias`'
origen: 'Auditoría externa del cinturón político, prioridad 7'
---

# ADR-0093 — La dimensión federal declara lo que no mide

## Contexto y planteo del problema

> "Ajustar el nombre o la descripción pública de 'Alineamiento de senadores por
> provincia' para que no se lea como una medición directa de gobernadores, algo
> que **la propia ficha ya aclara puertas adentro** pero que conviene explicitar
> también en la presentación del cinturón."

La auditoría fue justa al señalar dónde estaba el problema y dónde no. La ficha
metodológica ya decía exactamente lo que había que decir:

> "**Caveat importante**: este indicador mide comportamiento de voto de
> SENADORES, no la postura pública del gobernador de la provincia — un senador
> no depende del gobernador de turno, puede responder a la estrategia nacional
> de su propio partido."

El hueco era de **alcance**: la ficha lo declaraba y la presentación del
cinturón —la descripción que se ve en el modal, sin entrar a la metodología— no.

### Lo que se encontró al revisarlo

El problema aparecía en tres textos, no en uno.

**1. El indicador se vendía como virtud lo que es una limitación.** Decía:

> "Mide alianzas territoriales por el comportamiento real de voto en el Senado,
> no por declaraciones o el alineamiento partidario formal de cada gobernador."

El contraste con "declaraciones" sugiere que el voto del senador es la medida
*superior* de la alianza territorial, cuando en rigor es una **sustituta
declarada**: mide otro actor.

**2. `iaf_transferencias` tenía el mismo defecto y la auditoría lo marcó
aparte** (punto 109: "mide el gesto fiscal de la Nación hacia las provincias, no
la conducta o disposición de los gobernadores"). El texto decía:

> "Mide la armonía —o el conflicto— fiscal con los gobernadores."

Un giro de transferencias es una decisión del **Gobierno nacional**. Describe lo
que la Nación hace, no cómo responden las provincias.

**3. La descripción de la dimensión** enumeraba sus tres componentes sin decir
lo que tienen en común: **ninguno observa directamente al ejecutivo
provincial.**

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Se reescriben los tres textos. La dimensión conserva su nombre —"Alianzas
territoriales"— y agrega la precisión que faltaba:

> Ninguna de las tres observa directamente la conducta de los gobernadores. La
> primera describe lo que hace el Gobierno nacional; la segunda, cómo votan los
> senadores de cada provincia; la tercera, una decisión legislativa provincial
> ya tomada. No se encontró una fuente pública que midiera de forma
> automatizable la postura de los ejecutivos provinciales, así que la dimensión
> se lee como respaldo territorial observado por sus efectos, no como una
> medición de la relación con cada gobernador.

**No se renombra la dimensión.** "Alianzas territoriales" describe bien lo que
se busca medir; el problema no era el nombre sino la ausencia de la salvedad.
Renombrarla obligaría a tocar fichas y tests sin ganar precisión.

**No se cambian el cálculo, las bandas ni los pesos.** Este ADR es enteramente
de texto público.

## Más información

### Por qué importa más de lo que parece

Es la observación más barata de toda la auditoría y la que mejor ilustra un modo
de falla propio de un proyecto con buena documentación: **la salvedad existía,
estaba bien escrita, y vivía en el lugar donde menos gente la lee.** Un lector
que abre la card y no entra a la ficha se llevaba la impresión de que el índice
mide la relación con los gobernadores. La documentación exhaustiva no sustituye
a que el texto de primera lectura sea exacto.

### Limitación que queda declarada, no resuelta

Sigue sin haber fuente automatizable de la postura de los ejecutivos
provinciales — dos rondas de búsqueda documentadas en la ficha del indicador. La
dimensión mide respaldo territorial por sus efectos observables. Si aparece una
fuente directa, este ADR queda superado.
