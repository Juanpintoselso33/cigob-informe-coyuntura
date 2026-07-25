# ADR-0127 — La recaudación mide la base imponible, no la caja: pasa a DGI

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITCM · `recaudacion` · serie · card · `resultado_primario` (denominador) |
| **Fecha** | 2026-07-25 |
| **Modifica** | ADR-0003 (recaudación interanual real), ADR-0072 (reinterpretación del indicador) |
| **Origen** | Planteo del editor |

## El planteo

> "El indicador de la recaudación te dice si recauda más o menos en términos
> reales, pero si la política es bajar impuestos, se estaría castigando la baja
> de recaudación."

Es correcto, y el dato lo confirma. Deflactando por IPC, 2026:

| mes | TOTAL | DGI | **DGA (aduana)** |
|---|---|---|---|
| ene | −7,9% | −0,0% | **−31,1%** |
| feb | −9,8% | −0,1% | **−37,5%** |
| mar | −4,8% | −0,6% | **−17,4%** |
| abr | −3,9% | +0,9% | **−15,3%** |
| may | +1,8% | +12,8% | **−25,6%** |
| jun | −7,4% | −3,8% | **−21,8%** |

**El total cae ~5% real promedio; la base doméstica sube ~1,5%. Toda la caída
es aduana**, donde impactan los recortes de retenciones y derechos de
exportación. El índice estaba leyendo como deterioro económico el cumplimiento
de una promesa de gobierno.

ADR-0072 ya había reinterpretado el indicador como medida de **actividad y
formalidad de la base imponible** —no de viabilidad fiscal, que pasó al
resultado primario— y le bajó el peso de 60% a 30%. Este ADR termina ese
movimiento: si el indicador mide la base imponible, tiene que medir la base
imponible.

## Lo que se descartó

**El ratio recaudación/gasto**, que era la propuesta original del editor. Es
prácticamente una transformación monótona del resultado primario
(`recaudación/gasto ≈ 1 + resultado/gasto`), y **`resultado_primario` ya lidera
la misma dimensión con el 50%**. Habría medido dos veces lo mismo y eliminado
la única señal de base imponible del ITCM.

**Medir a legislación constante** sería lo correcto en teoría y exige modelar
cada cambio de alícuota, mínimo y régimen. No es reproducible de forma
automática y quedaría colgado del criterio de quien lo arme.

## Decisión

`recaudacion` pasa a medir la **recaudación DGI** —IVA doméstico, Ganancias,
créditos y débitos, internos— en variación interanual real, promedio móvil 3
meses (la construcción de ADR-0029 no cambia).

La apertura oficial es exacta y se verificó: **DGI + DGA + Seguridad Social =
total**, al peso.

La card publica el total y la aduana en la misma métrica, como contexto. La
brecha entre DGI y total *es* el efecto de la política tributaria sobre el
comercio exterior, y mostrarla es lo que evita que el cambio de serie parezca
un recorte conveniente.

## Las bandas NO se tocaron

La unidad sigue siendo variación real interanual y el cero sigue siendo el
punto con significado. Recalibrarlas al cambiar de fuente habría sido
indistinguible de mover el número (ADR-0045).

Chequeadas contra la distribución pre-mandato de la serie nueva (2021-2023,
n=35): mediana +4,5%, cortes en p0 / p14 / p57 / p80. Sirven.

## Por qué esto no es acomodar el número

Es la objeción obvia —cambiar la serie justo donde el total da mal— y el dato
la contesta. Con las mismas bandas, el puntaje de la DGI contra el del total:

| mes | Δ puntos |
|---|---|
| jul-2025 | **−19,6** |
| ago-2025 | **−45,5** |
| sep-2025 | **−31,4** |
| oct-2025 | −1,4 |
| nov-2025 | 0,0 |
| dic-2025 | +23,0 |
| feb-2026 | +44,3 |
| abr-2026 | +40,3 |
| jun-2026 | +31,1 |

**Durante casi todo 2025 la DGI habría puntuado mucho PEOR que el total** —
hasta 45 puntos. El cambio no favorece sistemáticamente a nadie: mide otra
cosa, y esa otra cosa a veces es peor y a veces mejor.

## El bug que casi se cuela

`INDEC_RECAUDACION_ID` no lo usaba sólo el indicador: **`resultado_primario` lo
usaba como DENOMINADOR** ("% de la recaudación"). Apuntar la constante a la DGI
habría cambiado en silencio la escala del resultado primario, midiéndolo contra
una base ~40% más chica.

Es la misma familia de error que ADR-0097 dejó en `fetch_reduccion_serie`: un
productor cambia y un consumidor que compartía la referencia se rompe sin que
nada avise. `resultado_primario` pasa a apuntar explícitamente a
`INDEC_RECAUDACION_TOTAL_ID`, con el comentario que explica por qué.

## Limitaciones declaradas

- **Excluir la aduana resuelve el caso más grande, no todos.** La propia DGI
  contiene impuestos cuyas alícuotas y mínimos cambiaron en el período: el
  indicador tampoco es neutral respecto de las decisiones del Gobierno.
- **La seguridad social también es base imponible doméstica y queda afuera.**
  Sigue su propia dinámica —cae en términos reales desde fines de 2025, señal
  del mercado laboral registrado— y mezclarla habría metido empleo en un
  indicador de actividad y formalidad. Vale la pena mirarla aparte.
- **La banda inferior no tiene respaldo en la muestra pre-mandato**: la DGI
  nunca cayó más de 5% real en 2021-2023. Describe una situación posible, no
  una observada.
- Deflactor único (IPC nacional), con el riesgo sistémico que declara ADR-0122.
