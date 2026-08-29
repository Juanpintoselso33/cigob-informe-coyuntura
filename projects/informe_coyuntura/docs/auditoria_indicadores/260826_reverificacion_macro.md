# Reverificación post-remediación · Macroeconomía

**Fecha de corte:** 26 de agosto de 2026

**HEAD auditado:** `e1dfab84`

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25/08/2026 a las 21:39:35 (UTC−3)

**Cobertura:** 17/17 indicadores del perímetro de la reauditoría del 25 de agosto: 15 cards vigentes y 2 indicadores retirados del ITCM que permanecen como contexto y conservan serie histórica (`idm` e `icip`).

**Comparación:** [reauditoría Macro del 25/08/2026](260825_reauditoria_post_cambios_macro.md), snapshot anterior `06c3e18e` y remediación `d2288021`.

## Resultado ejecutivo

La nueva remediación resolvió dos de las cuatro discrepancias macro anteriores y corrigió materialmente las otras dos. Sin embargo, el sweep completo encuentra **dos discrepancias residuales en textos públicos activos** y una diferencia pequeña, no material, entre el costo del Tesoro calculado y la TIREA oficial exacta.

| Veredicto | 25/08 | 26/08 | Cambio |
|---|---:|---:|---:|
| Confirmado | 7 | **8** | +1 |
| Compatible | 6 | **7** | +1 |
| Discrepante | 4 | **2** | −2 |
| No verificable | 0 | **0** | — |
| **Total** | **17** | **17** | cobertura completa |

Los dos discrepantes actuales no alteran el valor mecánico publicado del ITCM:

1. `rem_ipc_12m` publica correctamente 21,8%, pero su política de faltantes todavía afirma que renormalizan el IPC, el IDM y la antigua presión de dolarización. El IDM ya no puntúa y el tercer componente vigente es `desequilibrio_monetario`.
2. `desequilibrio_monetario` calcula correctamente la nueva matriz simétrica y la nueva ventana, pero la ficha metodológica pública todavía llama al M2 “demanda transaccional” y al componente B “salida efectiva de divisas” / “la misma fuga”, justamente las interpretaciones que la remediación refutó.

El costo del Tesoro pasa de 5,80% a **4,13%** y deja de usar el cupón contractual de una reapertura. La Secretaría de Finanzas publicó TIREA de corte de 25,59% para S30N6 y 27,57% para S16O6; ponderadas por valor efectivo, producen 26,8955% nominal y **4,1835% real** contra el REM de 21,8%. El colector reconstruye 25,41% para la reapertura y publica 4,13% real. La brecha es de 0,05 punto en el titular y 0,2 punto en el puntaje: la corrección es sustantivamente correcta, pero el dato no es idéntico al equivalente oficial, por lo que queda **Compatible** y no Confirmado.

## Matriz 17/17

| # | Indicador | Estado actual | Valor · período | Score · peso | Contraste externo y de contrato | Veredicto |
|---:|---|---|---|---:|---|---|
| 1 | Inflación mensual (`ipc_total`) | Activo | 2,11% · jul-26 | 72,8 · 15,60% | INDEC informa 2,1% nacional; el segundo decimal proviene de la serie. Valor, universo, banda y serie coinciden. | **Confirmado** |
| 2 | Reservas netas CIGOB (`reservas_bcra`) | Activo | USD 11.962 M · 31-jul | 67,8 · 5,44% | Reproduce SDDS estricto + Tesoro + BOPREAL 12m. Las estimaciones externas se ubican en un rango compatible pero usan otras deducciones. | **Compatible** |
| 3 | Capacidad prestable (`idc`) | Activo | −0,32σ · jul-26 | 49,3 · 3,36% | La combinación 30/40/30 y los niveles de BCRA se reproducen; el cociente bruto de asignación no descuenta fondos no prestables. | **Compatible** |
| 4 | EMAE interanual (`emae_ia`) | Activo | 2,69% · jun-26 | 69,5 · 6,60% | Coincide con el 2,7% difundido para el EMAE nacional. | **Confirmado** |
| 5 | Difusión EMAE (`emae_difusion`) | Activo | 80% (12/15) · jun-26 | 80,0 · 2,20% | Doce de quince sectores con variación i.a. positiva; conteo y denominador visibles. | **Confirmado** |
| 6 | IPI manufacturero 3m (`ipi_manufacturero`) | Activo | −2,00% · abr-jun | 32,0 · 2,20% | La media de los tres puntos revisados cierra; las gacetillas iniciales difieren levemente por revisión. | **Compatible** |
| 7 | Saldo comercial 12m (`saldo_comercial_12m`) | Activo | USD 22.481 M · jul-25/jun-26 | 85,0 · 4,80% | La ventana móvil reconstruida es consistente con el saldo oficial de junio y los acumulados semestrales. | **Confirmado** |
| 8 | Base imponible real (`recaudacion`) | Activo | 88,2 · jun-26 | 43,0 · 7,20% | DGI seleccionada + seis sistemas COMARB, deflactación y ajuste propio reproducibles; no hay equivalente externo idéntico del empalme. | **Compatible** |
| 9 | TCRM (`tcrm`) | Activo | 85,47 · jul-26 | 48,7 · 11,00% | Promedio mensual BCRA, base dic-2015; las referencias externas quedan a menos de medio punto por corte/revisión. | **Compatible** |
| 10 | REM inflación 12m (`rem_ipc_12m`) | Activo | 21,8% · encuesta jul-26 | 81,9 · 5,20% | El dato y el equivalente mensual son exactos, pero la ficha activa describe una renormalización imposible con IDM y el indicador retirado que precedió a la tensión monetaria. | **Discrepante** |
| 11 | Brecha real M3–M2 (`idm`) | Contexto; retirado del ITCM | 4,7 pp · jul-26 | no puntúa · 0% | La serie se conserva, `en_indice=false`, no existe card ni ruta metodológica pública y el peso volvió al IPC. El retiro del índice resuelve la dirección no validable de la banda. | **Confirmado** |
| 12 | Liquidez en pesos y presión compradora (`desequilibrio_monetario`) | Activo | 38,69 pts · jun-26 | 61,3 · 5,20% | Nueva ventana y matriz se reproducen; el BCRA confirma que comprar divisas no implica sacarlas del sistema. La ficha pública, no obstante, vuelve a afirmar “demanda”, “salida efectiva” y “fuga”. | **Discrepante** |
| 13 | IAI físico (`iai`) | Activo | −0,18% · jun-26 | 59,2 · 12,00% | `0,65 × ISAC + 0,35 × bienes de capital` reproduce el titular dentro del redondeo; insumos externos confirman signo y magnitud. | **Confirmado** |
| 14 | Pagos digitales y productividad (`icip`) | Contexto; retirado del ITCM | 8,36% · abr-26 | no puntúa · 0% | La serie queda disponible como contexto, pero no hay card, banda ni peso. Es consistente con que pagos de nube/servicios no equivalgan automáticamente a formación de capital. | **Confirmado** |
| 15 | Crédito privado real en pesos (`credito_privado`) | Activo | −1,5% · jul-26 | 32,8 · 3,20% | Préstamos en pesos, punta i.a., deflactados por IPC; la estimación de First Capital (−1,3%) es compatible por IPC previo/redondeo. | **Confirmado** |
| 16 | Costo real del Tesoro (`costo_financiamiento_tesoro`) | Activo | 4,13% · jul-26 | 95,3 · 4,00% | Ya usa precio de corte para reaperturas. Contra las TIREA oficiales exactas da 4,18%; la diferencia residual de 0,05 pp no cambia color ni ITCM al décimo. | **Compatible** |
| 17 | Resultado primario/recaudación (`resultado_primario`) | Activo | 5,55% · 12m a jun | 82,2 · 12,00% | La división de los dos acumulados cierra; las fuentes externas confirman signo y corte pero publican principalmente % del PIB, otro denominador. | **Compatible** |

## Antes y después de las cuatro discrepancias macro

| Indicador | Reauditoría 25/08 | Estado actual | Evaluación 26/08 |
|---|---|---|---|
| `idm` | Valor correcto, pero banda sin dirección defendible y textos de “sobran pesos” | Sale del ITCM; conserva la serie; el peso interno del IPC pasa de 40% a 60%; no hay card pública | **Resuelto.** La decisión evita convertir una brecha descriptiva en un juicio normativo no validado. |
| `icip` | Pagos corrientes tratados como inversión y con signo automáticamente positivo | Sale del ITCM; IAI queda como 100% de Inversión; conserva la serie; no hay card pública | **Resuelto.** Coincide con el tratamiento de nube/licencias cortas como consumo intermedio en cuentas nacionales. |
| `costo_financiamiento_tesoro` | 5,80%; la reapertura S30N6 usaba 31,37% contractual en vez de 25,59% de corte | 4,13%; reconstruye 25,41% desde precio y flujo; la S16O6 queda en 27,57% | **Corregido en magnitud; Compatible.** El equivalente hecho sólo con tasas oficiales es 4,18%. |
| `desequilibrio_monetario` | 50,86; ventanas de regímenes distintos y esquinas 40/77,5 fundadas en “fuga” | 38,69; misma ventana desde abr-25 y esquinas simétricas 58,75/58,75 | **Mecánica corregida; contrato público incompleto.** La ficha generada conserva la interpretación refutada en un campo activo. |

El ITCM pasa de **64,1 (tensión 3,6)** en el snapshot de las 19:27 a **65,6 (tensión 3,4)** en el snapshot de las 21:39. El movimiento neto combina el retiro de IDM e ICIP, la nueva matriz monetaria y la corrección de la TIREA; no debe atribuirse entero a un solo cambio.

## Hallazgos residuales

### 1. La ficha del REM describe componentes que ya no pueden renormalizar

En `web/src/lib/fichas.ts`, el campo activo `rem_ipc_12m.faltantes` dice que, si falta el REM, “el IPC, el IDM y la presión de dolarización renormalizan”. El contrato real tiene sólo IPC y `desequilibrio_monetario` como componentes restantes. La frase también aparece en `output/fichas/fichas-macro.md`, por lo que no es un comentario interno ni una mención histórica.

El valor 21,8%, la conversión a equivalente mensual, el puntaje 81,9 y el peso 5,2% son correctos. La discrepancia es de contrato de score/ficha, no de cifra.

### 2. La ficha de tensión monetaria vuelve a prometer lo que el método niega

La definición, las transformaciones principales y la leyenda de fórmula ya dicen correctamente que el componente B es compra neta de divisas y no informa el destino. Sin embargo, el campo activo `dobleUso`, renderizado bajo “Participación en otros indicadores”, afirma simultáneamente que:

- el IDM compara “oferta amplia de pesos” contra “demanda transaccional”;
- el indicador mira “la salida efectiva de divisas”;
- reemplaza una medición de “la misma fuga”.

La primera limitación todavía traduce cero compras bajo cepo como “poca fuga”. Estas frases están visibles en producción en `/metodologia/desequilibrio_monetario/`. Contradicen tanto ADR-0252/0254 como la evidencia del BCRA: en junio, de las compras sin fines específicos, el banco central estimó USD 800 millones depositados localmente, USD 500 millones en activos externos y USD 700 millones aplicados a consumos con tarjeta. La compra no identifica por sí sola una salida del sistema.

También persisten las palabras “fuga” en el docstring y algunos comentarios de `scripts/desequilibrio_monetario.py`. Eso no afecta el cálculo, pero hace que el código explique otra semántica que la superficie corregida.

### 3. El costo del Tesoro es una aproximación a una tasa oficial disponible

La corrección eliminó el error grande: para la reapertura S30N6 ya no anualiza el cupón 2,30% TEM como 31,37%. Reconstruye el rendimiento desde precio y flujo y obtiene 25,41%, próximo a la TIREA oficial 25,59%.

La validación incluida en el repositorio usa trece observaciones oficiales comparables: la reconstrucción presenta RMSE **0,414 pp**, MAE **0,246 pp** y desvío máximo **1,092 pp**. El test permite RMSE menor a 0,6 pp y máximo menor a 1,5 pp. Por eso es una aproximación controlada, no la lectura literal de la tasa oficial. Un comentario en `scripts/macro.py` todavía afirma RMSE 0,09 pp, mientras el docstring del mismo método informa 0,41 pp; el segundo coincide con la ejecución.

Para julio:

```text
TIREA oficial ponderada =
  (25,59 × 2.382.801,223 + 27,57 × 4.612.304,505)
  / 6.995.105,728
  = 26,8955%

Costo real oficial equivalente = 1,268955 / 1,218 − 1 = 4,1835%
Publicado = 4,13%
```

No es una discrepancia material del indicador actual: ambos valores dan verde, el puntaje cambia aproximadamente 0,2 y el efecto sobre el ITCM es menor a 0,01. Sí impide clasificarlo como Confirmado exacto y conviene decidir si el contrato quiere “TIREA oficial leída” o “TIREA implícita estimada con tolerancia”.

## Integridad de perímetro, pesos y series

- Cards macro publicadas: **15**, exactamente las 15 que integran `BANDAS_ITCM` y las dimensiones vigentes.
- Contexto retirado del ITCM: `idm` e `icip` aparecen en el artefacto crudo con `en_indice=false`, conservan CSV/`series.json` y no aparecen en `web/src/data/informe.json`. Su contrato vigente es `INDICADORES_CONTEXTO`.
- Producción: `/macro/` y `/metodologia/desequilibrio_monetario/` responden HTTP 200; `/metodologia/idm/` y `/metodologia/icip/` responden 404, consistente con la regla “sin card pública si no puntúa”.
- Suma de pesos efectivos de las 15 cards: **1,0000**.
- Suma de pesos de dimensiones: **1,0000**; pesos internos de cada dimensión: **1,0000**.
- ITCM recalculado desde las dimensiones: **65,558 → 65,6**; tensión publicada: **3,4**.
- Los últimos puntos de `series.json` coinciden con las cards para los 15 activos y con el valor de los dos indicadores de contexto retirados del índice. En reservas, la serie usa el primer día del mes como clave mensual mientras la card muestra el cierre 31-jul; no es cambio de período económico.
- La serie completa de costo del Tesoro fue recalculada: cambian 22 de los 40 meses con colocaciones según ADR-0258. La suite cubre reaperturas, emisiones a la par, instrumentos no comparables, precios y valores efectivos.

## Verificación automática

Comando focalizado:

```bash
.venv/bin/python -m pytest -q \
  tests/test_macro_costo_financiamiento.py \
  tests/test_itcm.py \
  tests/test_desequilibrio_monetario.py \
  tests/test_idm_e_icip_no_puntuan.py \
  tests/test_constructos_no_prometen_de_mas.py \
  tests/test_contrato_publico_dice_lo_que_corre.py \
  tests/test_fichas_generadas_al_dia.py \
  tests/test_fichas_pesos.py \
  tests/test_publicar.py
```

Resultado: **160 passed**.

Las pruebas validan cálculo, exclusión, perímetro, publicación y sincronía mecánica de fichas. No detectan los dos textos residuales porque no existe una aserción específica sobre `rem_ipc_12m.faltantes` ni sobre `desequilibrio_monetario.dobleUso`/la primera limitación.

## Fuentes externas reabiertas

Los trece indicadores sin cambio de cifra o método se volvieron a contrastar contra las fuentes registradas en la reauditoría del 25/08. Para los cuatro casos modificados y los residuos se reabrieron fuentes primarias y externas:

- [INDEC — IPC nacional, julio de 2026](https://www.indec.gob.ar/Nivel4/Tema/3/5/31).
- [INDEC — intercambio comercial de junio de 2026](https://www.indec.gob.ar/ftp/ica_digital/ica_d_07_26EF37859542/).
- [BCRA — Principales Variables](https://www.bcra.gob.ar/principales-variables/) — REM 12 meses 21,8% al 31/07/2026.
- [BCRA — Informe Monetario Mensual, julio de 2026](https://www.bcra.gob.ar/publicaciones/informe-monetario-mensual-julio-de-2026/).
- [BCRA — Mercado de Cambios y Balance Cambiario, junio de 2026](https://www.bcra.gob.ar/publicaciones/informe-de-evolucion-del-mercado-de-cambios-y-balance-cambiario-junio-de-2026/).
- [Secretaría de Finanzas — licitación del 15/07/2026](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-6) — S30N6: precio 1.194, TIREA 25,59%, VE $2.382.801 millones.
- [Secretaría de Finanzas — licitación del 29/07/2026](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-8) — S16O6: TIREA 27,57%, VE $4.612.305 millones.
- [OCDE — *Business investment in the face of the digital transformation* (2026)](https://www.oecd.org/content/dam/oecd/en/publications/reports/2026/03/business-investment-in-the-face-of-the-digital-transformation_e10f8cdd/4f89aa3e-en.pdf) — licencias cortas y servicios cloud se registran generalmente como consumo intermedio, no formación de capital.
- [Secretaría de Hacienda — resultado del SPN, junio de 2026](https://www.argentina.gob.ar/node/507702).

Las fuentes específicas de los otros indicadores —SDDS y balance BCRA, COMARB, IPI/EMAE, TCRM, IAI, First Capital e IIEP— permanecen enumeradas y vinculadas caso por caso en la [reauditoría macro anterior](260825_reauditoria_post_cambios_macro.md). No hubo cambios de valor, período, universo, fórmula, score o serie en esos trece casos entre ambos snapshots, salvo la redistribución de pesos que deriva de las suspensiones y que fue recalculada arriba.

## Prioridad de cierre

1. **P0 editorial/contrato:** actualizar `rem_ipc_12m.faltantes` y `desequilibrio_monetario.dobleUso`/limitación, regenerar fichas y agregar tests literales que impidan volver a publicar “demanda”, “salida efectiva” o “fuga” como descripción vigente.
2. **P1 precisión Tesoro:** elegir explícitamente entre leer/scrapear la TIREA oficial de cada resultado o conservar la reconstrucción implícita con tolerancia declarada; alinear el comentario de RMSE 0,09 con el RMSE ejecutado de 0,414.
3. **P2 trazabilidad:** conservar el inventario por colocación y mostrar, cuando haya reaperturas, TIREA oficial o diferencia contra la reconstrucción. La infraestructura actual ya transporta precio, monto, tasa reconstruida y contractual.

## Conclusión

El cinturón Macro mejoró de **4 a 2 discrepancias** y pasó de 17 a 15 cards activas, con dos series de contexto preservadas fuera del score. Las cuatro remediaciones principales están bien orientadas: IDM e ICIP ya no puntúan; el costo del Tesoro dejó de usar el cupón de la reapertura; y la matriz monetaria usa una sola ventana de régimen y esquinas simétricas. No queda un error numérico con impacto material sobre el ITCM actual. Lo que falta cerrar es más acotado pero verificable: dos contratos públicos todavía describen componentes o significados que el cálculo vigente retiró, y la TIREA reconstruida debe presentarse como aproximación —o sustituirse por la tasa oficial— si se busca exactitud literal.
