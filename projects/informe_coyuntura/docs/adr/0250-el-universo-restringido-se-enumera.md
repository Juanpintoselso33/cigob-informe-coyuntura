---
madr: 4
id: '0250'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [trabajo_independiente]
archivos: ['scripts/vida_cotidiana/collectors/trabajo_independiente.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'web/src/lib/datos.ts', 'tests/test_universos_declarados.py']
relacionado: ['0219']
ambito: 'Cinturón vida cotidiana · ITCIS · `trabajo_independiente` · qué categorías entran al cociente y cuál no'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «excluye monotributo social tanto del numerador como del denominador, aunque el rótulo promete todo el empleo registrado SIPA»'
---

# ADR-0250 — El universo restringido se enumera

## Contexto y planteo del problema

`trabajo_independiente` publicaba **20,6% del empleo registrado**. El universo no
era «el empleo registrado»: dejaba afuera al **monotributo social**, de los dos
lados del cociente.

La exclusión está bien fundada, y se verificó de nuevo contra la fuente antes de
tocar nada. El padrón del monotributo social cae de **653 mil a 259 mil personas
entre noviembre y diciembre de 2024** — un −60% en un mes. No hubo nada parecido
en el mercado de trabajo: fue una depuración del régimen. Es el único salto de
esa magnitud en catorce años de serie.

Y el efecto sobre el indicador no es de matiz. Con el régimen social adentro, la
participación independiente **cae** de 22,9% a 22,1% desde el 4T-2023; sin él,
**sube** de 19,1% a 20,6%. Las dos lecturas son opuestas y sólo una describe la
economía.

El problema, entonces, no era la exclusión: era que **el rótulo prometía otro
universo**. «% del empleo registrado» se lee como «SIPA entero», y quien
comparara contra el total de SIPA encontraría otro número sin saber por qué.

## Factores de decisión

- **La exclusión es correcta y está medida.** Incluir el régimen haría que el
  indicador midiera una reforma administrativa y la publicara, con signo
  invertido, como reconfiguración productiva.
- **Un universo restringido tiene que poder enumerarse.** Es la diferencia entre
  una exclusión declarada y un recorte silencioso.
- **El lector tiene que poder ver qué cambia al incluirlo**, en vez de tener que
  creernos.

## Opciones consideradas

- **A — Incluir el monotributo social** en numerador y denominador, como pedía
  la primera lectura de la auditoría.
- **B — Conservar la exclusión y cambiar el rótulo** al universo restringido,
  enumerando las categorías y publicando el contraste.

## Decisión

**Opción B**, que es la que el propio mandato de la auditoría prevé: «si no hay
una historia reproducible, cambiar el rótulo al universo restringido en vez de
imputarlo». No la hay — el quiebre de diciembre de 2024 parte la serie en dos y
no es empalmable.

La card pasa a declarar:

- **unidad**: `% del empleo registrado SIPA, sin monotributo social`;
- **numerador**: autónomos, monotributo general;
- **denominador**: esos dos más asalariados privados, públicos y de casas
  particulares;
- **el régimen excluido, con el mes de su quiebre**;
- **cuánto daría con él adentro** (22,1% contra 20,6%).

Ese contraste va **dentro de la explicación de la card**, no como card propia:
un indicador que no puntúa no es card ([[0153-pobreza-entra-al-itvc-y-no-hay-cards-de-contexto]]).

### Consecuencias

- **El valor no cambia**: sigue siendo 20,6%. Cambian el rótulo y lo que la card
  cuenta de sí misma.
- La suma se puede reproducir desde SIPA con las cinco series nombradas.
- Queda una decisión anotada: si en algún momento INDEC o el SIPA publican una
  serie homogénea del régimen social que salve el quiebre, la opción A vuelve a
  estar sobre la mesa y el rótulo tendría que volver a «empleo registrado».

### Confirmación

`tests/test_universos_declarados.py`:

- las categorías de los dos lados están enumeradas, y el numerador está
  contenido en el denominador;
- el régimen excluido está nombrado junto con el mes del quiebre;
- **la unidad declara el universo restringido** y ya no puede ser `% del empleo
  registrado` a secas.

## Pros y contras de las opciones

### A — Incluir el monotributo social

- Bueno, porque el rótulo actual quedaría cierto sin tocar nada más.
- Malo, porque el indicador pasaría a medir una depuración de padrón de −394 mil
  personas y a publicarla, invertida, como mejora del empleo.

### B — Rótulo restringido y enumerado

- Bueno, porque conserva la serie interpretable y hace auditable la exclusión.
- Malo, porque el rótulo es más largo y ya no se compara de un vistazo contra el
  total de SIPA. Es el costo de no prometer lo que no se mide.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_impacto_social.md`.
- [[0219-la-contracara-del-cierre-el-trabajo-independiente]] crea el indicador y
  ya documentaba la exclusión; lo que faltaba era declararla en el rótulo.
