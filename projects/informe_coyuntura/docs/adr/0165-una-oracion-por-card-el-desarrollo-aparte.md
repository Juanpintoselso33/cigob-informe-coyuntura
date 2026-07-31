---
madr: 4
id: '0165'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'transversal'
archivos: ['scripts/resumir.py', 'scripts/publicar.py', 'scripts/panel_validacion.py', 'web/src/pages/[slug].astro', 'web/public/overrides.css', 'tests/test_resumir.py']
ambito: 'Publicación y web · texto de todas las cards con conclusión'
origen: 'Reconstruido el 2026-07-31 desde los commits ec3d576, d2cf19c y 5390885, la docstring de `scripts/resumir.py` y `tests/test_resumir.py`. El código citaba ADR-0165 pero el ADR nunca se había escrito; lo detectó `tests/test_adr_format.py` en su primera corrida.'
commit: 'd2cf19c'
---

# ADR-0165 — Una oración por card, el desarrollo a un click

## Contexto y planteo del problema

Cada sección del tablero publicaba su análisis completo dentro de la card.
Medido en producción sobre la página de gestión: redundancia del ITCG 1.087
caracteres, matriz cruzada 877, la bajada de validación 796, vintages 432.
Siete cards así son unos cinco mil caracteres de prosa en una página que se
mira para leer números.

Además, en las tres secciones que tienen modal ese mismo texto ya estaba
repetido adentro: la card y el modal decían lo mismo.

Un arreglo previo (ec3d576) había acortado solo la card de validación. Medido
después en producción, el resto de la página seguía igual: el problema no era
una card, era la regla con la que todas publicaban su texto.

## Factores de decisión

- El texto no puede *truncarse*: un corte a mitad de frase o con puntos
  suspensivos es peor que el texto largo, porque deja una afirmación
  metodológica incompleta a la vista.
- Nada puede perderse. El desarrollo tiene que seguir accesible.
- La regla tiene que cubrir automáticamente a las secciones futuras. Si hay
  que acordarse de aplicarla en cada constructor, deja de aplicarse.
- Las conclusiones de este informe se escriben con el resultado adelante y la
  explicación atrás — la misma regla que obligó a poner el factor común al
  principio y no al final. Eso hace que la primera oración alcance como
  resumen. Si en alguna sección el resumen queda flojo, es una señal sobre
  cómo está escrita esa conclusión, no sobre el módulo que la resume.

## Opciones consideradas

- Resumir toda sección con conclusión, en una pasada única al final de
  `publicar.py` — elegida.
- Acortar card por card, a mano (el intento previo de ec3d576).
- Truncar por cantidad de caracteres con puntos suspensivos.

## Decisión

Cada sección publica un `resumen` —la primera oración completa, o las dos
primeras si la primera es muy corta— y la card muestra eso. El corte se hace
siempre en un límite de oración: nunca a mitad de frase y nunca con puntos
suspensivos. El resumen es texto completo y gramatical, no un truncamiento.

El módulo es `scripts/resumir.py`, con `TOPE = 260` caracteres y
`MINIMO_PRIMERA = 120` (por debajo de ese largo la primera oración se
acompaña de la siguiente). La detección de fin de oración excluye el punto
entre dígitos (fechas, montos) y una lista de abreviaturas frecuentes en
estos textos, que si no cortan la oración por la mitad.

`resumir.anotar(informe)` se llama **una sola vez al final de
`publicar.py`**, no en cada constructor de sección: así una sección nueva
queda cubierta sin que nadie tenga que acordarse. La conclusión original no se
recorta — queda intacta para el modal y el desplegable.

El desarrollo va al modal en las tres secciones que lo tienen, y a un
desplegable nativo en las otras cuatro, que no tenían dónde ponerlo. La regla
se aplica también a la **bajada** de cada sección, que es lo primero que se
lee, arriba de la card.

### Consecuencias

- Página de gestión: validación 601 → 207 caracteres, redundancia 1.087 →
  200, cruzada 877 → 326, vintages 432 → 224. El alto de la página baja de
  7.346 a 6.813 px.
- La bajada de validación de gestión pasa de 796 a 175 caracteres, con un
  "Cómo se construye" que abre el resto.
- No se pierde nada: el texto completo sigue publicado, a un click.

### Confirmación

`tests/test_resumir.py` cubre el contrato del módulo: que un texto corto quede
intacto, que el corte caiga en límite de oración y no a mitad de frase, que se
respete el tope, que el resto no se pierda, que no corte en un número con
punto ni en una abreviatura, que una primera oración muy corta se acompañe de
la siguiente, y que `anotar` recorra todo el informe sin tocar la conclusión
original.

## Más información

Este ADR se escribió el 2026-07-31, después de la decisión, al migrar el
corpus a MADR: `tests/test_adr_format.py` detectó que `publicar.py`,
`resumir.py` y `test_resumir.py` citaban un ADR-0165 inexistente. El contenido
se reconstruyó de la docstring de `scripts/resumir.py`, de los mensajes de los
commits ec3d576 / d2cf19c / 5390885 y de los tests — no de memoria. Las cifras
de antes y después son las medidas en producción que registran esos commits.
