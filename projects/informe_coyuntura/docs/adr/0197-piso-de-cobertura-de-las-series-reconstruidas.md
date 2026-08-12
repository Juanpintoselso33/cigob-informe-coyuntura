---
madr: 4
id: '0197'
estado: 'aceptado'
fecha: 2026-08-12
cinturon: 'transversal'
parametros: ['PISO_COBERTURA']
archivos: ['scripts/validacion_externa.py', 'tests/test_piso_cobertura.py']
relacionado: ['0031', '0082', '0106']
ambito: 'Series mensuales reconstruidas de ITCM/ITCG/ITCP y las correlaciones de validación externa que se publican en el snapshot'
origen: 'Al medir qué paramétricas admitirían una lectura anticipada del mes, apareció que el ITCG ya venía publicando una sin declararla'
---

# ADR-0197 — Una serie reconstruida no publica meses armados sobre una fracción del índice

## Contexto y planteo del problema

`validacion_externa.py` reconstruye la serie mensual de cada paramétrica desde
las series de sus componentes y la correlaciona contra un par externo (Merval
para el ITCG, EPU para el ITCP, índice líder para el ITCM). Esas correlaciones
se publican: `publicar.py` las incrusta en el snapshot y salen en la web.

El motor renormaliza pesos ante faltantes (ADR-0082), que es lo correcto para el
índice de un mes: si un indicador no llegó, su peso se reparte entre los
presentes. Aplicado a la **cola** de una serie histórica, sin embargo, eso deja
de ser renormalizar. Un mes donde llegó el 30% del índice no es "el índice con
ruido": es el índice de esos pocos componentes, publicado con el nombre del
índice completo y metido en un Pearson donde pesa exactamente igual que un mes
completo.

### Cómo apareció

Midiendo cuánta cobertura tendría una lectura anticipada del mes en curso para
cada paramétrica. El ITCG resultó tener una ya publicada:

| mes | índice publicado | cobertura del peso |
|---|---|---|
| 2026-05 | 73,9 | 84,5% |
| 2026-06 | 81,8 | 84,5% |
| **2026-07** | **73,2** | **44,8%** |
| **2026-08** | **65,2** | **29,2%** |

Mediana histórica de la serie: 94%. Los dos meses de la cola **entraban a la
correlación contra el Merval**.

Y el faltante no es aleatorio. Los componentes que se demoran son
sistemáticamente los que puntúan alto: `apertura_comercial` (14% del índice),
`reduccion_estado` (10,9%), `gasto_funcionamiento` (7,8%). Recalculando
jun-2026 —cobertura plena, índice 81,8— con sólo los componentes que
sobrevivían en agosto da **66,9**, prácticamente el 65,2 que se publicaba como
agosto. La caída de 16 puntos era el calendario de publicación, no la gestión.

El ITCP ya tenía las dos defensas desde 2026-07-09, puestas tras un incidente
del mismo tipo (el mismo mes daba 55,0 en una corrida y 26,4 en la siguiente).
El ITCG no tenía ninguna, y nadie lo notó porque el arreglo se hizo como
parche local en vez de como criterio.

## Factores de decisión

- Ningún gate mira esto: `gate_calidad.py` valida estructura, frescura y
  card-contra-serie, y los tests de reconciliación miran el snapshot. Que un
  punto de una serie histórica esté armado sobre un tercio del índice no lo
  chequeaba nada.
- Una advertencia no sirve: el consumidor es una correlación, y dentro del r un
  punto con 30% de cobertura pesa lo mismo que uno con 94%. No hay nota al pie
  que corrija eso.
- El sesgo tiene dirección conocida, así que el error no se promedia: empuja el
  índice hacia abajo justo en los meses más recientes, que son los que se leen.
- Tener dos definiciones de "cobertura" en el mismo archivo era parte del
  problema.

## Opciones consideradas

- **A. Piso de cobertura medido por peso de indicador, más tope de mes en
  curso, unificado para las tres series.**
- **B. Copiar el piso del ITCP tal cual** (medido por dimensión) al ITCG.
- **C. Publicar el mes igual, con la cobertura declarada** al lado.
- **D. Imputar los componentes faltantes** (carry-forward u otro método) para
  completar el mes.

## Decisión

**Opción A.** Un solo helper `_serie_con_piso()` que usan las tres
reconstrucciones, con `PISO_COBERTURA = 0.60`:

- **La cobertura se mide por peso de indicador**, no por dimensión. El criterio
  dimensional del ITCP no servía acá: como el motor renormaliza *dentro* de cada
  dimensión, una dimensión con un indicador vivo de cinco aporta su peso entero
  y da 100%. El ITCG de jul-2026 medía 100% dimensional y 44,8% de peso real.
- **El mes en curso no entra** en ITCG e ITCP. En ITCM no hace falta: sus
  fuentes (INDEC, BCRA mensual, Hacienda) publican por mes cerrado.

Efecto medido: recorta exactamente **jul-2026 y ago-2026 del ITCG**. El ITCM
(mínimo histórico 73,4%) y el ITCP (66,8%) quedan intactos — el piso les queda
como red, no como recorte.

### Consecuencias

- La correlación ITCG↔Merval se calcula sobre meses comparables entre sí.
- La serie del ITCG termina un mes antes que hoy. Es correcto: ese mes no
  existía todavía como medición del índice.
- El ITCP pasa a un piso estrictamente más estricto sin perder ningún mes.
- Queda un solo criterio de cobertura en el archivo, con nombre y test.

### Confirmación

- `tests/test_piso_cobertura.py` (9 tests): la aritmética de la cobertura, que
  el piso recorte, que el mes en curso no entre, y —recorriendo las tres series
  reales— que ningún mes publicado quede por debajo del piso.
- Un test fija además que el faltante del ITCG está **sesgado hacia abajo**, que
  es lo que hace insuficiente publicar con advertencia.

## Pros y contras de las opciones

- **A. Piso por peso + tope, unificado.** Bueno: corrige el caso real, deja un
  solo criterio y protege a las otras dos series antes de que les pase. Malo: la
  serie del ITCG pierde su punto más reciente, que es el que más se quiere ver.
- **B. Copiar el piso del ITCP.** Bueno: cambio mínimo. Malo: **no arregla
  nada** — jul-2026 pasa el filtro dimensional con 100%. Se descartó porque se
  midió antes de aplicarlo.
- **C. Publicar con la cobertura declarada.** Bueno: no se pierde información y
  el lector decide. Malo: el consumidor es un coeficiente de correlación, que no
  lee declaraciones. Sirve como complemento, no como reemplazo.
- **D. Imputar los faltantes.** Bueno: serie completa hasta hoy. Malo: inventa
  el dato justo donde más sesgo hay, y lo publica como medición. Es la opción
  que hace parecer que el problema no existe.

## Más información

- ADR-0082 — la renormalización ante faltantes, correcta para el mes y no para
  la cola de la serie.
- ADR-0106 — la línea base del ITCM ya publicaba su cobertura declarada; este
  ADR extiende esa doctrina de un punto a la serie entera.
- ADR-0031 — el par de validación del ITCG (Merval en dólares), que es el
  consumidor afectado.
- Medición lateral, del mismo día: el ITCP tiene el 70,7% de su peso con datos
  más frescos que el corte de su serie, así que **sí** admitiría una lectura
  anticipada declarada del mes en curso. El ITCM tiene el 16,2%, así que no.
  Publicar esa lectura es una decisión de producto y no se toma acá.
