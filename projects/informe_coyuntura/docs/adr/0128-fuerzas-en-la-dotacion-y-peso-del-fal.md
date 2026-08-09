---
madr: 4
id: '0128'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'gestion'
indicadores: [reduccion_estado, reforma_laboral]
relacionado: ['0187']
ambito: 'ITCG · `reduccion_estado` (contexto) · dimensión `reforma_laboral` (pesos)'
origen: 'Aporte externo sobre el cinturón de gestión (doc 260723), puntos 2 y 4'
---

# ADR-0128 — Las fuerzas están en la dotación, y el FAL baja a la mitad de su dimensión

Cierra los dos pendientes del aporte de gestión que no se habían resuelto.

---

## Contexto y planteo del problema

### 1. El denominador de la dotación APN incluye a las fuerzas

> "Habría que confirmar que el denominador de APN a achicar no incluye fuerzas
> armadas y de seguridad."

**Sí las incluye.** El padrón del INDEC tiene siete entidades de fuerzas entre
sus informantes:

- Estado Mayor Conjunto de las Fuerzas Armadas
- Estado Mayor General del Ejército Argentino
- Estado Mayor General de la Armada Argentina
- Estado Mayor General de la Fuerza Aérea
- Gendarmería Nacional Argentina
- Prefectura Naval Argentina
- Policía de Seguridad Aeroportuaria

No estaba escrito en ninguna parte. La pregunta era pertinente y la respuesta
tenía que estar publicada.

## Factores de decisión

### Cuánto cambia la lectura

| | dic-2023 | feb-2026 | variación |
|---|---|---|---|
| **APN completa** (lo que puntúa) | 231.305 | 188.213 | **−18,63%** |
| fuerzas (7 entes) | 22.585 | 19.144 | −15,24% |
| planta civil | 208.720 | 169.069 | **−19,00%** |

Las fuerzas son **~10% de la dotación** y se redujeron menos que el resto, de
modo que incluirlas **subestima el ajuste de la planta civil en 0,37 pp**.

## Opciones consideradas

- **No descontar las fuerzas del denominador de la dotación** — elegida: sacarlas sería una decisión editorial que hay que justificar por separado, no un arreglo técnico. Un gobierno que reduce el Estado y a la vez sostiene sus fuerzas está tomando una decisión, y el indicador debe reflejarla.
- **Descontarlas** — descartada.
- **Publicar el desglose en la card** — se hace, igual que en ADR-0097.

## Decisión

### Decisión

**No se descuentan.** Las fuerzas son parte del Estado y sacarlas del
denominador sería una decisión editorial que hay que justificar por separado,
no un arreglo técnico. Un gobierno que reduce el Estado y a la vez sostiene sus
fuerzas está tomando una decisión, y el indicador debe reflejarla.

Lo que sí cambia: **la card publica el desglose**, igual que ADR-0097 hizo con
las empresas del Estado. La elección de universo queda a la vista y un lector
que discrepe puede hacer la cuenta contraria con los números publicados.

**Limitación:** la hoja de detalle por entidad va uno o dos meses atrás del
cuadro principal, así que el desglose se publica con su propia fecha. Comparar
meses distintos produciría una planta civil inventada.

---

### 2. El FAL pasa a pesar la mitad de su dimensión

> "Cambiar el valor de los indicadores, y tomar un 50% para el FAL y otro 50%
> para Litigiosidad."

| | antes | ahora |
|---|---|---|
| `fal_modernizacion_laboral` | 0,70 | **0,50** |
| `litigiosidad_laboral` | 0,30 | **0,50** |

El argumento es conceptual: la dimensión mide el par **instrumento y
resultado**, y no hay razón para que el instrumento pese 2,3 veces al
resultado. Al contrario — un fondo bien construido que nadie use no es una
reforma laboral, y la litigiosidad es lo único que dice si algo cambió en los
hechos.

### El efecto, dicho como es

**El cambio mejora el puntaje.** La litigiosidad puntúa 59,4 y el FAL 30,8, así
que subirle el peso al primero levanta la dimensión y el índice:

| | antes | ahora |
|---|---|---|
| dimensión reforma laboral | 39,4 | **45,1** |
| ITCG | 71,7 | **72,5** |

No se puede invocar "el efecto es neutro" como defensa, porque no lo es. La
justificación es únicamente el argumento conceptual, y viene de una revisión
externa que lo propuso sin mirar el resultado. Queda escrito acá y en la ficha
para que se pueda discutir en esos términos y no en otros.

**La dimensión sigue siendo la más floja del ITCG** —las otras cuatro van de 58
a 83— y sigue por debajo del umbral de 50 que el test conserva desde ADR-0098.

## Pros y contras de las opciones

### Lo que NO se tomó de la propuesta

El aporte proponía además abrir el FAL en dos medidores de 25% cada uno: la Ley
27.802 y el Decreto 408/2026. **Ya está hecho, y con más detalle**: ADR-0098
descompuso el indicador en tres etapas (construcción 40 / vigencia 20 /
adopción 40) y la construcción se mide sobre tres hitos normativos fechados,
que incluyen los dos que el aporte menciona más el marco financiero de la CNV.
Reemplazarlo por dos hitos sería perder resolución.

---

## Más información

### Limitaciones

- El desglose de fuerzas **no se incorpora a la serie histórica**, sólo a la
  card: la hoja de detalle no cubre todo el período con la misma consistencia
  que el cuadro principal.
- Las siete entidades se identifican **por nombre**. Si el INDEC renombra una,
  el desglose la pierde en silencio y el total publicado no cambiaría — el
  contexto quedaría subestimado sin que nada avise.
- El peso 50/50 es **una convención igual que el 70/30 anterior**. Ninguno de
  los dos sale de un documento de diseño; lo que cambia es que ahora hay un
  argumento escrito a favor del reparto elegido.
