---
madr: 4
id: '0337'
estado: 'aceptado'
fecha: 2026-09-24
cinturon: 'transversal'
archivos: ['web/src/components/NivelTension.astro', 'web/src/components/Hero.astro', 'web/src/components/Bluf.astro', 'web/src/components/TensionPanel.astro', 'web/src/components/Archivo.astro', 'web/src/components/Evolucion.astro', 'web/src/components/IndicadorModal.astro', 'web/src/components/SemaforoLeyenda.astro', 'web/src/pages/[slug].astro', 'web/src/pages/frontada.astro', 'web/src/pages/metodologia/[id].astro', 'web/src/pages/metodologia/index.astro', 'web/src/lib/datos.ts', 'web/src/lib/fichas.ts', 'scripts/publicar.py']
relacionado: ['0181', '0311', '0333', '0338']
ambito: 'Presentación · cómo se muestra la tensión en toda la web'
origen: 'Revisión de Luis del 23-sep-2026 sobre los apuntes del 15-sep: «se sacó [la escala de 10 del titular], pero hay que sacarlo en todo, nos quedamos con los colores para mostrar la tensión». Juan eligió «número y escala» en toda la web y graficar el índice en la evolución.'
---

# ADR-0337 — La tensión se lee por color, sin número

## Contexto y planteo del problema

ADR-0311 sacó el «/10» del titular porque ese 10 no es un tope natural —es el
rango de la matriz de tensión— y mostrarlo sugiere una escala científica que el
método no promete. Dejó la escala a nivel de cinturón, dimensión e indicador, con
el argumento de que ahí el lector baja a buscar el detalle. El resultado fue una
web con dos registros: un titular sin escala y unas cuarenta cards con «0,9/10»,
«3,7/10», «6,5/10».

La revisión del equipo pide terminar el movimiento: la tensión se comunica con
los colores.

## Factores de decisión

- El argumento de ADR-0311 vale igual abajo que arriba: el 10 no es un tope
  natural en ningún nivel.
- El color no puede ser el único canal (daltonismo, impresión en gris, lector de
  pantalla): la palabra del tramo y la posición del marcador lo acompañan.
- El detalle numérico sigue existiendo donde tiene unidad propia: el puntaje del
  índice y de cada dimensión (0-100, o base 100 en el ITCIS) y el valor de cada
  indicador.

## Opciones consideradas

1. Sacar sólo el «/10» y dejar el número («3,7» con su color).
2. Número sólo en el titular; en el resto, color.
3. Sin número de tensión en ningún lado: color, palabra del tramo y posición.

## Decisión

**Opción 3**, en toda la web.

- `NivelTension` y su gemela del modal muestran la palabra del tramo y la barra,
  sin valor ni rótulos 0/10. Sólo si faltan los cortes (no hay palabra que decir)
  el valor sale como número.
- La síntesis de portada, el panel de riesgo, el archivo, la página alternativa
  (`frontada`), el chip de la ficha y el modal de indicador nombran el tramo en
  vez de citar «X/10».
- El gráfico de evolución deja de graficar la tensión y grafica **el índice** de
  cada cinturón en su escala (0-100, o base 100 en el ITCIS); subir es mejorar en
  los cuatro.
- Los cortes se explican en la escala del puntaje, que sí se publica:
  `coloresEnIndice()` y `indiceDeTension()` los derivan de `semaforo_cortes`
  (verde con 60 o más, amarillo de 40 a 60, naranja de 20 a 40 y rojo por debajo
  de 20; en el ITCIS, 105 / 95 / 85). La leyenda del semáforo, las notas
  metodológicas de cada cinturón y las fichas de índice los dicen así.
- Los textos que arma `publicar.py` (`aporte_lectura`, `por_que` de dimensión)
  nombran el color y su palabra (`_lectura_tension`).

### Consecuencias

- La tensión 0-10 sigue existiendo en el cálculo: el score de cada cinturón, el
  score global, los cortes y el estado no cambian. Cambia sólo cómo se muestran.
- Quedan fuera, a propósito: `output/informe.md` (material de ingesta, no web),
  los avisos de Slack y la fórmula interna del indicador de tarifas, que se
  define en tensión (`2(E−10)`) y la ficha la documenta como fórmula.
- Las fichas de índice escriben los cortes 60/40/20 como texto. Si ADR-0333
  cambiara, hay que actualizarlas junto con `semaforo_cortes`.

### Confirmación

El build pasa y el snapshot se regeneró con los textos nuevos. La suite completa
(`pytest tests`) y `gate_calidad.py` en verde.

## Más información

Extiende [[0311-el-titular-sin-escala-y-los-rotulos-sin-siglas-internas]] a toda
la web. Los cortes son los de [[0181-el-color-es-la-tension-que-ya-se-publica]] y
[[0333-el-color-y-el-estado-leen-la-misma-escala]].
