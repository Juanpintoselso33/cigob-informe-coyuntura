---
madr: 4
id: '0098'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'gestion'
indicadores: [fal_modernizacion_laboral]
archivos: ['fal_hitos.json']
modifica: ['0068']
ambito: 'ITCG · `fal_modernizacion_laboral` · banda · serie · `fal_hitos.json`'
origen: 'Auditoría externa del cinturón de gestión (doc 2), prioridad alta'
---

# ADR-0098 — El FAL se mide en tres etapas: construcción, vigencia y adopción

| **Modifica** | ADR-0068 (régimen del FAL, Ley 27.802) |

## Contexto y planteo del problema

> "FAL estructuralmente cerca de cero hasta noviembre de 2026 **por diseño
> legal, no por falta de gestión**. Está honestamente declarado en la ficha,
> pero convendría que el texto del informe mensual lo incluya siempre, porque el
> lector generalmente no baja al detalle metodológico."

La auditoría proponía como mínimo una nota mensual y, como alternativa, excluir
el indicador del ITCG hasta la fecha de vigencia.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

El índice pasa a componerse de tres etapas:

```
0,40 · construcción normativa + 0,20 · vigencia + 0,40 · adopción
```

**Construcción** es la proporción de hitos normativos cumplidos. Cada uno está
fechado y respaldado por una norma publicada, verificable por número en InfoLeg
— el mismo patrón que `concesiones_fechas.json` y `privatizaciones_fechas.json`:

| hito | norma | fecha |
|---|---|---|
| marco financiero para los fondos | Resolución General 1071/2025 (CNV) | 23-jun-2025 |
| ley sancionada y publicada | Ley 27.802 | 06-mar-2026 |
| reglamentación del Fondo | Decreto 408/2026 | 01-jun-2026 |

**Vigencia** vale 100 desde el 1-nov-2026 (Decreto 408/2026, art. 27, que
prorrogó el arranque previsto para junio) y 0 antes.

**Adopción** es el compuesto que antes era todo el indicador: menciones en el
Boletín Oficial más fondos registrados en la CNV.

| | antes | ahora |
|---|---|---|
| valor | 0,4 | **40,2** |
| puntaje | 10 (piso) | **30,8** |
| ITCG | 70,9 | **73,1** |

El **techo antes de la vigencia es 60**: instrumento terminado y en espera.

### Las bandas se recalibraron, y por qué eso no es circularidad

Las anclas anteriores (40-60 = "adopción masiva") describían una escala de
sólo-adopción. Aplicadas sin cambios a la escala nueva habrían dado **75 puntos
a un instrumento que nadie usa todavía**. La recalibración responde a que
cambió lo que la escala mide, no a mover el resultado — la distinción que
ADR-0045 exige y que ADR-0096, el mismo día, resolvió al revés: allí la métrica
cambió y las bandas **no** se tocaron, porque la unidad seguía siendo comparable.

Los cortes se fijan sobre los estados que la escala puede tomar, no sobre el
rango observado:

| estado | valor | puntaje |
|---|---|---|
| nada hecho | 0 | 10 |
| **instrumento construido, sin vigencia** ← hoy | 40 | **30** |
| régimen vigente, adopción nula | 60 | 65 |
| vigente y con adopción real | 80 | 90 |
| adopción plena | 100 | 100 |

Es exigente a propósito. Y tiene una propiedad útil: **el 1-nov-2026 el
indicador sube solo de 30 a 65** sin que nadie toque nada, porque la entrada en
vigencia es un hecho fechado.

### La serie

Se reconstruye en la misma escala, de modo que cada escalón coincide con la
publicación de una norma:

| mes | valor | qué pasó |
|---|---|---|
| dic-2023 → may-2025 | 0,0 | no había instrumento |
| jun-2025 | 13,3 | marco financiero de la CNV |
| mar-2026 | 26,7 | Ley 27.802 |
| jun-2026 | **40,2** | Decreto 408/2026 |

Mezclar la serie vieja (sólo adopción, ~0 en todo su recorrido) con la card
nueva habría dejado dos escalas distintas en el mismo gráfico.

## Más información

### Limitaciones

- **Dar crédito por construir el instrumento es discutible**: un gobierno podría
  sancionar y reglamentar una ley que después nadie use. Por eso construcción y
  adopción pesan lo mismo (40 y 40), y por eso la dimensión mide además el
  resultado con un indicador aparte.
- Los hitos son tres y cada uno vale 13,3 puntos: **el indicador es grueso** en
  su etapa de construcción. No hay forma de hacerlo más fino sin inventar hitos
  intermedios que no tengan norma que los respalde.
- El pleno de 420 menciones del Boletín Oficial sigue siendo una **calibración
  provisoria** anclada al ritmo de homologaciones del Ministerio de Trabajo.

### El problema era más grande que la nota

El indicador valía **0,4 sobre 100**, y sus dos componentes estaban en cero por
la misma razón:

| componente | valor | por qué |
|---|---|---|
| cobertura en convenios | 0,7% (3 menciones de 420) | la ley es de mar-2026 |
| adopción financiera | 0,0% (0 fondos en CNV) | el régimen no rige hasta nov-2026 |

Sacar el componente financiero —lo que sugería la auditoría— habría llevado el
indicador de 0,4 a 0,7: nada.

El diagnóstico de fondo: **el indicador medía la adopción de un instrumento que
legalmente todavía no puede adoptarse.** No medía gestión, medía el calendario.
Y en el tablero, un 0,4 sobre 100 se lee como fracaso absoluto justo cuando el
Gobierno hizo todo lo que estaba a su alcance.

### Consecuencia que conviene mirar

**La dimensión de reforma laboral deja de estar marcada como crítica**: pasa de
24,8 a 39,4 y el umbral de ADR-0020 es 30. No cambió la realidad, cambió la
medición.

Sigue siendo **la dimensión más floja del ITCG por amplio margen** —las otras
cuatro van de 58 a 83— y así queda asentado en el test, que ahora verifica que
esté por debajo de 50. El umbral no se movió para conservar la marca.

### Por qué no se excluyó del índice

Era la otra alternativa que ofrecía la auditoría. Se descartó porque habría
dejado la dimensión de reforma laboral apoyada sólo en la litigiosidad, y con
eso se pierde el par **instrumento/resultado** que la propia auditoría destaca
como buena práctica del diseño: el FAL es el medio, la litigiosidad es el fin.
Medir la construcción del medio es preferible a no medirlo.
