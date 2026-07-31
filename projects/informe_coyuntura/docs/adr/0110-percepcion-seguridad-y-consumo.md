---
madr: 4
id: '0110'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
indicadores: [confianza]
continuado_por: ['0115']
ambito: 'ITVC · dimensión `confianza` · rótulo público'
origen: 'Auditoría de Vida Cotidiana, punto 3.4 y recomendación 3 (prioridad alta)'
---

# ADR-0110 — La dimensión se llama por lo que tiene adentro

| **Apoyado en** | ADR-0108 (matriz de redundancia del ITVC) |

## Contexto y planteo del problema

La auditoría observó que la dimensión agrupaba cinco indicadores de naturaleza
distinta bajo una etiqueta que no describe a dos de ellos:

> "Patentamiento de motos y consumo de carne per cápita […] no miden ni
> confianza ni seguridad sino poder de compra y consumo popular. Las propias
> fichas de estos dos últimos los describen como «proxy de consumo durable» y
> «proxy histórico del bienestar alimentario y del poder de compra popular»,
> respectivamente — más cerca, conceptualmente, de Sostenibilidad de ingresos."

No es una objeción menor de nomenclatura: **el 15% del peso interno de la
dimensión** (carne 10 + motos 5) mide algo distinto de lo que el rótulo anuncia.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

La dimensión pasa a llamarse **"Percepción, seguridad y consumo"**. El nombre
enumera lo que hay adentro: percepción encuestada (ICC) y revelada por conducta
de búsqueda (sentimiento digital), seguridad (victimización), y consumo
(carne, motos).

Nada más cambia: mismos componentes, mismos pesos internos, mismo peso nominal
del 15%. **El ITVC queda en 95,4**, idéntico.

### Consecuencias

- El rótulo vive en un solo lugar (`itvc.DIMENSIONES_ITVC`) y la web lo lee del
  dato, así que el cambio no se puede desincronizar entre el cálculo y la
  presentación.
- Un rótulo honesto no reemplaza a la reorganización: la dimensión sigue
  mezclando tres conceptos. Lo que cambia es que ahora lo dice.

## Más información

### La evidencia

ADR-0108 lo confirmó desde el dato, no desde el concepto. `patentamiento_motos`
correlaciona:

| con | r (niveles) |
|---|---|
| `mora_familias` | **−0,974** |
| `endeudamiento_familiar` | +0,773 |
| `brecha_salario_cbt` | +0,770 |
| `icc_utdt` | +0,442 |

Acopla con el bloque de poder adquisitivo, no con el de percepción. La objeción
conceptual de la auditoría tiene respaldo empírico.

### Por qué no la reorganización

La auditoría planteaba dos caminos y este ADR toma el primero. El segundo
—partir en "Confianza y percepción" + "Seguridad" y mudar carne y motos a
Sostenibilidad de ingresos— es **conceptualmente más prolijo y la evidencia de
arriba lo respalda mejor que al rename**. No se toma ahora por lo que la propia
auditoría advierte:

> "La opción (b) es más prolija pero exige rehacer los pesos nominales y no
> debería tomarse sin una decisión explícita del equipo, dado que toca la
> arquitectura de cinco dimensiones que ya está consolidada en el informe."

Medido: el peso efectivo que se mudaría es **2,25%** (motos 0,75 + carne 1,50), y
la dimensión de origen quedaría con ICC 52,9% · victimización 35,3% ·
sentimiento 11,8% tras renormalizar. Es poco peso y mucha arquitectura: cambia
el número de dimensiones del cinturón, sus pesos nominales y la lectura de la
dimensión crítica, a semanas del lanzamiento.

**Queda abierta como decisión editorial**, con el costo ya medido para que se
pueda tomar sin rehacer este análisis.
