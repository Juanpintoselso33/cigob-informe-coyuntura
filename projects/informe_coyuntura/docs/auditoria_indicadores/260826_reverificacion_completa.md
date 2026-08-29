# Reverificación completa — tercer sweep 69/69

**Fecha:** 26 de agosto de 2026

**HEAD auditado:** `e1dfab84`

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25/08/2026 a las 21:39:35 (UTC−3)

**Perímetro:** los mismos 69 indicadores/decisiones de la auditoría original: 63 cards vigentes y 6 indicadores correctamente retirados del tablero o conservados como archivo/contexto

**Alcance:** cifra, período, unidad, universo, fórmula, score, peso, dimensión, series, fichas, artefactos derivados, producción y contraste web con fuentes oficiales y externas

## Resultado ejecutivo

La nueva remediación bajó las discrepancias de **10 a 3**. No quedan discrepancias numéricas en Impacto social ni Gestión. Las tres actuales son dos contratos públicos activos de Macro y un subconteo material de sesiones de control judicial en Política.

| Veredicto sobre el perímetro original | Auditoría inicial | Reauditoría 25/08 | Reverificación 26/08 |
|---|---:|---:|---:|
| Confirmado | 27 | 34 | **40** |
| Compatible | 25 | 25 | **26** |
| Discrepante | 17 | 10 | **3** |
| No verificable | 0 | 0 | **0** |
| **Total** | **69** | **69** | **69** |

Lectura del producto hoy:

- **63 cards activas:** 34 confirmadas, 26 compatibles, 3 discrepantes.
- **6 decisiones de retiro/contexto confirmadas:** `idm`, `icip`, `apoyo_empresario`, `judicializacion`, `sentimiento_digital` y `reestructuracion_organismos` no aportan a ningún score ni aparecen como cards.
- **0 casos no verificables:** hubo evidencia suficiente para emitir veredicto en las 69 filas.

## Resultado por cinturón

| Cinturón | Perímetro | Cards actuales | Confirmados | Compatibles | Discrepantes | No verificables | Índice / tensión |
|---|---:|---:|---:|---:|---:|---:|---:|
| Macroeconomía | 17 | 15 | 8 | 7 | **2** | 0 | 65,6 / 3,4 |
| Política | 19 | 17 | 12 | 6 | **1** | 0 | 70,9 / 2,9 |
| Impacto social | 19 | 18 | 12 | 7 | **0** | 0 | 93,8 / 6,2 |
| Gestión | 14 | 13 | 8 | 6 | **0** | 0 | 79,6 / 2,0 |
| **Total** | **69** | **63** | **40** | **26** | **3** | **0** | Global: **3,6** |

Los conteos por cinturón incluyen las decisiones de retiro del perímetro original. Por eso los veredictos suman 69 aunque el tablero vigente tenga 63 cards.

## Las tres discrepancias actuales

### 1. Actividad de comisiones de control (`paralisis_denuncias`) — valor subestimado

**Publicado:** 7 sesiones en los últimos doce meses.

**Problema:** el extractor no cuenta sesiones; cuenta notas cuyo *slug* coincide con un regex muy específico: `sesiono-la-comision-de-(acusacion|disciplina)-N`. Cuando una sesión produce una noticia con título sustantivo, la URL cambia y el evento desaparece.

El propio universo curado del repositorio reconoce tres reuniones adicionales alrededor de la ventana; las dos últimas caen dentro de los doce meses calendario correctos:

- 06-08-2025, Acusación: reunión que propone abrir un proceso de remoción;
- 17-03-2026, Acusación: sesión ordinaria que propone acusar a dos jueces;
- 28-05-2026, Acusación: sesión ordinaria que propone iniciar otra remoción.

Por lo tanto, el mínimo conciliado dentro de septiembre de 2025–agosto de 2026 es **9**, no 7. El archivo oficial contiene además cinco reuniones combinadas en esa ventana; si el indicador conserva la definición amplia “cuántas veces sesionaron”, el inventario completo llega a **14**. La [sesión ordinaria del 28 de mayo](https://consejomagistratura.gov.ar/index.php/2026/05/28/la-comision-de-acusacion-propone-al-plenario-iniciar-el-proceso-de-remocion-del-juez-salmain/) demuestra el modo de falla: fue sesión, pero el título no satisface el regex.

| Escenario | Puntaje del indicador | Poder judicial | ITCP | Tensión Política |
|---|---:|---:|---:|---:|
| Publicado: 7 | 45,0 | 60,7 | 70,9 | 2,9 |
| Mínimo conciliado: 9 | 10,0 | 52,0 | 69,6 | 3,0 |
| Inventario amplio: 14 | 10,0 | 52,0 | 69,6 | 3,0 |

**Acción:** definir evento de sesión, decidir explícitamente el tratamiento de reuniones conjuntas, reconstruir un inventario deduplicado desde título+cuerpo y rehacer la serie. Los tres eventos ya reconocidos por el repositorio no pueden excluirse de un indicador que se llama cantidad de sesiones.

### 2. REM inflación 12 meses (`rem_ipc_12m`) — política de faltantes obsoleta

El valor **21,8%**, el score 81,9 y el peso efectivo 5,2% son correctos. La discrepancia está en `web/src/lib/fichas.ts` y en la ficha Markdown generada: el campo activo de faltantes dice que, si falta el REM, renormalizan “el IPC, el IDM y la presión de dolarización”.

Ese contrato ya no existe:

- IDM fue retirado del ITCM y quedó como contexto;
- la antigua presión de dolarización fue reemplazada por `desequilibrio_monetario`;
- los únicos componentes restantes de la dimensión son IPC y liquidez/presión compradora.

**Acción:** actualizar la política de faltantes para nombrar los componentes vigentes y agregar una prueba que compare los IDs citados por la ficha con la dimensión efectiva.

### 3. Liquidez en pesos y presión compradora (`desequilibrio_monetario`) — interpretación refutada en texto activo

La mecánica nueva es reproducible: misma ventana de régimen abierto para ambos componentes, esquinas cruzadas simétricas, valor 38,69 y score 61,3. Sin embargo, el campo público activo `dobleUso` todavía afirma que:

- M2 es “demanda transaccional”;
- el indicador observa “salida efectiva de divisas”;
- reemplaza una medición de “la misma fuga”.

Estas frases están visibles en producción en `/metodologia/desequilibrio_monetario/` y contradicen la propia remediación: la compra neta de divisas no informa su destino. La fórmula principal ya lo explica correctamente; la ficha se contradice dentro de la misma página.

**Acción:** eliminar “demanda”, “salida efectiva” y “fuga” de campos activos; mantener esas palabras sólo en el changelog histórico que explica el nombre abandonado. Agregar regresiones sobre `dobleUso` y limitaciones, no sólo sobre título/fórmula.

## Estado de las diez discrepancias de la pasada anterior

| Discrepancia del 25/08 | Estado 26/08 | Evaluación |
|---|---|---|
| Costo real del Tesoro | 5,80% → 4,13%; equivalente con TIREA oficiales 4,18% | **Resuelta en magnitud; Compatible** |
| Ratio DNU | Fórmula, ficha y unidad ya dicen publicados/publicadas | **Resuelta; Confirmado** |
| Transferencias reales | Fórmula/ficha ya describen deflación mensual | **Resuelta; Confirmado** |
| IDM | Fuera del score/card; serie como contexto | **Resuelta; retiro confirmado** |
| Tensión monetaria | Ventana y matriz corregidas | **Parcial: queda texto activo refutado** |
| ICIP | Fuera del score/card; serie como contexto | **Resuelta; retiro confirmado** |
| Apoyo empresario | Crudo marcado archivo, sin peso/puntaje; no card | **Resuelta; suspensión confirmada** |
| Judicialización | Crudo marcado archivo, sin peso/puntaje; no card | **Resuelta; suspensión confirmada** |
| Subocupación | Descripción y ficha dicen correctamente % de la PEA | **Resuelta; Confirmado** |
| Supermercados | Snapshot, serie y ficha: junio 82,1, base 2017 | **Resuelta; Confirmado** |

Nueve de las diez quedaron cerradas en su causa original. La tensión monetaria quedó corregida en cálculo, pero no completamente en la superficie explicativa.

## Hallazgo de precisión: costo del Tesoro

La corrección importante está bien: una reapertura ya no usa el cupón contractual 31,37% como si fuera rendimiento de corte. El colector reconstruye 25,41% desde precio y flujo para S30N6 y publica costo real 4,13%.

Las TIREA oficiales son 25,59% y 27,57%; ponderadas por valor efectivo producen 26,8955% nominal y **4,1835% real**. La diferencia publicada es 0,05 punto, sin cambio de color y con impacto menor a 0,01 sobre el ITCM, por lo que el veredicto es Compatible.

La validación de trece tasas presenta RMSE 0,414 pp, MAE 0,246 pp y máximo 1,092 pp. Un comentario de `scripts/macro.py` todavía afirma RMSE 0,09 pp; el docstring y la ejecución dan aproximadamente 0,41. Conviene elegir un contrato inequívoco: leer la TIREA oficial o declarar que se publica una reconstrucción implícita con tolerancia.

Fuentes: [licitación del 15/07 — S30N6](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-6) y [licitación del 29/07 — S16O6](https://www.argentina.gob.ar/noticias/resultado-de-la-licitacion-por-efectivo-de-instrumentos-del-tesoro-nacional-denominados-8).

## Residuos transversales fuera del conteo 69

### Redundancia de Gestión usa componentes suspendidos

La página pública de Gestión declara que la redundancia cruza **14 componentes y 76 pares**. `output/validacion_externa.json` incluye `masa_salarial` y `reestructuracion_organismos`, aunque ambos están suspendidos y el ITCG vigente tiene 13 cards. Además, el campo `n_indicadores = 14` no coincide con las trece claves visibles de la propia matriz.

No altera ITCG 79,6, porque es analítica derivada. Sí describe como componentes actuales variables retiradas. Debe recalcularse con los IDs activos o rotularse explícitamente como análisis histórico.

### Los DOCX institucionales están vencidos

`scripts/fichas/verificar.py` encuentra **61 diferencias** en los Word manuales:

| Documento | Diferencias |
|---|---:|
| Macro | 17 |
| Política | 20 |
| Gestión | 12 |
| Impacto social | 12 |
| **Total** | **61** |

Los Markdown y la web sí están sincronizados; ADR-0260 define los Word como copias manuales de la última versión enviada, no como espejos nocturnos. Por eso estas diferencias no degradan los veredictos de las cards. Pero ningún DOCX debe volver a circular sin regenerarse y pasar el verificador.

## Integridad de score, perímetro y publicación

- Cards actuales: Macro 15, Política 17, Impacto social 18, Gestión 13; total 63.
- Los IDs de cards coinciden con los componentes efectivos de cada índice.
- Pesos efectivos: 1,0000 en los cuatro cinturones.
- Los seis indicadores retirados no tienen card ni aporte. `apoyo_empresario`, `judicializacion` y `reestructuracion_organismos` se conservan en el artefacto crudo con `en_indice: false`, sin peso/puntaje y con motivo; `sentimiento_digital` conserva sólo su serie de archivo. IDM e ICIP quedan como contexto, no como suspendidos.
- ITCM 65,6 / tensión 3,4; ITCP 70,9 / 2,9; ITCIS 93,8 / 6,2; ITCG 79,6 / 2,0; global 3,6.
- Producción responde HTTP 200 en home, los cuatro cinturones y fichas vigentes; `/metodologia/idm/` responde 404 de acuerdo con la regla de no publicar una card/ficha vigente si no puntúa.
- La producción ya muestra 65,6, 4,13 y 38,69 en Macro; 70,9 y publicados/publicadas en Política; 93,8, 82,1 y `% de la PEA` en Impacto social; 79,6 y dos medidas en Reforma del Estado.
- También se reprodujeron en producción los dos textos macro obsoletos y el rótulo de 14 componentes/76 pares de Gestión, por lo que no son artefactos locales sin desplegar.

## Validación automática

| Control | Resultado |
|---|---|
| Suite Python completa | **3181 passed, 3 skipped, 5 warnings** |
| Tests focalizados Macro | **160 passed** |
| Tests focalizados Política | **439 passed** |
| Tests focalizados Impacto social | **281 passed** |
| Build Astro | **OK, 81 páginas** |
| Verificador de remediación | **OK, 69 → 63 cards, score global 3,9 → 3,6** |
| Pesos y topología | **OK** |
| Producción | **HTTP 200 y snapshot nuevo visible** |

Los tests cubren cálculo y contratos ya formalizados. No detectan los tres hallazgos actuales porque validan el regex de sesiones sin probar cobertura contra el inventario, y no inspeccionan los campos textuales específicos `faltantes`/`dobleUso`.

## Expedientes por cinturón

- [Macro — 17/17](260826_reverificacion_macro.md)
- [Política — 19/19](260826_reverificacion_politica.md)
- [Impacto social — 19/19](260826_reverificacion_impacto_social.md)
- [Gestión — 14/14](260826_reverificacion_gestion.md)
- [Consolidado de la pasada anterior](260825_reauditoria_post_cambios_completa.md)

## Orden recomendado de cierre

1. Corregir `paralisis_denuncias`: inventario de eventos, definición de reuniones combinadas, serie reconstruida y regresiones de cobertura.
2. Limpiar los campos activos de `desequilibrio_monetario` y actualizar la política de faltantes del REM.
3. Recalcular o rerrotular la redundancia de Gestión con su universo vigente.
4. Decidir si costo del Tesoro lee TIREA oficial o publica una reconstrucción aproximada; corregir la cifra de RMSE del comentario.
5. Regenerar los cuatro DOCX institucionales antes de volver a distribuirlos.

No corregir JSON, Markdown o HTML a mano. Las soluciones deben nacer en extractor/metadato fuente, incluir pruebas de regresión y regenerar todos los artefactos derivados.
