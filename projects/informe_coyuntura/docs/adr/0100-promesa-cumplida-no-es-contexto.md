---
madr: 4
id: '0100'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'gestion'
indicadores: [asistencia_directa, social_orden, cumplido]
continuado_por: ['0186']
ambito: 'ITCG · `asistencia_directa` · dimensión `social_orden` · estado `cumplido`'
origen: 'Auditoría externa del cinturón de gestión (doc 2), punto 3.8'
---

# ADR-0100 — Una promesa cumplida no es un indicador de contexto

| **Acota** | ADR-0051 (las cards de contexto salen del tablero) |

## Contexto y planteo del problema

> "**Indicador saturado**: la propia ficha lo admite, la línea de base 2023
> (Potenciar Trabajo) ya estaba en 98,3% de pago directo. El salto normativo fue
> real, pero el indicador está «pegado» cerca del máximo desde 2024, con muy
> poco recorrido para seguir informando algo nuevo mes a mes. Esto es un problema
> serio de **poder discriminante**: un indicador que no puede moverse deja de ser
> útil para el seguimiento mensual, aunque sea correcto conceptualmente."

## Opciones consideradas

- **Sacar la promesa cumplida del conjunto de indicadores de contexto** — elegida.
- **El segundo camino que proponía la auditoría** — evaluado y no hecho; el motivo está detallado en el cuerpo del ADR.

## Decisión

`asistencia_directa` **sale del cálculo del ITCG y se queda en el tablero**, con
un estado nuevo: **promesa cumplida**.

```python
INDICADORES_CUMPLIDOS = {
    "asistencia_directa": {"desde": "2024-04", "desde_txt": "abril de 2024", ...},
}
```

La dimensión `social_orden` pasa de 40/40/20 a **67/33**: los dos que quedan
conservan su proporción relativa (2:1), de modo que la dimensión no cambia de
carácter, sólo deja de arrastrar un componente sin recorrido.

| | antes | ahora |
|---|---|---|
| social_orden | 90,6 | **84,4** |
| ITCG | 73,1 | **72,5** |

## Más información

### Limitaciones

- **El estado es reversible y nadie lo vigila automáticamente.** Si la
  desintermediación retrocediera, el indicador seguiría fuera del cálculo hasta
  que alguien lo devuelva a mano. La card sigue publicando el valor, así que un
  retroceso sería visible, pero no dispara ninguna alarma.
- **El eje de alcance/calidad queda sin medir.** La caída real del 80% es un
  hecho relevante que el informe hoy no cuenta en ningún lado. Queda como deuda
  explícita, con el dato ya calculado en este ADR para quien retome la
  discusión.
- El umbral para declarar una promesa cumplida **es de criterio**: acá fueron 27
  meses en el valor máximo y una línea de base que ya estaba en 98,3%. No hay
  regla automática, y si el patrón se repite en otros indicadores convendrá
  escribirla.

### Es peor que "cerca del máximo"

La serie está en **exactamente 100,0 desde abril de 2024**: veintisiete meses sin
una sola variación. Antes de eso oscilaba entre 92,9 y 100,9 —ese valor por
encima de 100 sugiere además que el cociente puede pasarse de 1—, pero desde el
salto normativo no volvió a moverse.

Con 4% del ITCG, es peso que el índice destina a información nula.

### Qué se evaluó y por qué no se hizo

La auditoría proponía dos caminos. El segundo —"separar desintermediación
(logrado, indicador cerrado) de alcance/calidad (abierto, con recorrido)"—
llevaba a buscar un eje que sí se moviera.

Existe, y es dramático. El **valor real** del devengado en asistencia directa,
deflactado por IPC contra dic-2023:

| mes | real (base dic-2023) |
|---|---|
| jul-2023 | 209.844 |
| abr-2024 | 45.237 |
| abr-2025 | 37.705 |
| **abr-2026** | **27.320** |

Una caída cercana al 80%, construible con la fuente que ya se usa.

**No se incorporó como indicador puntuable.** Su dirección es contestable: la
misma caída se lee como promesa cumplida ("no hay plata", ajuste fiscal) o como
protección social erosionada, según quién mire. Puntuarla obliga a tomar
partido, y el mismo día ADR-0095 documentó lo que cuesta incorporar un indicador
cuya dirección depende de quién gobierne. No se repite la operación con un
número más cargado políticamente.

### Por qué esto no contradice ADR-0051

ADR-0051 estableció que **lo que no puntúa no se muestra**, y fue una corrección
editorial explícita: el tablero no debía mezclar cards que construyen la tensión
con cards que no. Los indicadores que sacó —alertas de manifestación, protestas
en CABA— **no miden la dimensión de su índice**: son seguimiento lateral.

Una promesa cumplida es otra cosa. `asistencia_directa` **sí mide** lo que
`social_orden` se propone medir, y lo mide tan bien que llegó al techo. Retirarla
del tablero haría que el informe dejara de contar que la desintermediación se
logró — que es, en un tablero de cumplimiento de promesas, exactamente la clase
de noticia que hay que dar.

La excepción es **acotada y verificada por test**: fuera de las cumplidas, sigue
sin poder haber cards sin puntaje, y toda cumplida debe declarar su fecha de
logro y el motivo.

**En el tablero la card se queda dentro de su dimensión**, junto a sus pares, con
una etiqueta que dice "✓ Logrado en abril de 2024 · ya no puntúa". La primera
versión de este ADR la mandaba a un bloque aparte al pie de la página; el editor
lo corrigió con un argumento mejor: el indicador pertenece a esa dimensión y
sacarlo de ahí haría parecer que mide otra cosa. Lo que cambió es que dejó de
puntuar, no dónde va.

El encabezado de la dimensión lo refleja: dice "2 indicadores + 1 logrado", para
que el puntaje no parezca calculado sobre tres.
