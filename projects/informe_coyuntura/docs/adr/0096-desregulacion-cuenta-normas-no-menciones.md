---
madr: 4
id: '0096'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'gestion'
indicadores: [desregulacion_normativa]
modificado_por: ['0125']
ambito: 'ITCG · `desregulacion_normativa` · serie · caché por norma'
origen: 'Auditoría externa del cinturón de gestión (doc 1), prioridad alta'
---

# ADR-0096 — Desregulación: contar normas derogadas, no menciones de una palabra

## Opciones consideradas

- **Contar normas completas derogadas desde dic-2023**, leyendo sólo la parte dispositiva — elegida.
- **Contar menciones de una norma** — descartada.
- **Sumar las derogaciones parciales** — no: se relevan aparte y no se suman.

## Decisión

El indicador pasa a contar **normas completas derogadas desde dic-2023**, con
tres reglas:

1. **Sólo la parte dispositiva.** Se corta el texto en `RESUELVE:` / `DECRETA:` /
   `DISPONE:` y se ignora todo lo anterior.
2. **Normas completas, no actos.** Leyes, decretos, resoluciones y disposiciones
   que quedan sin efecto. El DNU 70/23 aporta 38.
3. **Las derogaciones parciales se relevan aparte y no se suman.** Hoy son 57.
   Se publican como contexto: hay actividad desregulatoria que el conteo no
   captura, y decirlo es parte de la medición.

| | antes | ahora |
|---|---|---|
| unidad | normas que mencionan "deroga" | normas completas derogadas |
| valor | 61 | **47** |
| puntaje | 86,5 | **72,0** |
| ITCG | 71,9 | **70,9** |

**Las bandas no se tocaron.** Recalibrarlas para que el puntaje quedara donde
estaba habría sido exactamente la circularidad que la misma auditoría advierte
en su punto 3.2. El puntaje baja porque la métrica se corrigió, no porque el
mundo cambiara.

### La forma de la serie

La serie reconstruida dice algo que la anterior no podía decir:

| mes | acumulado |
|---|---|
| dic-2023 | **38** |
| mar-2024 | 42 |
| feb-2025 | 43 |
| may-2025 | 45 |
| sep-2025 | 47 |

**La desregulación, medida en normas completas, fue casi toda un solo acto de
diciembre de 2023.** El resto del mandato aporta 9 normas en más de dos años y
medio.

La auditoría había intuido exactamente esto —"puede dar la impresión de que la
desregulación es un proceso lineal y gradual, cuando en los hechos tuvo un pico
inicial muy grande"— aunque a partir de una premisa equivocada. La intuición era
correcta; el mecanismo, no.

## Más información

### Limitaciones

- **La escala sigue siendo una convención propia**: 100 normas = plan completo.
  No proviene de ninguna meta oficial. Es el punto 3.2 de la auditoría y este
  ADR **no lo resuelve**; sólo lo deja escrito en la ficha pública, que antes no
  lo decía con esa claridad.
- El conteo **no pondera por peso económico**: derogar una ley que regula un
  mercado entero cuenta igual que derogar una resolución administrativa menor.
- **Subestima la desregulación en sentido amplio**, porque las 57 derogaciones
  parciales quedan afuera. Es una elección: mezclarlas produciría un número sin
  unidad interpretable.
- Al concentrarse el grueso en un solo mes, el indicador **se mueve poco mes a
  mes**. Describe bien el fenómeno y por eso mismo aporta poca variación al
  índice — el mismo problema de rango dinámico que la segunda auditoría señala
  para TDPS y el FAL.

### Lo que decía la auditoría

> "El DNU 70/23 —el megadecreto de desregulación de diciembre de 2023,
> probablemente el acto normativo individual más significativo de todo el
> programa desregulador— **queda fuera del conteo porque no está indexado como
> texto completo en InfoLeg**. Esto es un problema serio de validez de
> constructo."

Era su recomendación de prioridad más alta.

### La premisa era falsa, y el error era nuestro

**El DNU 70/2023 sí está indexado y siempre estuvo contado.** La consulta actual
lo devuelve:

```
Decreto DNU 70/2023 · PEN · 21-dic-2023
BASES PARA LA RECONSTRUCCION DE LA ECONOMIA ARGENTINA
```

Lo importante no es que la auditoría se equivocara, sino **de dónde sacó el
dato**: de nuestra propia ficha metodológica, que afirmaba textualmente que "el
megadecreto 70/2023 no está indexado como texto completo en la fuente y no
aparece en el conteo". El auditor leyó la documentación, la creyó —es lo
correcto— y construyó sobre ella su recomendación principal.

Una limitación mal declarada no es un exceso de prudencia: **es información
falsa que se propaga a quien la lee**, y en este caso costó la prioridad más
alta de una auditoría externa.

### Los problemas reales

Al ir a verificar la premisa aparecieron tres, ninguno de los cuales era el
enunciado.

**1. Cerca de la mitad de lo contado no derogaba nada.** La búsqueda de InfoLeg
matchea la palabra "deroga" en cualquier parte del documento, incluidos los
considerandos, donde una norma suele relatar lo que derogó *otra*. De 60 normas
relevadas, **sólo 24 derogan algo en su parte dispositiva**. Entre las contadas
había una resolución de Cancillería sobre un nombramiento episcopal, que
menciona un decreto derogado de la Sagrada Congregación Consistorial.

Es la misma familia de error que ADR-0068 (la consulta "fondo de cese laboral"
contaba el régimen homónimo de la construcción) y que ADR-0091 (`veto_quorum`
contaba como fracaso de quórum las informativas del art. 71 CN). **Tercer caso
de una búsqueda de texto completo sobre una base legal que cuenta lo que no es.**

**2. El DNU 70/23 pesaba uno.** Sí estaba contado, pero como una unidad, igual
que un decreto que elimina un trámite. Deroga **38 normas completas** y modifica
parcialmente otras 30.

**3. Los objetos derogados son incommensurables.** Lo que se deroga va desde una
ley entera hasta "el punto 9) del apartado E) del artículo 20 de la Sección II
del Capítulo I del Título V de las NORMAS". Contar "normas derogadas" sin
distinguir sería tan arbitrario como contar actos.

### Caché

El análisis por norma vive en `data/gestion/desregulacion_normas.json` y es
**permanente**: el texto de una norma publicada es inmutable, así que cada
corrida sólo procesa las nuevas. Sin la caché, cada actualización bajaría 60+
documentos de InfoLeg.

Se agregó al `git add` del workflow nocturno **en el mismo cambio** — un caché
que no se commitea no sobrevive al cron y se reconstruye entero cada noche.
