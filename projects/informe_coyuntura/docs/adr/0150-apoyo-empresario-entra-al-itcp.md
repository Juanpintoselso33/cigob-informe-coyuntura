# ADR-0150 — Apoyo empresario entra al ITCP, y el bug que lo encontró

- **Estado**: Aceptado
- **Fecha**: 2026-07-27
- **Ámbito**: cinturón político (ITCP) · dimensión `sector_privado`
- **Relacionados**: ADR-0148 (la pasada que esto **descarta**), ADR-0149
  (detector), ADR-0131 (protocolo de codificación, **corregido acá**),
  ADR-0088 (la dimensión), ADR-0145 (el negativo que el usuario hizo revisar),
  ADR-0045 (no recalibrar para que dé mejor)

## Lo que se buscaba y lo que apareció

ADR-0148 dejó 103 comunicados de AEA y UIA codificados y una sola cosa
pendiente para publicar: la segunda pasada con kappa ≥ 0,70.

Se hizo. Y la segunda pasada encontró algo que ningún test, ningún gate y
ninguna revisión propia había encontrado: **los 57 comunicados de UIA se habían
codificado sin texto.**

## El bug

El scraper de UIA barría el HTML entero y se quedaba con el menú de navegación
del sitio. Los 57 textos del registro eran **idénticos** — mismo bloque de
menú, carácter por carácter. El comunicado vive en `<div class="nota--body">`,
que nunca se leyó.

O sea que más de la mitad del corpus se clasificó **sólo por el título**. Y
títulos como «Comunicado de la Unión Industrial Argentina» o «COMUNICADO DEL
G6» no dicen absolutamente nada. Al primero yo le había asignado
`critica`/`ejecutivo_nacional`. Con el texto real resulta ser, efectivamente,
una crítica frontal a declaraciones del Presidente — **acerté por prior, no por
lectura**, que para un protocolo de análisis de contenido es lo mismo que
errar.

Lo encontraron los dos codificadores ciegos, por separado, en sus notas de
casos difíciles. Ninguno de los dos podía saber que era un bug: los dos
reportaron «los textos de UIA vienen todos iguales, codifiqué por el título».

**Es el argumento entero a favor de la segunda pasada.** No sirvió para lo que
se esperaba —medir si dos personas coinciden— sino para algo que ninguna
verificación automática hacía: mirar el material con ojos que no lo habían
armado.

## El diseño de concordancia también estaba mal

La v1 de las reglas decía: «la segunda pasada la tiene que hacer otra persona».
Eso mide *al autor del manual contra un tercero*, y confunde dos cosas
distintas: que las reglas sean ambiguas, y que el autor codifique distinto de
lo que escribió. La primera medición lo mostró crudamente:

| par | κ postura | κ destinatario |
|---|---|---|
| autor vs. ciego A | 0,732 | 0,653 |
| autor vs. ciego B | 0,752 | 0,668 |
| **ciego A vs. ciego B** | **0,925** | **0,953** |

Los dos ciegos coincidían casi perfectamente **entre sí** y discrepaban
conmigo. El desviado era el autor, y de forma sistemática: yo tenía 35 casos en
`ejecutivo_nacional` y ellos 47 y 50, porque **dejaba que el eje 1 contaminara
el eje 2** — si un texto no comentaba ninguna medida, lo mandaba a
`externo_o_propio` en vez de preguntarme a quién le hablaba.

**Diseño nuevo, que es el estándar de análisis de contenido**: dos codificadores
independientes ciegos entre sí codifican el corpus completo, el kappa se mide
**entre ellos**, y quien escribió el manual **no codifica: adjudica** los
desacuerdos una vez medido el número. Esto corrige el anexo de ADR-0131 para
todo el proyecto.

## Reglas v2

Los dos ciegos marcaron por separado los mismos cinco huecos del manual. Se
cierran, y la pasada se rehace entera (ADR-0131 prohíbe reinterpretar una
pasada ya hecha):

1. **Documento programático o doctrinario** («el sector privado es clave para el
   desarrollo»): neutro, y destinatario `ejecutivo_nacional` si interpela a la
   política nacional. **Adopta el criterio contrario al que yo había usado.**
2. **Diagnóstico estructural** (presión tributaria, costo argentino): crítica si
   atribuye el problema a una política vigente o pide cambiarla; neutro si sólo
   describe una condición.
3. **Defensa de la independencia judicial**: se aplica la regla del ámbito donde
   se decide — juicio político → congreso; reclamo de acatamiento de un fallo →
   ejecutivo; defensa genérica → judicial.
4. **Anuncio del Ejecutivo aún no ingresado al Congreso**: ejecutivo_nacional.
5. **Lamento o repudio por un hecho que no decidió el Estado**: neutro y
   externo_o_propio, salvo que el texto atribuya el hecho a una política.
6. Y **`dudoso` deja de estar reservado al caso mixto**: cubre también «el
   material no alcanza para determinar la postura».

Se agrega además una **regla madre** en el eje 2: *el destinatario se decide con
independencia de la postura*. Es exactamente el error sistemático de arriba,
escrito para que no vuelva.

Que las aclaraciones no están escritas para que el número dé mejor se verifica
solo: en el punto 1, el más frecuente de todos, la regla nueva **contradice** la
codificación descartada.

## Resultado

Dos codificadores ciegos nuevos (C y D), corpus con el texto real, reglas v2:

| eje | acuerdo | **kappa** |
|---|---|---|
| postura | 100,0 % | **1,000** |
| destinatario | 97,1 % | **0,955** |

Tres desacuerdos en 103 casos, los tres de `destinatario` sobre casos `neutro`.
**El conjunto computable es idéntico en las dos pasadas: 31 casos, cero
desacuerdo** — que es lo único que mueve el indicador. Los tres se adjudican a
`externo_o_propio`: son reportes de evento institucional (aniversario de AEA,
una cumbre del CFI, la Conferencia Industrial) y la regla manda
`externo_o_propio` cuando el texto habla de la cámara o su sector sin
interpelar a un poder.

**Advertencia sobre ese kappa, que va también a la ficha pública:** los dos
codificadores son agentes de IA del mismo modelo base. Son genuinamente
independientes —ninguno vio el trabajo del otro— pero comparten priores y
concuerdan más de lo que concordarían dos personas de formación distinta. El
número acredita que **el manual es unívoco**, no que cualquier par de lectores
humanos llegaría a lo mismo. Un κ de 1,000 en un eje de cuatro categorías sobre
103 casos debería leerse con esa salvedad puesta.

## El indicador

`apoyo_empresario` = (apoyos − críticas) / (apoyos + críticas) sobre los
comunicados dirigidos al Ejecutivo nacional, ventana móvil de 12 meses.

- **32 puntos mensuales desde dic-2023, sin huecos.** n por ventana entre 3 y 8,
  promedio 5,7.
- Rango observado **−0,667 a +0,333**. Hoy −0,667.
- La serie cuenta una historia legible: crítica sostenida durante 2024, mejora
  hacia el equilibrio entre nov-2025 y feb-2026, y quiebre brusco en marzo de
  2026 — el mes del comunicado de la UIA por las declaraciones presidenciales
  sobre «los que defienden la industria», seguido del cierre de Fate y del
  reclamo por la provisión de gas.

**Anclas**: 0,6 / 0,2 / −0,2 / −0,6, que parten el rango *teórico* (−1 a +1) en
cinco tramos iguales centrados en el cero. No se calibran contra lo observado:
ADR-0045 sólo autoriza eso cuando el extremo es matemáticamente inalcanzable, y
±1 —«los pronunciamientos de doce meses todos en el mismo sentido»— con n≈6 no
tiene nada de inalcanzable. Que la serie no toque los extremos es desempeño
real.

**Peso: 50/50 con `brecha_obra_publica`**, fijado antes de mirar su efecto sobre
el ITCP. Miden cosas distintas y ninguna domina: la brecha es una medida
*revelada* (dato duro del INDEC, validado contra Construya r=+0,79) pero de un
solo sector; ésta es *declarada* (lo que las cámaras firman), directa sobre la
relación con el Ejecutivo y sobre cualquier tema, pero de sólo dos entidades.
Revelada vs. declarada, angosta vs. ancha: el empate es el reparto honesto.

Familia `tension` (conducta de un tercero hacia el Gobierno) y rezago 6,0 meses
(centroide de la ventana; la fuente no tiene rezago de publicación).

## Consecuencias

- **`_uia_comunicado` extrae el cuerpo** desde `nota--body` y lo guarda en el
  aviso: el detector de ADR-0149 ahora entrega material para codificar, no sólo
  un título. Era la causa raíz.
- **La serie se calcula una sola vez**, en `politica.apoyo_empresario_serie()`;
  la card devuelve su último punto y `serie_12m` sale del registro. Card y serie
  no pueden divergir, que es lo que verifica G3 (ADR-0086/0087).
- **La card publica cuántos comunicados quedan sin codificar.** Es el único
  indicador del cinturón cuyo dato lo actualiza una persona: si nadie codifica,
  la serie se congela sin que falle nada. El número a la vista es la única
  defensa contra eso.
- El test de ADR-0149 que verificaba que `apoyo_empresario` **no** estuviera en
  `itcp.py` se da vuelta: ahora verifica que esté, con bandas y peso.
- **La primera pasada (ADR-0148) queda descartada por completo**, no corregida.

## Lo que queda pendiente

- **Sumar cámaras.** Dos entidades dejan afuera al agro y a la banca. SRA y
  AmCham siguen sin ser relevables por política declarada de sus sitios
  (`robots.txt` y login de socios); si alguna vez hacen falta, la vía es
  pedírselo a la entidad, no sortear el bloqueo.
- **El texto de AEA sigue cortado en 700 caracteres en origen**, porque viene de
  extraer PDFs. En comunicados que abren con un rodeo puede quedar afuera el
  pasaje que fija posición. Los dos codificadores lo marcaron (caso `idx 83`).
  Se arregla releyendo los 46 PDFs completos, y eso obliga a rehacer la pasada.
- **Ninguna verificación automática mira el contenido de los textos.** El bug de
  UIA habría sobrevivido indefinidamente. El test nuevo
  `test_los_textos_del_registro_no_son_todos_iguales` cubre exactamente esa
  forma, pero la lección general es más ancha: los gates verifican estructura,
  frescura y coherencia card-serie, y ninguno verifica que el material que se
  leyó sea el material que se creía leer.
