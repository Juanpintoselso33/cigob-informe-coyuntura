---
madr: 4
id: '0071'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [costo_financiamiento_tesoro]
relacionado: ['0019', '0021', '0022', '0074']
ambito: 'Cinturón macro · ITCM · dimensión Financiamiento · `costo_financiamiento_tesoro` (nuevo)'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 3'
---

# ADR-0071 — costo_financiamiento_tesoro: el precio del financiamiento soberano entra al ITCM

## Contexto y planteo del problema

La auditoría marcó un hueco de consistencia: **la dimensión se llamaba
"Capacidad de financiamiento" y no incluía el precio del financiamiento
soberano**. Reservas, IdC y crédito privado miden *cuánta* financiación hay y
en qué condiciones se fondea el sistema, pero ninguno dice **cuánto le cuesta
al Estado refinanciarse**, que es exactamente la diferencia entre un programa
sostenible y uno que se agota.

La auditoría recomendaba incorporar el **riesgo país (EMBI)**. Se descartó por
tres razones:

1. **Rompe la validación externa.** El ITCM se valida contra el riesgo país
   (r = −0,726, n=31) y el texto publicado dice explícitamente que el EMBI *"no
   integra el índice"*. Meterlo adentro vuelve circular la única prueba
   independiente de que el índice no es autorreferencial.
2. **La fuente no es oficial.** El EMBI se toma de una API comunitaria y en el
   código está envuelto en un `try/except` que degrada a "no disponible". Sirve
   para validar; no para puntuar bajo los gates de frescura.
3. **Es político antes que macro.** La propia conclusión publicada del ITCM
   dice que los saltos mensuales del riesgo país *"co-mueven con la
   reconstrucción del cinturón político, no con ésta"*.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Se incorpora **`costo_financiamiento_tesoro`**: la **tasa real ex-ante** que
paga el Tesoro por colocar deuda en pesos en el mercado local.

- **Numerador**: TIREA (tasa efectiva anual) implícita de cada colocación,
  calculada desde el precio de corte, la fecha de vencimiento y la forma de
  pago del instrumento; promediada por mes ponderando por monto adjudicado.
- **Universo**: solo instrumentos **a tasa fija en pesos** (capitalizables y a
  descuento). Quedan afuera CER, dólar linked y tasa variable: su rendimiento
  no es comparable con el de una tasa fija, y promediarlos era el problema de
  agregación que hacía inviable la primera versión de esta idea.
- **Deflactor**: inflación esperada a 12 meses del REM.
- **Fuente**: planillas anuales de colocaciones de la Secretaría de Finanzas
  (oficial, con historia desde 2020) + BCRA. Los nombres de archivo no son
  estables, así que se resuelven leyendo los enlaces de la página.

### Escala de U invertida

Es **la única banda no monótona del ITCM**. Los dos extremos son malos:

| tasa real | puntaje | lectura |
|---|---|---|
| ≤ −5% | 20 | represión: el Estado se financia licuando al ahorrista |
| −5 – 0% | 55 | represión leve |
| 0 – 6% | 100 | mercado normal y sostenible |
| 6 – 12% | 75 | caro pero manejable |
| 12 – 20% | 45 | tensión de refinanciamiento |
| > 20% | 15 | bola de nieve: la deuda crece más rápido que la economía |

El motor de interpolación (ADR-0021) es agnóstico a la monotonía —convierte
bandas en anclas, las ordena e interpola—, así que la U invertida no exigió
tocar `parametrica.py`. Anclas resultantes: (−5, 20) · (−2,5, 55) · (3, 100) ·
(9, 75) · (16, 45) · (20, 15).

Es la misma filosofía que la auditoría reclama para el TCRM: distinguir el
nivel bueno alcanzado por las buenas del alcanzado por las malas.

### Ponderación

La dimensión pasa a llamarse **"Capacidad y costo del financiamiento"** —el
nombre viejo prometía lo que no medía— y queda:

| componente | antes | ahora |
|---|---|---|
| reservas_bcra | 45% | 34% |
| idc | 40% | 30% |
| **costo_financiamiento_tesoro** | — | **25%** |
| credito_privado | 15% | 11% |

El nuevo indicador toma 25% y **los otros tres se recortan en proporción**
(× 0,75). Deliberadamente **no** se aprovechó para bajar el IdC ni subir el
crédito: ese rebalanceo es otra recomendación de la auditoría y se decide
aparte, para no mezclar dos decisiones en un mismo cambio. Peso efectivo del
nuevo indicador: 4,0% del ITCM.

### Consecuencias

- ITCM 57,2 → **58,5**; tensión 4,3 → **4,2**. La dimensión de financiamiento
  sube de 45,2 a **53,6**: antes leía "financiamiento débil" sin ver que el
  Tesoro hoy se financia a tasa real sana (+8,1%).
- Serie de **29 puntos desde dic-2023**. Enero y febrero de 2024 no tienen dato
  (todo lo emitido fue CER) y se declaran como faltantes: no se imputa.
- El indicador **no lleva polaridad** en el gráfico. Pintar medio gráfico de
  verde y medio de rojo afirmaría que "más es mejor", que es lo contrario de lo
  que mide.
- Se publica en **TIREA, no en TNA**. A tasas altas divergen mucho (dic-2023:
  105% nominal contra 169% efectiva) y un lector que compare contra un diario
  necesita saberlo; queda declarado en la ficha.
- El riesgo país **sigue afuera del índice y sigue siendo el validador
  externo**, sin cambios.

## Más información

### Precedentes directos

ADR-0022 (crédito privado real y composición 45/40/15 de la dimensión) · ADR-0021 (puntaje interpolado entre anclas) · ADR-0019 (validación externa del ITCM contra el riesgo país)

### Validación contra prensa contemporánea

Se verificaron los dos extremos de la serie reconstruida contra la cobertura
de esos días:

**dic-2023 — TIREA 174,7%, tasa real −12,2% → puntaje 20 ("licuación")**

La primera licitación de la gestión colocó la LEDE S18E4 a TEM 8,66%. La
prensa: *"animosidad licuatoria del equipo económico"* (El Cronista); *"muy
por debajo de la inflación esperada"* (El Ágora, en una nota titulada
"Licuando los pesos"); *"con una tasa real tan negativa…"* (Infobae). El
nombre de la banda coincide con la palabra que usaba la prensa. La aritmética
cierra: TEM 8,66% compuesta da TIREA 168,8% contra los 174,7% calculados (la
diferencia son los días exactos al vencimiento).

**ago-2025 — TIREA 61,4%, tasa real +33,5% → puntaje 15 ("bola de nieve")**

*"Tasas récord de hasta 69,2% anual"* (BAE), *"una tasa que duplica la
inflación"* (Perfil), *"las mega tasas… son insostenibles en el tiempo"* (El
Economista), con rollover del 61% y *"el peor resultado del año"*. El promedio
ponderado de 61,4% es consistente con un máximo de 69,2% en el tramo corto.
La trayectoria coincide con la medición de Equilibra sobre las TEM de las
Lecap cortas (2,7% jun → 3,3% jul → 3,9% ago).

### Alternativas descartadas

- **Riesgo país como componente** — las tres razones del contexto.
- **Spread del Tesoro contra BADLAR/TAMAR** — se implementó y se midió: oscila
  entre −43 y +36 pp sin tendencia, porque cada mes el Tesoro coloca a plazos
  distintos y el promedio mezcla puntos de la curva contra una tasa bancaria a
  30 días. No es señal.
- **Tasa nominal sin deflactar** — las anclas quedarían obsoletas con cada
  cambio de régimen inflacionario.
- **Rollover (% de vencimientos renovados)** — cae en la misma trampa que la
  recaudación: un Tesoro con superávit puede decidir *no* renovar y cancelar
  deuda, y eso puntuaría como fracaso siendo fortaleza.
