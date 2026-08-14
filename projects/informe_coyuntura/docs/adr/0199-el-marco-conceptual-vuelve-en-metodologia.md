---
madr: 4
id: '0199'
estado: 'aceptado'
fecha: 2026-08-13
cinturon: 'transversal'
archivos: ['web/src/pages/metodologia/index.astro', 'web/public/overrides.css', 'tests/test_marco_conceptual.py']
relacionado: ['0194', '0200', '0201', '0202']
ambito: 'Capa textual del informe — el encuadre conceptual que se publica'
origen: 'El editor notó que la explicación del concepto de tensión había desaparecido del sitio y pidió reponerla en /metodologia'
---

# ADR-0199 — El marco conceptual vuelve, y esta vez sí vive en /metodologia

## Contexto y planteo del problema

El rediseño de la aguja ([[0194-la-aguja-es-la-lectura-primaria]]) sacó del hero
de la portada el párrafo que definía qué mide el informe:

> La gobernabilidad de un proyecto de gobierno no se mide por la ausencia de
> conflictos, sino por su capacidad para **procesar la tensión** entre las
> demandas del entorno y los recursos de acción disponibles. Este informe de
> coyuntura sistematiza el mapa de tensiones de la Argentina actual a través de
> **cinco cinturones analíticos**, examinando cómo las decisiones oficiales
> operan un constante intercambio de problemas donde la viabilidad fiscal,
> cambiaria, social y política se recalculan en tiempo real.

El commit lo justificó diciendo que «el encuadre conceptual del observatorio
vive en /metodologia». **No era cierto: nunca había estado ahí, y no se mudó.**
Verificado sobre el árbol de trabajo: `procesar la tensión`, `demandas del
entorno`, `recursos de acción` e `intercambio de problemas` devuelven cero
resultados en todo el repositorio desde `1f6aa0e` (2026-08-12 06:09).

El resultado es que durante un día el sitio publicó una tensión 0-10 por
cinturón, una aguja, un semáforo de cuatro tramos y una regla de «dos o más
tensionados» **sin decir en ninguna página qué es esa tensión**, por qué se mide
en cinturones ni de dónde sale el marco. La palabra «barbarismo» estaba peor:
aparece en el BLUF de la portada, como chip en cada card de cinturón y en la
página de cada uno, y no está definida en ningún lado del sitio.

Conviene separar esto del resto de los recortes de esa mañana, que fueron
buenos: el subtítulo de Evolución (386 → 91 caracteres), los dos subtítulos de
la página de cinturón, las descripciones de los índices (1.205 → 426) y la
fórmula de conversión a tensión salieron porque **la aguja los volvió
redundantes** — muestran lo que ya se ve. El encuadre conceptual no es
redundante con ninguna aguja: una aguja no puede decir qué es lo que mide.

Ningún gate lo detectó, y ninguno podía: `gate_calidad.py` mira estructura,
frescura y card-contra-serie; los tests de reconciliación comparan el snapshot
consigo mismo. **Nada en el proyecto mira la prosa publicada.** Es la misma
clase de hueco que motivó `tests/test_web_labels.py`.

## Factores de decisión

- El rediseño no se toca: la aguja sigue siendo la lectura primaria y la portada
  sigue sin párrafo institucional. Esto no revierte 0194.
- El marco es lo primero que hay que entender del informe, no una nota al pie.
- Los umbrales no se escriben en el front — factor heredado de 0194 y que sigue
  vigente: el texto describe la dirección de la escala, nunca los cortes.
- El párrafo es texto institucional de la Fundación: se repone **palabra por
  palabra**, no se reescribe ni se «mejora».

## Opciones consideradas

- **A. El marco abre /metodologia, en prosa.**
- **B. Devolverlo al hero de la portada.**
- **C. Una página nueva `/marco`.**
- **D. Trocearlo en cards del grid de metodología**, como el resto de la página.

## Decisión

**Opción A.** Una sección nueva encabeza `/metodologia`, antes de «El estándar»:
eyebrow «El marco», título «Qué es la tensión que mide el informe», cuatro
párrafos de prosa.

1. **El párrafo original, verbatim.** Es la definición y abre la página.
2. **Qué es un cinturón**: el marco CIGOB-Matus ampliado de tres cinturones a
   cinco, y qué mide el quinto (sintonía emocional con el humor social), que es
   el que no viene de Matus.
3. **Qué es la escala 0-10**: dirección (0 aflojado, 10 apretado), cuáles cuatro
   derivan de un índice paramétrico propio y cuál todavía promedia proxies. Sin
   cortes numéricos.
4. **Qué es el barbarismo**: mirar un solo cinturón, con los tres nombres que el
   sitio ya usa (tecnocrático, político, gerencial), y el enganche con la regla
   de lectura que ya vive dos secciones más abajo.

El orden de la página pasa a ser **qué se mide → cómo se documenta → por qué
creerle → los índices → los indicadores**.

### Consecuencias

- `/metodologia` deja de ser sólo el diccionario de fichas: es la página del
  método completo. El lead del hero lo declara («Primero el marco… Para leer el
  informe alcanza con el marco; para auditarlo, está todo»), en lugar del
  anterior «para leer el informe no hace falta nada de esto», que con el marco
  adentro ya era falso.
- «Barbarismo», que el sitio usaba en tres lugares sin definir, queda definido.
- La prosa larga vuelve a crecer en `/metodologia` — que es adonde el rediseño
  quiso mandarla, así que no contradice a 0194.
- **Deuda declarada**: el Nav apunta «Metodología» a `/#metodologia` (la sección
  de la portada), no a `/metodologia`. El marco queda a dos clics del lector que
  usa el Nav. No se toca acá para no mezclar navegación con contenido.

### Confirmación

`tests/test_marco_conceptual.py`: comprueba que el párrafo original siga
publicado en `/metodologia` —normalizando espacios, porque el JSX lo parte en
líneas— y que las cuatro nociones que el resto del sitio usa sin definir
(tensión, cinturón, escala 0-10, barbarismo) estén nombradas en la sección.

Es un test de presencia de prosa, algo que el proyecto no tenía. No juzga la
redacción: hace que la próxima poda tenga que borrar un test para borrar el
marco, en vez de llevárselo sin que nadie se entere. Que esta desaparición haya
durado un día y la haya encontrado una pregunta del editor, y no un gate, es el
argumento.

## Pros y contras de las opciones

- **A. Abre /metodologia, en prosa.** A favor: es adonde 0194 dijo que estaba,
  se lee antes que el estándar y el «cómo», y no le devuelve texto a la portada.
  En contra: la página crece y su h1 sigue diciendo «Diccionario de
  indicadores», que ahora le queda corto.
- **B. Al hero de la portada.** A favor: es de donde salió y donde primero hace
  falta. En contra: es exactamente lo que 0194 decidió sacar, con razones que
  siguen siendo buenas — el estado se lee antes de leer.
- **C. Página nueva `/marco`.** A favor: separa encuadre de documentación. En
  contra: una página entera para cuatro párrafos, un ítem más de navegación, y
  parte en dos lo que el lector busca junto.
- **D. Cards del grid.** A favor: uniforme con el resto de `/metodologia`. En
  contra: el encuadre es un argumento encadenado (qué es la tensión → qué es un
  cinturón → cómo se mide → qué pasa si mirás uno solo); en cuatro tiles se lee
  como cuatro afirmaciones sueltas.

## Más información

- El texto restaurado es el de `Hero.astro` previo a `1f6aa0e`, sin cambios.
- La ampliación de tres cinturones a cinco y la definición del quinto salen de
  «Marco Conceptual del Informe de Coyuntura» (Fundación CIGOB, mayo 2026),
  citado en `docs/archivo/cinturon_espiritu_epoca.md`.
- Los nombres de los tres barbarismos y su lectura salen de los análisis por
  pestaña en `docs/archivo/` (02 macro, 03 política, 05 gestión), que a su vez
  citan el brief de CIGOB.
- Queda abierto si `/metodologia` debería llamarse «Metodología» en vez de
  «Diccionario de indicadores» ahora que contiene las dos cosas, y si el Nav
  debería apuntar ahí.
