---
madr: 4
id: '0326'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'transversal'
archivos: ['web/src/pages/metodologia/index.astro', 'web/public/overrides.css']
relacionado: ['0199', '0192', '0321', '0322']
ambito: 'Sección «El marco» de `/metodologia` — texto público, no cálculo'
origen: 'Apuntes de Juan del 15-sep-2026 (#monitor-de-proyecto-de-gobierno): «cambiar el texto del marco por el proporcionado por Luis». El texto viene del documento de trabajo «Reducir sin simplificar: cómo comunica el Monitor la complejidad», de Luis Babino.'
---

# ADR-0326 — El marco dice cómo comunica, no sólo qué mide

## Contexto y planteo del problema

La sección «El marco» de `/metodologia` explicaba **qué** mide el informe: qué
es la tensión, de dónde salen los cuatro cinturones, qué significa la escala
0–10 y qué es el barbarismo. Nada decía **por qué se muestra así**.

Ese hueco importa porque el Monitor recibe dos críticas opuestas y ninguna se
contesta con los datos: que un número único aplana un fenómeno complejo, y que
mostrar sesenta y pico de indicadores es no decir nada. El informe tiene una
respuesta —está en cómo está construido— y no estaba escrita en ningún lado.

Luis Babino la escribió en un documento de trabajo del equipo, «Reducir sin
simplificar». Juan pidió incorporarla al marco.

## Factores de decisión

- El marco ya tiene una apertura que es **la definición del informe, palabra
  por palabra** (ADR-0199). No se toca.
- Todo ejemplo sobre el propio método tiene que ser **verificable en el repo**.
- El texto es de cara al lector, no una nota interna del equipo.

## Opciones consideradas

- **Reemplazar el marco entero** por el texto de Luis. Se descarta: borraría la
  definición de tensión, los cuatro cinturones, la escala y el barbarismo, que
  es lo que el lector necesita antes de cualquier consideración sobre cómo se
  comunica.
- **Ponerlo en la portada**, junto a `MarcoTension`. Se descarta: ese bloque fue
  recortado dos veces a propósito (ADR-0194, ADR-0199) y su trabajo es contestar
  «tensión de qué» en dos frases. La reflexión sobre el método es meta y va
  donde está el marco completo.
- **Sumarlo al final del marco**, como tramo propio. Elegida.

## Decisión

Se agrega al final de la sección `#marco` un tramo titulado **«Reducir sin
simplificar»**, con la síntesis de Luis como cita, la distinción entre
reduccionismo y simplificación con método, las capas navegables del informe
(cinturón → dimensión → indicador → ficha) y tres ejemplos concretos.

El orden es deliberado: primero qué se mide, después por qué se muestra así.

### Un ejemplo del documento original NO se publicó

El documento citaba, como caso de «descomponer en vez de promediar», *«la
decisión de no fusionar tipo de cambio multilateral con saldo comercial: se
evaluó combinar un precio relativo con una cantidad en un solo número, y se
descartó»*.

**Esa decisión no existe.** No hay ningún ADR que la evalúe ni que la descarte;
lo más cercano, ADR-0073, rechaza copiar al TCRM la regla anti-salto del saldo
comercial, que es otra cosa. En el documento del equipo del 15-sep la fusión
aparece como **pregunta abierta** («¿se podría combinar con el saldo de la
balanza…?», respondida con «opinando sin saber, me suena que sería superador»),
no como decisión tomada.

Publicarla habría sido atribuirle al informe una deliberación que nunca tuvo.
En su lugar van dos casos verificables y recientes:

| Ejemplo | Por qué ilustra el principio | Fuente |
|---|---|---|
| `desequilibrio_monetario` cruza sus dos componentes en matriz en vez de promediarlos | Un componente sano no tapa a uno degradado | ADR-0192 |
| El consumo de carne deja de ser un compuesto único | El total fusionado daba 94,4 mientras la vacuna estaba en 89,2, su mínimo histórico | ADR-0322 |
| La recaudación se descompone en los tributos ligados a la actividad | El agregado puede subir mientras la parte que sigue a la actividad cae — pasó en cinco meses de 2026 | ADR-0321 |

### Consecuencias

- El marco pasa de cuatro párrafos a cuatro más un tramo con subtítulo propio.
- Los tres ejemplos **envejecen con el informe**: si alguno de esos indicadores
  cambia de diseño, el texto queda describiendo algo que ya no es así. Los tres
  citan su ADR, que es lo que permite detectarlo.
- El tramo introduce dos clases nuevas de estilo, `cg-marco-h3` y
  `cg-marco-cita`. Ambas cruzan las dos columnas en desktop: `.cg-marco` usa
  `columns: 2` desde 900px, y sin `column-span: all` el subtítulo quedaría a
  mitad de la columna izquierda con su texto siguiendo en la derecha.

### Confirmación

`npm run build` con 82 páginas y el tramo verificado en
`dist/metodologia/index.html`, leído como texto plano y no como código.

## Pros y contras de las opciones

**Sumarlo al final del marco** · Bueno, porque conserva la definición y agrega
el encuadre. Bueno, porque el lector que llegó hasta ahí ya tiene el vocabulario
para entenderlo. Malo, porque queda lejos de la portada, que es donde más se lee.

**Reemplazar el marco** · Bueno, porque es lo que el apunte pedía en su letra.
Malo, porque destruye contenido que el sitio necesita y que ningún otro lugar
publica.

**Ponerlo en la portada** · Bueno, por visibilidad. Malo, porque revierte dos
decisiones editoriales previas de acortar ese bloque.

## Más información

ADR-0199 repuso el marco en `/metodologia` después de que ADR-0194 lo diera por
mudado sin mudarlo. El documento original de Luis queda como fuente del texto;
este ADR registra qué se tomó y qué no.
