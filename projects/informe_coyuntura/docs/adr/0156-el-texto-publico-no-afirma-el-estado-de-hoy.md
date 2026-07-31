---
madr: 4
id: '0156'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'transversal'
archivos: ['web/src/lib/fichas.ts', 'descripciones.ts']
ambito: 'capa de texto público (`web/src/lib/fichas.ts`, `descripciones.ts`,'
---

# ADR-0156 — El texto público no afirma el estado de hoy

componentes con prosa) + guard nuevo
- **Relacionados**: ADR-0154 y ADR-0155 (los cambios que dejaron el texto viejo y
  destaparon el patrón), el guard de pesos de fichas (`test_fichas_pesos.py`),
  ADR-0119 (registro público sin jerga)

## Contexto y planteo del problema

Observación del editor, después de encontrar una afirmación falsa en la sección de
metodología: **el problema es la cantidad de texto coyuntural, escrito a mano,
sobre datos que cambian mes a mes.**

El caso que lo disparó: la sección de metodología decía que «la matriz cruzada
verifica que cada índice correlacione más con su ancla propia». Con la matriz de
hoy eso es **falso en 2 de los 4 índices** — y nada lo detectaba, porque
`gate_calidad.py` valida datos y estructura del snapshot, y ningún test lee la
prosa.

Al barrer la capa entera aparecieron **13 frases con deixis temporal** en fichas y
4 en descripciones. Dos de ellas ya eran falsas por cambios del mismo día:
nombraban `endeudamiento_familiar` como componente vigente del ITVC cuando había
salido del índice unas horas antes.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

**Regla:** el texto público dice el **método**; el **número lo deriva el
pipeline**. Cuando hace falta nombrar un estado, la frase remite a algo que se
recalcula —la tabla de composición, la serie, la ficha del componente— en vez de
afirmar el valor.

Reescritas con ese criterio:

| dónde | qué decía | por qué |
|---|---|---|
| `itvc.agregacion` | «hoy la vulnerabilidad financiera (**endeudamiento con mora**) está marcada crítica» | **ya era falsa**; ahora remite a la tabla |
| `itvc.agregacion` | «Hoy afecta al **endeudamiento de consumo** y a motos. Su efecto está medido: quita **1,9** puntos» | **ya era falsa**, y el número se movía; ahora remite a las fichas |
| `consumo_carne.limitaciones` | «vacuna cayó **10%**, cerdo subió **12%**, total **3%**» | tres variaciones medidas a mano que se mueven todos los meses |
| `iai.transformaciones` | «**hoy** construcción 65% + capital 35%; cuando… pasa sola a 55/30/15» | composición que **cambia sola**: el texto se rompe el día del cambio |
| `itcg.seleccion` | «**Hoy** el cinturón es 100% automático» | afirmación verificable que puede expirar |
| `descripciones` (asistencia directa) | «en 2023 pasaba por organizaciones; **hoy** va directo» | afirmación de estado, reescrita como el giro que hubo |

### Consecuencias

- La capa de texto queda con menos afirmaciones que mantener, y las que quedan
  están declaradas.
- **Lo que este guard NO cubre, y se dice**: los 62 números estructurales
  (bandas, pesos, base) siguen a mano. Los pesos tienen guard propio; las anclas
  de bandas no, y una recalibración puede dejar el texto viejo. Es la próxima
  pieza de la misma familia.
- Tampoco cubre las afirmaciones de estado **sin** deixis, del tipo «la matriz
  verifica que…», que fue el caso original. Ésa se arregló a mano en ADR-0155 y
  hoy el texto de la matriz **se deriva de los números en cada corrida**, que es
  la solución de fondo: cuando una afirmación se puede computar, se computa.

## Más información

### El diagnóstico separa dos cosas que parecían una

Del barrido salieron **62 frases con números** fuera del changelog. La mayoría
**no es el problema**: son anclas de bandas («más de 50% → el más alto»), pesos
estructurales («pesa 15% junto a…»), el período base, números de ley. Son
metodología, no coyuntura, y los pesos además ya tienen su propio guard.

El problema es más chico y más específico: **las frases que fechan una afirmación
en el presente.** Son las que expiran sin que nadie las edite, porque no hay nada
que las contradiga hasta que alguien las lee.

### El guard: no prohíbe la deixis, obliga a declararla

`tests/test_texto_publico_no_caduca.py`. Cada aparición de «hoy»,
«actualmente», «por ahora» y compañía en la prosa pública tiene que estar en un
inventario con **su motivo**. Una frase nueva rompe el test y fuerza la elección:
reescribirla como método —casi siempre lo correcto— o asumir explícitamente que
alguien la va a mantener.

El criterio para aceptar una es uno solo: **que remita a algo que el pipeline
recalcula**. Con ese filtro quedaron 8 aceptadas, y son de tres tipos:
la que apunta a la tabla de composición; la que declara un límite del estado del
arte («la mejor señal automatizable disponible hoy» — si aparece una fuente
mejor se cambia el indicador, no el texto); y la que declara un rezago o un
alcance pendiente.

Tres detalles del diseño del test, todos por experiencia previa de este repo:

- **excluye `cambios`**, que es un changelog: sus entradas dicen lo que era cierto
  ESE día y tienen que quedar como están;
- **exige que el inventario no tenga entradas de más** — una entrada huérfana deja
  la puerta abierta para que vuelva a entrar deixis por ahí sin aviso;
- **tiene un test de que el test mira algo**, contra el falso verde: si el parseo
  de `fichas.ts` se rompe y no encuentra ninguna cadena, los otros tres pasarían
  vacíos. Verificado además al revés, inyectando una frase: el guard la marca.
