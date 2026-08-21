---
madr: 4
id: '0119'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
indicadores: [consumo_carne]
relacionado: ['0215', '0216', '0217']
cerrado_por: ['0218']
ambito: 'ITVC · fichas públicas de `consumo_carne` y de los indicadores invertidos'
origen: 'Auditoría de Vida Cotidiana, recomendaciones de baja prioridad'
---

# ADR-0119 — Los tres pendientes de baja prioridad del cinturón de vida

| **Cierra** | las 11 recomendaciones de la auditoría |

## Contexto y planteo del problema

La auditoría del cinturón de vida cotidiana dejó tres recomendaciones de baja
prioridad sin resolver: el consumo de carne como medida de bienestar
alimentario, la notación de las fórmulas invertidas y los identificadores
legado. Este ADR las trata una por una y con eso cierra las 11 recomendaciones.

## Opciones consideradas

- **Consumo de carne**: la limitación es real y ahora tiene número, pero **el indicador no se cambia**, por un dato que la auditoría no tenía.
- **Notación de las fórmulas invertidas**: se corrige.
- **Identificadores legado**: no se renombran, y está bien.

## Decisión

### 1. Consumo de carne: la limitación es real y ahora tiene número

La auditoría dudaba de que la carne vacuna —consumo aparente— siguiera midiendo
bienestar alimentario sin captar la sustitución hacia pollo y cerdo. Se
construyó el consumo aparente de las tres carnes desde la faena en toneladas del
INDEC. La sospecha se confirma:

| carne | dic-2023 → hoy |
|---|---|
| vacuna | **−10,2%** |
| cerdo | **+11,5%** |
| pollo | −0,9% |
| **total tres carnes** | **−3,3%** |

La sustitución existe y es grande: la vacuna sola exagera el deterioro
alimentario en unos 7 puntos.

**Pero el indicador no se cambia**, por un dato que la auditoría no tenía: como
serie de tendencia, la carne vacuna sigue al total de las tres carnes casi
perfecto —r=0,970 en niveles, **0,987 en los cambios mes a mes**—. Se mueve igual
que el conjunto; lo que distorsiona es el nivel, no la dirección. Pesa 1,5% y
acompaña, así que el costo de esa distorsión es acotado.

Se declara en la ficha con los números, que es lo que la auditoría pedía: la
card ya decía "la sustitución no se captura" en abstracto; ahora dice cuánto.

### 2. Notación de las fórmulas invertidas

Cinco componentes son "al revés" (más mora, más informalidad, más subocupación,
más victimización, más búsquedas de urgencia = peor). Su LaTeX pone la base de
2023 **arriba** y el valor de hoy **abajo**, al contrario de todos los demás, y
nada lo explicaba — que es exactamente la ambigüedad que la auditoría marcó para
"un lector externo".

Las cinco leyendas ganan la misma frase: la fracción se invierte a propósito
para que, igual que en el resto, **por encima de 100 signifique mejora** —si hoy
hay menos que en 2023, el cociente supera 100—. `mora_familias`, que además no
declaraba estar invertida en su leyenda, ahora lo hace.

### 3. Identificadores legado: no se renombran, y está bien

`despacho_cemento` es en realidad el ISAC de construcción y `mortalidad_pymes`
el IPI industrial. La auditoría pedía sanearlos **"en una futura migración de
esquema"**, y con razón: la clave técnica está enterrada, no la ve el lector.

Se verificó que **los rótulos públicos ya son correctos**: la card muestra
"Construcción (ISAC)" y "Actividad industrial (IPI)", y ambas fichas declaran en
sus limitaciones que el nombre interno promete otra cosa. Renombrar la clave
tocaría las series, los CSV históricos, el snapshot y los mapeos, con riesgo
real y cero ganancia para quien lee. Se deja, que es la decisión que la propia
auditoría condicionaba a una migración mayor.

### Estado de la auditoría

Con esto, las **11 recomendaciones** quedan resueltas o declaradas: 4 de alta
prioridad, 4 de media, 3 de baja. Ninguna abierta.
