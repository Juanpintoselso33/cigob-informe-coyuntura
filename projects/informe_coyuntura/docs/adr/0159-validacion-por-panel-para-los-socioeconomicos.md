---
madr: 4
id: '0159'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'transversal'
cierra: ['0158']
relacionado: ['0167', '0176']
cerrado_por: ['0162']
ambito: 'validación externa del ITVC, ITCG e ITCP; módulo'
---

# ADR-0159 — Validación por panel para los compuestos socioeconómicos

`scripts/panel_validacion.py`
- **Relacionados**: ADR-0158 (el régimen del ITCM, de la otra familia), ADR-0155
  (ancla del ITVC), ADR-0031 (matriz cruzada), ADR-0019 D6

## Contexto y planteo del problema

Cierra la objeción del editor: **validar un compuesto contra una sola variable es
comparar peras con manzanas.** ADR-0158 resolvió la mitad económica; ésta es la
otra.

Las guías UNECE/ONU dicen que los compuestos **socioeconómicos** normalmente no
tienen serie de referencia, y prescriben (§6.61) compararlos con **varias
estadísticas relacionadas** y **explicar las diferencias al publicar**. El ITVC,
el ITCG y el ITCP son de esa familia.

## Opciones consideradas

- **Comparar contra un panel de 8 estadísticas externas**, ninguna de ellas componente de ninguno de los cuatro índices —hay un test que lo verifica—, reportando el promedio convergente, el discriminante y la brecha entre ambos — elegida.
- **Validar contra una sola serie externa** — descartada.

## Decisión

Cada uno se compara contra un **panel de 8 estadísticas externas**, ninguna de
las cuales es componente de ninguno de los cuatro índices (hay un test que lo
verifica). Se reportan dos promedios —contra las de su propia familia
(convergente) y contra las ajenas (discriminante)— y la **brecha** entre ambos,
en niveles y en primeras diferencias.

| familia | estadísticas |
|---|---|
| ITVC | consumo en supermercados · en autoservicios mayoristas · en centros de compras |
| ITCG | Merval en dólares |
| ITCP | incertidumbre de política (EPU) · confianza en el gobierno · clima electoral |
| ITCM | marcha de la actividad (su ancla, ADR-0158; acá entra sólo como ajena) |

**Las familias se fijan por concepto y antes de mirar resultados**, en el módulo.
Es la parte que no puede decidirse con los números: asignar la familia según con
quién correlaciona mejor volvería la prueba circular y siempre daría bien.

### Consecuencias

- Las tres secciones de validación publican el perfil además de su gráfico. El
  gráfico sigue mostrando una sola estadística porque la sección dibuja un par de
  series; el panel va en la conclusión.
- **El pool externo es fino y hay que decirlo**: de las 97 series publicadas, 69
  ya son componentes de algún índice, y de las 28 restantes la mayoría son
  transformaciones o insumos de componentes. Por eso el ITCG tiene **una sola**
  estadística de su familia, que es poco para un promedio.
- El texto se genera en `publicar.py` a partir de los números guardados, no se
  guarda escrito. Si viniera armado desde `validacion_externa.py`, corregir una
  redacción obligaría a re-correr un script que sale a la red — el mismo tipo de
  acoplamiento que ya causó problemas en esta sesión.
- **Queda pendiente**: el paso 9 del handbook pide además «identificar vínculos
  mediante **regresiones**», que el panel no hace. Y el ITCG merece más
  estadísticas de su familia.

## Más información

### Resultado, incluido el que no confirma

| índice | niveles (conv. / disc.) | brecha | diferencias (conv. / disc.) | brecha |
|---|---|---|---|---|
| **ITCP** | 0,410 / 0,230 | **+0,18** | 0,367 / 0,167 | **+0,20** |
| ITVC | 0,342 / 0,253 | +0,09 | 0,152 / 0,292 | **−0,14** |
| ITCG | 0,747 / 0,434 | +0,31 | 0,119 / 0,159 | **−0,04** |

**El ITCP pasa en los dos planos.** El ITVC y el ITCG pasan en niveles y **no en
diferencias**: descontada la tendencia común del período, se mueven tanto o más
con estadísticas de otros terrenos que con las del suyo.

Eso **se publica**, y es el punto de todo el cambio. El estándar pide explicar
las diferencias, no informar sólo las que confirman; el precedente que las
propias guías citan —el índice de situación de vida del SCP holandés— publica que
explica apenas el 4% de la variación en felicidad. Un resultado débil declarado
vale más que uno fuerte que en realidad medía la tendencia del período.

El texto público lo dice con esas palabras y agrega la salvedad que corresponde:
con unos treinta meses de historia y un panel corto, es **un resultado a vigilar
antes que un veredicto**.

### Por qué esto es mejor que lo que había

Un ancla única daba **un** número y ninguna forma de saber si significaba algo.
El panel hace visible lo que ese número escondía: que en niveles casi todo
correlaciona con casi todo. El caso más claro apareció al medirlo — el índice de
salarios del sector público correlaciona **+0,97** con el ITCG, más que cualquier
ancla propia de cualquier cinturón, sólo porque las dos series suben de forma
monótona. Con un par por índice, ese hecho no se ve nunca.
