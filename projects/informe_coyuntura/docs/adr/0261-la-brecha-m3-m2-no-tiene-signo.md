---
madr: 4
id: '0261'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [idm]
archivos: ['scripts/itcm.py', 'tests/test_idm_e_icip_no_puntuan.py', 'tests/test_itcm.py', 'tests/test_constructos_no_prometen_de_mas.py']
relacionado: ['0009', '0045', '0192', '0193', '0254', '0257', '0264', '0265']
ambito: 'Cinturón macro · ITCM · `idm` · la deuda que ADR-0254 dejó escrita: la banda quedó calibrada bajo una lectura que el propio ADR dio por muerta'
origen: 'Reauditoría externa post-cambios, 25-ago-2026: «las bandas siguen castigando automáticamente una brecha positiva como si probara exceso de pesos»'
---

# ADR-0261 — La brecha M3–M2 no tiene signo, así que no puntúa

## Contexto y planteo del problema

ADR-0254 le sacó a `idm` el nombre que no le correspondía —«Exceso de pesos
sobre la demanda»— y dejó la deuda anotada en su propio texto: *«la banda del
indicador se calibró leyendo la brecha como exceso monetario —"&gt;5 → 10"
castiga fuerte el positivo—. Esa lectura sigue siendo defendible por otra vía
(los pesos yéndose de las transacciones), pero la calibración merece
revisarse»*.

La reauditoría del 25 de agosto volvió sobre eso y lo llamó discrepancia: el
número y el rótulo están bien, pero **el indicador tal como entra al ITCM no**.
Su recomendación fue explícita: *«retirar temporalmente del índice o recalibrar
signo y anclas contra episodios/outcomes observables»*.

Se intentó lo segundo. Este ADR documenta que no se pudo, y por qué eso decide
lo primero.

### Lo que la banda afirma hoy

Anclas vigentes: `−2 → 100 · 0 → 85 · 3,5 → 60 · 6,5 → 35 · 8 → 10`. Dicho en
castellano, afirma dos cosas separables:

1. **una dirección** — cuanto más positiva la brecha, más tensión;
2. **un nivel** — una brecha de −2 pp o menos es un **100**, la perfección, y
   una brecha de 0 pp ya vale 85.

La segunda sólo se sostenía con la lectura muerta: si el positivo era «sobran
pesos», el negativo era «no sobran» y por lo tanto óptimo. Sobre 33 meses de
serie, **12 puntúan exactamente 100** y los doce son de la era del cepo.

### Cuatro mediciones

**1. La tesis original no está en el dato.** «Sobran pesos → presión sobre
precios» se contrasta con el IPC y no aparece: `r = 0,075` contemporáneo,
`0,009` a un mes, `0,067` a tres, sobre 30-33 meses. No es débil, es nada.

**2. Ninguna referencia externa firma la dirección.** Las mismas tres que usó
ADR-0257, más el IPC, el TCRM y las reservas netas:

| referencia | r (niveles) | ¿apoya la dirección de la banda? |
|---|---:|---|
| EPU, incertidumbre (↑ = peor) | +0,257 | sí, no significativo |
| índice líder (↑ = mejor) | −0,235 | sí, no significativo |
| Merval en dólares (↑ = mejor) | +0,224 | **no** |
| TCRM (↑ = mejor) | **+0,384** * | **no** |
| reservas netas (↑ = mejor) | **+0,501** * | **no** |
| IPC m/m (↑ = peor) | +0,075 | ninguna señal |

Los **dos únicos coeficientes significativos del panel completo apuntan al
revés** que la banda. En primeras diferencias todo se derrumba a ruido salvo el
TCRM (+0,406 *), que sigue apuntando al revés. Y en la submuestra del régimen
abierto (n=16) se da vuelta otra vez: ahí sí aparecen el índice líder (−0,661 *)
y el IPC a un mes (+0,652 *) apoyando la dirección. Seis referencias, tres
especificaciones, signos que cambian según cuál se mire. **El dato no puede
firmarla.**

**3. La banda mezcla dos regímenes monetarios.** Es el mismo defecto que
ADR-0257 encontró en el componente A del indicador vecino. Los cortes (2, 5, 8
pp) se leyeron sobre una historia donde el lado negativo es **entero** de la era
del cepo, y **desde la apertura la brecha fue positiva los 14 meses**, entre
+2,85 y +7,13 pp. O sea: la mitad de la escala donde vive la perfección es
inalcanzable en el régimen vigente, y el indicador quedó clavado entre 24,5 y
64,6 puntos por un cambio de régimen, no por el estado de la economía.

Acá el arreglo de ADR-0257 **no transfiere**. Aquella banda es posicional por
diseño y se re-ventaneó; ésta es una banda de valores, y recalibrarla contra 14
meses en un rango de 4,3 pp sería declarar que el mejor de los últimos catorce
meses vale 100 — amplificar ruido y llamarlo escala.

**4. Lo que queda ya está en el índice, medido mejor.** `idm` es la variación
interanual real del cociente entre el M2 privado transaccional (var. 197 del
BCRA) y el M3 privado (var. 17 + var. 100). El **componente A** de
`desequilibrio_monetario` es el **nivel** de ese mismo cociente, con las mismas
tres variables, más los depósitos privados en dólares (var. 104) en el
denominador. Están en la misma dimensión y pesaban 20% cada uno.

Y no es una coincidencia: la cabecera de `desequilibrio_monetario.py` dice que
ese indicador **nace de una observación sobre el IDM** —*«M2 y M3 son agregados
de OFERTA y no dicen con claridad cuánta confianza hay en el peso»*—. El
proyecto ya había decidido que esta comparación no mide lo que se le pedía, y
construyó el reemplazo. Lo que faltaba era retirar al reemplazado.

> La matriz de redundancia no lo marca (r = 0,311) y **no la contradice**:
> compara un nivel con una tasa de variación, que es justo el par que una
> correlación contemporánea de puntajes no ve. El argumento acá es definicional,
> no estadístico.

## Factores de decisión

- **Una dirección que no se puede firmar no se codifica.** Es la regla que
  ADR-0257 aplicó a las esquinas de la matriz y vale igual acá.
- **El dato es informativo aunque el puntaje no lo sea.** Retirar el contrato
  con el score no es borrar la serie.
- **No inventarle un fundamento nuevo a un número ya escrito** (ADR-0257).
- **Comparabilidad hacia atrás**: la fórmula del colector no se toca.

## Opciones consideradas

- **A — Dejar la banda como está** y anotar la deuda por segunda vez.
- **B — Cortes simétricos alrededor de cero**, conservando la dirección.
- **C — Banda neutra alrededor de cero** (U invertida: cualquier divergencia
  grande es tensión, venga del lado que venga).
- **D — Recalibrar contra el régimen abierto**, como ADR-0257 hizo con A.
- **E — Estimar una función de demanda de dinero** y medir el exceso de verdad.
- **F — Retirarlo del ITCM** y publicarlo como contexto.

## Decisión

**Opción F.** `idm` sale de `BANDAS_ITCM` y de `DIMENSIONES_ITCM`, y entra a
`INDICADORES_CONTEXTO`. Se sigue calculando, se sigue escribiendo en
`output/series/macro.csv` y se sigue archivando en BigQuery: **lo que se retira
es su contrato con el score, no el dato**.

El 20% que deja en `estabilidad_monetaria` **vuelve entero al IPC** (40 → 60), y
el REM y el desequilibrio monetario se quedan en 20% cada uno. No se renormaliza
en proporción, y esa parte la decidió una guarda vieja: ADR-0193 no fijó estos
pesos como proporciones sino contra un ancla **nominal** —el desequilibrio tenía
que pesar como las reservas, 5,2% contra 5,44%— y repartir el 20% en proporción
lo subía a 6,5%. La primera versión de esta entrega lo hizo, y
`test_el_desequilibrio_pesa_como_las_reservas_y_no_como_el_tcrm` la frenó. Sacar
un indicador no es una excusa para promover a otro.

### Consecuencias

- **El ITCM sube 1,2 puntos** con los valores del 25-ago-2026, de 64,8 a 66,0
  medido solo (65,3 junto con ADR-0262). `idm` puntuaba 50,0 contra 67,8 de su
  dimensión, así que retirarlo la levanta a 72,3. **La tensión publicada del
  cinturón no se mueve: 3,5 antes y 3,5 después.**
- **La serie histórica sigue viva y sigue siendo comparable**: la fórmula del
  colector no cambió ni una línea.
- **La dimensión queda con tres indicadores**, dos de inflación y la matriz de
  liquidez. Es su núcleo declarado desde ADR-0193.
- **`idm` DEJA DE PUBLICARSE COMO CARD.** No es un efecto colateral: es lo que
  «sale del score» significa en este proyecto. La regla —ADR-0153, reaplicada
  por ADR-0216— es que o integra el índice o no es card, sin categoría
  intermedia. Macro pasa de **17 a 16 cards** con este ADR (a 15 sumando
  ADR-0262) y el perímetro publicado de 65 a 63. **La serie no desaparece**:
  sigue en `output/series/macro.csv`, en `series.json` y en BigQuery, y sigue
  disponible para cualquier lectura que la quiera. Lo que desaparece del tablero
  es una card que mostraría un puntaje que ya no se puede defender.
- **La cañería que lo hace efectivo estaba rota y se arregla aparte.**
  `macro.py` deriva `en_indice` de `BANDAS_ITCM` y se acomoda solo, pero
  `MACRO_OCULTOS`, en `publicar.py`, era un literal hardcodeado —a diferencia de
  `POLITICA_OCULTOS` y `GESTION_OCULTOS`, que sí se construyen desde
  `INDICADORES_CONTEXTO`—. Con el literal, declarar un indicador como contexto en
  macro no ocultaba nada y la card volvía por el `else` de `publicar.py`: la
  misma vía por la que ADR-0153 y ADR-0216 tuvieron que aplicar la regla dos
  veces. `publicar.py` pasa a derivar `MACRO_OCULTOS` de
  `itcm.INDICADORES_CONTEXTO`, como los otros dos cinturones.

### Confirmación

`tests/test_idm_e_icip_no_puntuan.py`, más el ajuste de `test_itcm.py` y de
`test_constructos_no_prometen_de_mas.py`. Cinco mutaciones, cinco fallas:
devolverle la banda y el 20%; devolverle sólo la banda (retiro a medias, que es
el modo real de romperlo); repartir el 20% en proporción; y las dos de
ADR-0262.

Tres invariantes estructurales viajan con la guarda porque no las cuidaba nadie:
banda ⟺ dimensión, contexto sin banda, y el efecto numérico pineado contra un
fixture congelado del 25-ago-2026 —no contra el dato del día, para que la
corrida nocturna no lo mueva—.

## Pros y contras de las opciones

### A — Dejar la banda

- Bueno: no cambia nada publicado.
- Malo: es la segunda vez que se anota la misma deuda. Y sostiene una dirección
  cuyo único fundamento explícito ADR-0254 ya declaró inválido.

### B — Cortes simétricos, misma dirección

- Bueno: quita la asimetría, que es la huella más visible de la lectura muerta.
- Malo: **profundiza** la dirección que no se puede firmar. Medido: el mes
  publicado cae de 50,0 a 34,0 y la media del régimen abierto de 43,5 a 30,1.
  Además obliga a afirmar que una brecha de cero vale 55 —mediocre—, que es una
  afirmación nueva y de la nada.

### C — Banda neutra alrededor de cero

- Bueno: no firma la dirección, sólo la magnitud, y elimina la saturación
  (0 meses en 100 contra 12).
- Malo: firma otra cosa igual de fuerte y peor: que la remonetización de
  2024-2025 fue tensión. Medido: la media de la serie cae de 69,8 a 42,4 y los
  meses de −9 a −13 pp pasan de 100 a entre 10 y 35. Cambiar una afirmación sin
  fundamento por otra no es una corrección.

### D — Recalibrar contra el régimen abierto

- Bueno: es exactamente lo que ADR-0257 hizo con el componente A, y por la misma
  razón.
- Malo: no transfiere. A es posicional por diseño; `idm` es una banda de
  valores, y catorce meses en 4,3 pp no son una escala.

### E — Estimar una demanda de dinero

- Bueno: mediría el fenómeno que el nombre original prometía.
- Malo: ADR-0254 ya lo descartó y sigue valiendo — variables, forma funcional,
  período y validación. Es un indicador nuevo, no una recalibración.

### F — Retirarlo del ITCM *(elegida)*

- Bueno: no afirma nada que no se pueda sostener, no toca la fórmula ni la
  serie, y completa una sustitución que el propio proyecto empezó en ADR-0192.
- Malo: el ITCM pierde un componente y la dimensión queda con tres. Y arrastra
  una deuda de publicación (`MACRO_OCULTOS`) que hay que cerrar aparte.

## Más información

**Queda abierto y declarado.** La dirección no se puede firmar *con la muestra
que hay*: en el régimen abierto sólo hay 14-16 meses, y ahí dos referencias sí
la apoyan de forma significativa. Si con más muestra el signo se ordena de forma
estable, este es el primer indicador a revisar — y la guarda está escrita para
permitirlo: pide que no puntúe **hoy**, no que no pueda volver nunca.

- ADR-0254, que dejó la deuda: `0254-la-brecha-m3-m2-no-es-oferta-menos-demanda.md`
- ADR-0192, que construyó el reemplazo y dijo por qué.
- ADR-0257, de donde sale el método: medir, y si el dato no ordena, no ordenar.
- Reauditoría: `docs/auditoria_indicadores/260825_reauditoria_post_cambios_macro.md`, caso 11.
