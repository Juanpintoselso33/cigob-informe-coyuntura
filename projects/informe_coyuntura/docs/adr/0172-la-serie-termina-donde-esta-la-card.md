---
madr: 4
id: '0172'
estado: 'aceptado'
fecha: 2026-08-05
cinturon: 'politica'
indice: 'ITCP'
archivos: ['scripts/descargar_series.py', 'scripts/gate_calidad.py']
continua: ['0091']
relacionado: ['0089', '0133']
ambito: 'Series de ventana móvil · invariante G3 card↔serie'
origen: 'El gate G3 cortó la publicación cuatro noches seguidas por veto_quorum; al ir a declararlo excepción aparecieron otros siete indicadores perdonados por la misma causa'
---

# ADR-0172 — La serie termina donde está la card

## Contexto y planteo del problema

Los indicadores de ventana móvil calculan lo mismo dos veces con **anclas
distintas**: la card evalúa la ventana en `date.today()` y la serie mensual a
cada **fin de mes cerrado**. Las dos ventanas están corridas un mes de forma
permanente. Coinciden sólo los días en que caen igual — por casualidad.

G3 existe justamente para verificar que el último punto de la serie coincida
con el titular de la card. Ante cada choque de esta familia se fue declarando
una excepción. Al 4-ago-2026 había **8 indicadores perdonados y todos por la
misma causa**:

| Indicador | Perdonado desde |
|---|---|
| `alineamiento_senadores_prov` | 2026-07-09 |
| `cohesion_bloque` | 2026-07-10 |
| `votometro_ventaja_lla` | 2026-07-09 |
| `derrotas_legislativas` | 2026-07-09 |
| `cepo_mulc` | 2026-07-16 |
| `bloqueo_sostenido` | 2026-07-16 |
| `desafios_legislativos` | 2026-07-19 |
| `veto_quorum` | 2026-08-04 |

En esa familia G3 ya no verificaba nada: detectaba el almanaque y se lo
perdonaba a sí mismo.

**Lo que el waiver tapaba no era cosmético.** El 5-ago-2026,
`desafios_legislativos` publicaba:

- **titular: 3** normas desafiadas (ventana sep-2025 → ago-2026) → puntaje **90,0**
- **último punto del gráfico, justo debajo: 10** (ventana ago-2025 → jul-2026) → puntaje **43,6**

Los dos números son correctos para su ventana. La diferencia es que los **siete
desafíos de agosto de 2025** —cinco decretos el día 7, dos leyes el día 20— salen
de la ventana todos juntos al rodar el mes. La página se contradecía arriba y
abajo del mismo indicador, y G3 lo dejaba pasar por diseño. Lo detectó
`tests/test_puntaje_unico_camino.py`, tres pasos más adelante del pipeline y por
otro camino.

`veto_quorum` mostró la otra cara del mismo problema: con la card en 1/10 = 10,0
y la serie en 1/12 = 8,3, **cortó la publicación del informe entero cuatro noches
seguidas** (1 al 4 de agosto). Cinco cinturones sin publicar por una diferencia
de denominador que nadie miró, porque el pipeline no avisa cuando falla.

## Factores de decisión

- Un invariante que se perdona ocho veces por la misma causa dejó de ser un
  invariante. O la asimetría se elimina, o G3 no significa nada para esa familia.
- La contradicción es **visible para el lector**: titular y gráfico del mismo
  indicador, en la misma pantalla, con puntajes de 90 y 43,6.
- Que la única red que atrapó esto haya sido un test de otro paso es señal de que
  el waiver movía el problema, no lo resolvía.
- El titular tiene que seguir siendo la foto de HOY: el tablero declara mostrar
  la situación actual, y anclar la card al último mes cerrado la dejaría hasta 30
  días desfasada por diseño.

## Opciones consideradas

- **Que la serie lleve un punto final anclado a hoy, además de los fines de mes
  cerrados** — elegida. Card y serie miran la misma ventana y coinciden por
  construcción, sin tolerancia.
- **Anclar la card al último mes cerrado** — descartada: también las alinea, pero
  el titular pasa a estar hasta un mes viejo en un tablero que dice mostrar hoy, y
  el ITCP publicaría 43,6 donde hoy publica 90 por una convención de calendario.
- **Declarar la excepción número nueve y publicar** — descartada: es cómo se
  llegó a ocho. Deja la contradicción en la página.

## Decisión

### 1. `_fines_de_mes` acepta `incluir_hoy`

Con `incluir_hoy=True` agrega `hasta` como punto final cuando no es ya un fin de
mes. Las series de ventana móvil pasan a terminar en el mismo instante que
evalúa la card, así que el último punto del gráfico **es** el titular.

Optan por él los siete llamadores de la familia: `veto_quorum`,
`derrotas_legislativas`, `bloqueo_sostenido`, `desafios_legislativos`,
`cohesion_bloque` (las dos cámaras) y `alineamiento_senadores_prov`.
`fetch_adhesion_reformas_provincial_serie` queda como estaba: su card no se
ancla a hoy.

### 2. Salen cuatro excepciones de G3

`veto_quorum`, `derrotas_legislativas`, `bloqueo_sostenido` y
`desafios_legislativos` vuelven a estar bajo vigilancia de G3. Verificado contra
datos vivos: card y serie coinciden **exactas**, no dentro de tolerancia.

| Indicador | card | serie[-1] |
|---|---:|---:|
| `desafios_legislativos` | 3,0 | 3,0 |
| `derrotas_legislativas` | 3 | 3 |
| `bloqueo_sostenido` | 33,3 | 33,3 |
| `veto_quorum` | 10,0 | 10,0 |

### Consecuencias

- El gráfico de `desafios_legislativos` gana el acantilado de 10 a 3. Es real e
  informativo: el Congreso dejó de confrontar después de septiembre de 2025.
- G3 vuelve a ser un chequeo con dientes para cuatro indicadores que llevaban
  entre tres semanas y un día sin verificarse.
- El último punto de cada serie deja de caer en fin de mes. Cualquier consumidor
  que asuma cadencia mensual estricta ve un intervalo corto al final.

### Confirmación

`gate_calidad.py` (G3) sobre los cuatro indicadores sin excepción, y
`tests/test_puntaje_unico_camino.py::test_ninguna_serie_mide_otra_magnitud_que_la_que_puntua_su_indice`,
que es el que detectó la contradicción.

## Más información

### Limitaciones

- **`cohesion_bloque` y `alineamiento_senadores_prov` siguen perdonados.** Se les
  cambió el anclaje igual que al resto, pero no pude verificarlos contra datos
  vivos y quedan con waiver hasta que una corrida real lo confirme. Hay un motivo
  concreto para no darlos por hechos: el punto de hoy se ancla a medianoche
  (`datetime(fin_mes.year, fin_mes.month, fin_mes.day)`) y la card usa la hora de
  la corrida, así que un acta votada ese mismo día los separa. `cohesion_bloque`
  suma que el compuesto bicameral cruza dos series por fecha y basta con que una
  cámara no tenga punto de hoy.
- **`votometro_ventaja_lla` y `cepo_mulc` no se tocaron.** No pasan por
  `_fines_de_mes`: sus series se arman por otro camino. La causa raíz es la
  misma y la solución debería serlo, pero requiere trabajo aparte.
- Este ADR alinea las anclas; **no reduce la volatilidad de fin de ventana**. Un
  indicador con eventos concentrados en un mes va a seguir dando saltos grandes
  cuando ese mes salga de la ventana. La diferencia es que ahora el salto se ve
  en el gráfico en lugar de aparecer como una discrepancia entre el gráfico y el
  titular.
