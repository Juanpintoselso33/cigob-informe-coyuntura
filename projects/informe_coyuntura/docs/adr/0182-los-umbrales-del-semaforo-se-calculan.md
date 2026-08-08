---
madr: 4
id: '0182'
estado: 'aceptado'
fecha: 2026-08-08
cinturon: 'transversal'
indice: 'todos'
archivos: ['scripts/parametrica.py']
continua: ['0181']
ambito: 'Umbrales del semáforo en la unidad cruda del indicador · interpolación inversa'
origen: 'Las 15 fichas de Gestión traen los umbrales escritos en prosa, y los números con los que se escribieron envejecieron en una semana'
---

# ADR-0182 — Los umbrales del semáforo se calculan, no se escriben

## Contexto y planteo del problema

ADR-0181 fija los cortes de color en la tensión. Falta la otra mitad de lo que
pidió CIGOB: que la ficha pública muestre **en qué valor concreto del indicador
cambia el color**, en la unidad que el lector ve en la card —km adjudicados,
artículos derogados, centavos por dólar, % de avance— y no en puntaje.

Los documentos entregados resuelven eso escribiendo la tabla a mano en cada
ficha. Se escribieron contra la corrida del 31 de julio de 2026 y **una semana
después ya estaban desactualizadas**: RIGI decía 24,6% de cartera cuando el
valor vigente es 31,6%, y el ITCG total decía 78,22 cuando es 79,4.

Eso no es un descuido de quien las escribió: es lo que le pasa a cualquier
número copiado a prosa en un informe que se regenera todas las noches. Y
envejece **en silencio**, porque nada del pipeline lee un `.docx`: ningún gate,
ningún test y ninguna corrida se enteran de que la ficha dejó de coincidir con
el dato.

## Factores de decisión

- El umbral tiene que estar en la **unidad cruda** del indicador, la misma que
  muestra la card. Un umbral en puntaje 0-100 no le sirve a nadie que esté
  mirando "2.614 de 9.091 km adjudicados".
- Esa información **ya existe**: la tabla de bandas de cada indicador es
  exactamente la función que convierte unidad cruda en puntaje. El umbral es su
  interpolación inversa, no un dato nuevo que haya que producir.
- Algunas escalas **no son monótonas**: el óptimo está en el medio y cada corte
  se cruza dos veces.
- Algunos indicadores declaran una **transformación** antes de puntuar, y la
  card muestra la unidad de antes de transformar.
- Algunos indicadores **no tienen tabla de bandas** y aun así tienen que
  recibir color.
- La prosa que explica el color en la ficha tiene que salir de la **misma
  aritmética** que produjo el color. Si se escribe aparte, se desincroniza.

## Opciones consideradas

- **Escribir los umbrales en la ficha**, como hacen los documentos entregados
  — descartada.
- **Publicar el umbral en puntaje 0-100** y dejar que el lector traduzca —
  descartada: es justamente la traducción que la ficha tiene que hacer, y es la
  única parte que el lector no puede hacer solo.
- **Calcularlos por interpolación inversa de las anclas** — elegida.

## Decisión

`parametrica.umbrales_en_unidad(indicador, escala)` interpola las anclas del
indicador **hacia atrás** en los puntajes de corte 60, 40 y 20 —los mismos de
ADR-0181— y devuelve los tramos en la unidad cruda:

```json
[{"color": "verde", "desde": null, "hasta": 6.0},
 {"color": "amarillo", "desde": 6.0, "hasta": 9.0}, ...]
```

Cuatro cosas que la implementación tiene que hacer bien, y que son la razón de
que esto sea una función y no una tabla:

1. **Es una lista de tramos, no un mapa por color.** Un color puede aparecer
   más de una vez (ver el caso no monótono abajo). Un `desde`/`hasta` en `null`
   es extremo abierto. La ficha renderiza la lista tal cual, así que soportar
   el caso raro no le cuesta nada a la web.
2. **Aplica la inversa de la transformación declarada**, el mismo camino que ya
   usa `span_crudo`. Las bandas de `rem_ipc_12m` están escritas en equivalente
   **mensual**, pero la card muestra la expectativa **anual**: sin la inversa,
   su corte de verde se publicaría como **2,80%** al lado de un valor de 22,3%,
   cuando en la unidad de la card ese mismo corte es **39,29%**.
3. **Fusiona tramos contiguos del mismo color.** Cuando un corte coincide con
   un ancla exacta, el valor cae en el borde de dos segmentos y los dos lo
   reportan (`apertura_comercial` devuelve `9 / 9` para el corte de 40).
4. **Devuelve `None` cuando no hay tabla de bandas.** Vida cotidiana y espíritu
   de época no tienen anclas: sus componentes son base-100 o fórmulas 0-10
   directas. Reciben color igual, y la ficha **omite** la sección de umbrales
   en vez de mostrar una tabla vacía o inventada.

La frase que explica el color (`semaforo.por_que`) se genera en `publicar.py`
con la misma aritmética que produjo el color y la misma convención de
membresía de tramo (low-exclusivo / high-inclusivo, la del motor). No se
escribe a mano por la misma razón que los umbrales no se escriben a mano.

### Consecuencias

- **La ficha no puede envejecer respecto del dato.** El umbral y el valor salen
  de la misma corrida; si cambia la tabla de bandas, la ficha cambia con ella
  sin que nadie tenga que acordarse.
- **La tabla de umbrales del ITCG que traen las fichas deja de ser la fuente.**
  Sigue siendo útil como control cruzado —y de hecho sirvió para descubrir que
  las fichas cortaban en 65/45/25—, pero lo que se publica es lo calculado.
- **Aparece una guarda explícita que hoy no se ejercita.** Si la inversa de una
  transformación fuera decreciente invertiría el orden `desde`/`hasta` de cada
  tramo. La única transformación declarada hoy (`rem_ipc_12m`) es creciente,
  así que reordenar en silencio dejaría en producción una rama sin ningún test
  que la pise. La función **falla fuerte** con un `ValueError` en vez de
  arreglarlo sola: el día que aparezca una inversa decreciente hay que sumarle
  soporte explícito y su test.
- **Un hallazgo de la revisión, que vale anotar por la forma que tuvo.** La
  tensión publicada de vida cotidiana se re-derivó a mano con la fórmula
  `5 − (índice−100) × 0,2` en vez de reusar `itvc.tension_de_itvc()`, que ya
  acota a `[0, 10]`. Resultado: **seis componentes del ITVC con la tensión
  fuera de su dominio documentado** (`mora_familias` 21,6, `alquiler_real` 12,1,
  `peso_tarifas` 10,7, `pobreza_nowcast` −0,4, `sentimiento_digital` −2,5,
  `patentamiento_motos` −3,0). **Ningún color cambiaba**, porque los cuatro
  cortes caen dentro de `[0, 10]`, así que ningún test de color podía detectarlo.
  Volver a derivar un número que ya tiene función es la manera de producir un
  defecto que no se ve. El color sigue saliendo de la tensión **cruda**, sin
  acotar, vía `color_de_indice_base100`: eso no cambió.

### Confirmación

- **Reversibilidad sobre las 57 tablas** de los tres índices —15 del ITCG, 17
  del ITCM y 25 del ITCP, incluidas las bandas que el ITCP conserva como
  referencia histórica—: `puntaje_de(umbral_verde) == 60,0` con tolerancia de
  redondeo. Es el test que detecta un error de interpolación inversa sin
  depender de valores pineados, y recorrer las tablas en vez del snapshot lo
  hace independiente de qué indicadores estén en el índice ese día.
- El no monótono `costo_financiamiento_tesoro` devuelve **seis** tramos, con
  verde como intervalo cerrado.
- `rem_ipc_12m` devuelve el umbral en unidad cruda (anual), no en la
  transformada.
- Ningún tramo repetido cuando el corte cae sobre un ancla.
- El valor vigente de cada indicador cae dentro de algún tramo publicado.
- Una tensión publicada fuera de `[0, 10]` falla (`TestTensionEnDominio`).

## Pros y contras de las opciones

**Escribir los umbrales en la ficha**

- Bueno: es lo que los documentos ya traen; cero trabajo de implementación.
- Bueno: permite redacción libre por indicador, con matices que una función no
  puede expresar.
- Malo: envejece con el dato, en silencio y sin gate posible. Ya pasó: las
  fichas de agosto duraron una semana.
- Malo: 57 tablas escritas a mano son 57 lugares donde una recalibración de
  bandas tiene que replicarse.

**Publicar el umbral en puntaje 0-100**

- Bueno: trivial de calcular y siempre correcto.
- Malo: no responde la pregunta que la ficha existe para responder. "El corte
  de verde está en 60 puntos" no le dice a nadie cuántos km hay que adjudicar.

**Calcular por interpolación inversa** — elegida

- Bueno: el umbral y el valor salen siempre de la misma corrida.
- Bueno: no hay dato nuevo que recolectar; la información ya estaba en las
  bandas.
- Bueno: soporta el caso no monótono sin ninguna excepción en la web.
- Malo: agrega una función con aritmética delicada —cruces, deduplicación,
  inversas— que hay que testear en serio; el test de reversibilidad sobre las
  57 tablas existe por eso.
- Malo: no cubre los indicadores sin anclas, que quedan con color pero sin
  tabla.

## Más información

### El caso no monótono, completo

`costo_financiamiento_tesoro` (ITCM) mide la tasa real del Tesoro y su óptimo
está **en el medio**: muy baja es financiamiento reprimido, muy alta es costo
insostenible. Sus anclas son
`[(−5, 20), (−2,5, 55), (3, 100), (9, 75), (16, 45), (20, 15)]`, así que cada
corte se cruza **dos veces** y el mapa real es este:

| | naranja | amarillo | **verde** | amarillo | naranja | rojo |
|---|---|---|---|---|---|---|
| desde | −∞ | −3,57 | **−1,89** | 12,50 | 16,67 | 19,33 |

Verde es un **intervalo cerrado** (−1,89 a 12,50), no un `≥` ni un `≤`; los que
quedan partidos en dos son amarillo y naranja. **Del lado izquierdo nunca hay
rojo**: por debajo de −5 el puntaje satura en 20 y el color se queda en naranja.
Es el único indicador así hoy, y la función lo soporta en general porque nada
impide que aparezca otro.

### La trampa del redondeo

`aporte_score` se publica **redondeado a un decimal**. Usarlo como insumo del
color rompe el borde: un puntaje de 59,9 da tensión 4,01, que redondeada es 4,0,
que es verde — cuando 59,9 tiene que ser amarillo. El color se calcula siempre
sobre la tensión **sin redondear**; `aporte_score` sigue publicándose redondeado
para lectura, pero no es el insumo del color. El caso 59,9 tiene test propio
(`test_no_usa_la_tension_redondeada`), y existe precisamente porque es el error
que alguien va a volver a cometer leyendo el snapshot en vez del puntaje.

Por eso `publicar._semaforos` recalcula la tensión desde el dato **más crudo
disponible** en cada rama: el puntaje 0-100 del indicador para ITCM/ITCG/ITCP,
el `indice_itvc` base-100 para vida cotidiana, y sólo para espíritu de época
—donde no hay otro dato— el propio `aporte_score`.

### Los indicadores sin tabla

Vida cotidiana y espíritu de época reciben color y **no** reciben tabla de
umbrales. No es una carencia que haya que tapar: sus componentes no puntúan por
bandas, así que no hay ningún valor en unidad cruda donde el color cambie. Lo
que sí hay que evitar es lo contrario —una tabla vacía o inventada—, que es
peor que la ausencia porque parece un dato.

**Pendiente declarado, no resuelto.** El diseño pedía que la ficha *dijera* que
este indicador no tiene umbrales en unidad propia y por qué. Lo implementado
hoy es más silencioso: `pages/metodologia/[id].astro` renderiza la sección sólo
si `semaforo.umbrales` existe, así que en esos indicadores la sección
sencillamente no aparece. Funcionalmente no engaña —no hay tabla falsa— pero un
lector que compare dos fichas ve una diferencia sin explicación. Falta una nota
de una línea en la rama negativa.
