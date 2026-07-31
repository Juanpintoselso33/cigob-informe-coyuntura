---
madr: 4
id: '0124'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'macro'
indicadores: [emae_difusion, actividad]
ambito: 'ITCM · `emae_difusion` (nuevo) · dimensión `actividad` · banda · serie'
origen: 'Propuesta del editor, a partir de un informe externo sobre la composición del crecimiento'
---

# ADR-0124 — La actividad se mide también en amplitud: entra la difusión sectorial del EMAE

## Contexto y planteo del problema

El editor pidió un indicador que contara **cuántos sectores están creciendo**,
no sólo cuánto crece el agregado. El disparador fue un informe externo que
describía un crecimiento traccionado por energía y minería mientras el empleo y
la industria se deterioraban — una distinción que el EMAE agregado no puede
expresar, porque devuelve un solo número.

## Opciones consideradas

- **Entra `emae_difusion`** con peso 0,20, que **sale entero del EMAE agregado** — elegida.
- **Sacarle peso al IPI** — descartada: la composición por fuente de la dimensión no se mueve.

## Decisión

Entra `emae_difusion`: **porcentaje de los 15 sectores del EMAE que crecen
interanualmente**.

La dimensión `actividad` pasa de dos indicadores a tres:

| | antes | ahora |
|---|---|---|
| `emae_ia` | 0,80 | **0,60** |
| `emae_difusion` | — | **0,20** |
| `ipi_manufacturero` | 0,20 | 0,20 |

**El 0,20 sale entero del EMAE agregado, no del IPI.** La composición por
FUENTE de la dimensión no se mueve: el EMAE sigue aportando el 80% y el IPI el
20%. Lo que cambia es que ese 80% pasa a leerse en dos registros —cuánto crece
la actividad y en cuántos sectores crece—. El IPI no se toca porque sigue
siendo el único respaldo de fuente distinta, y su 20% ya está justificado en
ADR-0079 por exposición a manufactura.

### Los quince sectores

Se usan los 15 sectores de actividad del dataset de apertura sectorial. La
16ª serie del dataset, **"Subsidios netos", se excluye a propósito**: es un
componente de la agregación (impuestos netos de subsidios), no una actividad
económica, y contarla habría metido una partida contable entre los sectores.

Se publican el mismo día que el nivel general, así que **el indicador no agrega
rezago** sobre el que la dimensión ya tiene.

## Más información

### Limitaciones

- **Todos los sectores pesan igual.** Un mes en que crece la pesca cuenta lo
  mismo que uno en que crece la industria manufacturera, que es varias veces
  mayor. Ponderar por participación daría otra lectura y exigiría una fuente
  adicional de estructura sectorial; queda anotado.
- **Sólo mira el signo, no la magnitud.** Un sector que crece 0,1% y otro que
  crece 15% cuentan igual. Eso es lo que hace al indicador robusto —no lo mueve
  un valor extremo— y a la vez lo que le impide distinguir crecimiento débil de
  fuerte. Esa parte la mide el EMAE agregado, y por eso los dos conviven.
- **Los quince sectores son categorías amplias**: "industria manufacturera" es
  una sola de ellas y agrupa actividades muy distintas entre sí.
- **Hereda las revisiones del EMAE.** El INDEC revisa las series sectoriales
  hacia atrás, de modo que una revisión puede cambiar retroactivamente el
  conteo de un mes ya publicado. La serie se regenera entera en cada corrida.
- El indicador **no dice nada sobre empleo**, aunque el planteo que lo originó
  venía de ahí. Que los sectores que caen sean intensivos en mano de obra es
  una lectura del analista sobre el detalle publicado, no algo que el número
  mida por sí solo.

### Por qué el agregado no alcanza

Mayo de 2026 es el caso que justifica el indicador:

| EMAE agregado | difusión |
|---|---|
| **+0,2% i.a.** | **8 de 15 sectores** |

| ▲ crecen | | ▼ caen | |
|---|---|---|---|
| Explotación de minas y canteras | **+15,7%** | Pesca | −29,3% |
| Electricidad, gas y agua | +8,0% | **Industria manufacturera** | **−5,6%** |
| Agricultura y ganadería | +4,6% | **Comercio** | **−4,3%** |
| Construcción | +1,9% | Hoteles y restaurantes | −1,8% |
| Intermediación financiera | +1,5% | Administración pública | −1,4% |
| Servicios sociales (salud) | +0,9% | Servicios comunitarios | −1,3% |
| Transporte y comunicaciones | +0,6% | Enseñanza | −0,1% |
| Inmobiliarias y alquiler | +0,4% | | |

El agregado dice "no pasó nada". La apertura dice que el crecimiento se
concentró en dos sectores de alta productividad y bajo empleo, mientras los dos
que más ocupan gente se contrajeron. **Son dos hechos distintos y sólo uno
llegaba al índice.**

No es un mes aislado: desde 2023 hay trece meses con el EMAE dentro de ±1,5 pp
—donde el agregado no informa nada— y la difusión en ellos va de 46,7% a 80%.

### Las anclas, y por qué no se ancló en 50

La tentación era anclar en 50% —la línea clásica de los índices de difusión
tipo ISM—. **Con los datos argentinos habría estado mal.** Sobre 257 meses
(2005-2026) la mediana es **73,3%**: en un mes normal crecen 11 de 15 sectores.
Un corte en 50 habría dado puntaje alto a la mitad inferior de la distribución.

Los cortes se ponen por **cantidad de sectores**, no en porcentajes redondos:
con 15 sectores el indicador sólo puede tomar 16 valores (múltiplos de 6,67),
así que cada límite va en el hueco entre dos valores alcanzables.

| sectores | difusión | puntaje | lectura |
|---|---|---|---|
| 14-15 | > 90 | 100 | crecimiento generalizado |
| 11-13 | 70 – 90 | 80 | mayoría amplia |
| 8-10 | 50 – 70 | 60 | mayoría ajustada |
| 5-7 | 30 – 50 | 35 | minoría creciendo |
| 0-4 | ≤ 30 | 10 | contracción generalizada |

Reparto sobre datos reales — **las cinco bandas pobladas**, criterio de
ADR-0042 (nace discriminando, no hay que recalibrarlo después):

| muestra | 0-4 | 5-7 | 8-10 | 11-13 | 14-15 |
|---|---|---|---|---|---|
| historia completa (n=257) | 6% | 16% | 23% | 33% | 21% |
| pre-mandato (n=227) | 7% | 14% | 22% | 34% | 23% |
| mandato actual (n=30) | 0% | 33% | 33% | 30% | 3% |

Los cortes son conceptuales —cada banda es una lectura entera del estado de la
economía— y además reparten razonablemente fuera del período que miden, que es
lo que ADR-0120 exige para no calibrar contra el propio mandato.

### Redundancia, declarada

`emae_difusion` correlaciona **0,84 con el EMAE agregado en niveles** y 0,55 en
diferencias, sobre 257 meses. Es alto, y conviene decirlo antes de que lo
encuentre una auditoría.

La vara pertinente: el par **EMAE ↔ IPI que ya conviven en esta dimensión
correlaciona 0,857**, o sea más. La difusión no es más redundante que el
respaldo que ADR-0076/0079 ya aceptaron a propósito. Y su correlación baja a
0,55 en diferencias, que es donde vive la señal mes a mes.

Por gobierno, la correlación en niveles es estable (Macri 0,84 · Fernández 0,87
· Milei 0,81): el indicador no cambia de comportamiento según quién gobierne,
a diferencia de `brecha_obra_publica` (ADR-0095).

### Impacto

| | antes | ahora |
|---|---|---|
| dimensión actividad | 56,8 | **54,9** |
| ITCM | 62,1 | **61,9** |
| tensión | 3,8 | 3,8 |

El movimiento es chico porque la dimensión pesa 11% del índice. **Las bandas de
los otros indicadores no se tocaron.**

### La serie

Se reconstruye con la misma fórmula que puntúa, desde 2005 (los sectores
publican desde 2004 y el interanual necesita doce meses). El backfill del
mandato está completo: **30 puntos mensuales desde dic-2023**, sin huecos.
