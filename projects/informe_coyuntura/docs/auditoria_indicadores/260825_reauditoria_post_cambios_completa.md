# Reauditoría completa post-cambios — 69/69 indicadores

**Fecha de corte:** 25 de agosto de 2026

**Snapshot auditado:** `web/src/data/informe.json`, generado el 25/08/2026 a las 19:27:20 (UTC−3)

**Commit auditado:** `06c3e18e`

**Perímetro:** los mismos 69 indicadores de la auditoría original: 65 cards activas y 4 decisiones de retiro

**Método:** inspección de colectores, fórmulas, universos, series, fichas, pesos y scores; búsqueda web indicador por indicador con fuente oficial y contraste externo; pruebas locales y build completo

## Resultado ejecutivo

El segundo sweep completo confirma una mejora sustantiva, pero la remediación todavía no está cerrada como producto de punta a punta.

| Veredicto sobre el perímetro original | Antes | Ahora | Cambio |
|---|---:|---:|---:|
| Confirmado | 27 | **34** | +7 |
| Compatible | 25 | **25** | 0 |
| Discrepante | 17 | **10** | −7 |
| No verificable | 0 | **0** | 0 |
| **Total auditado** | **69** | **69** | |

La lectura complementaria del producto vigente es:

- **65 cards activas:** 32 confirmadas, 25 compatibles, 8 discrepantes y 0 no verificables.
- **4 indicadores retirados:** `reestructuracion_organismos` y `sentimiento_digital` quedaron correctamente fuera del score; `apoyo_empresario` y `judicializacion` también salieron de cards y pesos, pero siguen expuestos como si fueran vigentes en artefactos derivados.
- **Cobertura:** 69/69, sin casos bloqueados por falta de datos.

La caída de 17 a 10 discrepancias no significa que aparecieron diez errores numéricos. Ocho corresponden a cards activas: un error de tasa, seis contratos públicos o constructos todavía incoherentes y una ficha desactualizada. Las otras dos corresponden a suspensiones incompletas.

## Resultado por cinturón

| Cinturón | Perímetro auditado | Activos actuales | Confirmados | Compatibles | Discrepantes | No verificables | Score / tensión actual |
|---|---:|---:|---:|---:|---:|---:|---:|
| Macroeconomía | 17 | 17 | 7 | 6 | **4** | 0 | 64,1 / 3,6 |
| Política | 19 | 17 | 9 | 6 | **4** | 0 | 70,9 / 2,9 |
| Impacto social | 19 | 18 | 10 | 7 | **2** | 0 | 93,8 / 6,2 |
| Gestión | 14 | 13 | 8 | 6 | **0** | 0 | 79,6 / 2,0 |
| **Total** | **69** | **65** | **34** | **25** | **10** | **0** | Global: **3,7** |

En Política, dos de las cuatro discrepancias son indicadores retirados con residuos públicos. En Impacto social, el confirmado adicional es el retiro correcto de `sentimiento_digital`. En Gestión, el confirmado adicional es el retiro correcto de `reestructuracion_organismos`. Por eso la columna de veredictos se refiere al perímetro original y no sólo a las cards vigentes.

## Las 10 discrepancias que quedan

### Prioridad 0 — un valor activo todavía incorrecto

#### 1. Costo real del financiamiento del Tesoro (`costo_financiamiento_tesoro`)

- **Publicado:** 5,80% real anual para julio de 2026.
- **Reproducible con las tasas de corte oficiales:** aproximadamente **4,18%**.
- **Causa:** en la reapertura S30N6 se anualiza el cupón contractual de 2,30% TEM, equivalente a 31,37%, en vez de usar la **TIREA de corte 25,59%** determinada por el precio de la reapertura. La S16O6 del 29/07 sí usa correctamente 27,57%.
- **Reconstrucción:** TIREA ponderada de julio 26,8955%; contra REM 12 meses de 21,8%, costo real 4,1835%.
- **Impacto:** el indicador debería puntuar aproximadamente 95,1 y la dimensión Financiamiento 63,7; el ITCM sería aproximadamente **64,4**, no 64,1.
- **Acción:** obtener TIREA/TEM de corte por licitación o calcular el rendimiento desde precio y flujo en toda reapertura; agregar un fixture específico para S30N6 y reauditar reaperturas históricas.
- **Evidencia:** [resultado oficial del 15/07](https://www.argentina.gob.ar/node/507628), [resultado de mercado que reproduce 25,59%](https://www.roadshow.com.ar/economia-coloco-us-470-millones-del-nuevo-bonar-2029-y-supero-el-183-de-rollover/) y [planilla oficial de colocaciones](https://www.argentina.gob.ar/sites/default/files/colocaciones_31-07-26_1.xlsx).

### Prioridad 1 — números corregidos, contrato público todavía viejo

#### 2. Ratio DNU / leyes (`ratio_dnu`)

- El valor **1,48 = 37/25** y el inventario jurídico están corregidos.
- `descripciones.ts`, `formulas.ts`, `fichas.ts` y la ficha generada todavía hablan de “DNU dictados / leyes sancionadas” y de la búsqueda textual descartada.
- El contrato correcto debe ser único: **DNU publicados / leyes publicadas en el Boletín Oficial, ventana de 365 días**.

#### 3. Transferencias federales reales (`iaf_transferencias`)

- El valor **+1,6% real** está corregido y coincide con el contraste de IARAF.
- La implementación deflacta cada flujo mensual antes de sumar, pero la fórmula y ficha públicas todavía describen sumas anuales divididas por un IPC promedio anual.
- Hay que actualizar todas las capas explicativas y explicitar jurisdicciones, clases de transferencia, ventana, IPC y base común.

### Prioridad 1 — constructos macro renombrados, pero no rediseñados

#### 4. Brecha de crecimiento real M3–M2 (`idm`)

- El valor 4,7 pp y el nuevo nombre descriptivo son correctos.
- Las bandas siguen castigando automáticamente una brecha positiva como si probara “exceso de pesos”.
- Textos activos todavía dicen que M2 son los pesos que la gente “quiere” y que un valor positivo significa que “sobran pesos”.
- Mantenerlo fuera de una lectura causal hasta justificar signo y bandas, o estimar explícitamente una función de demanda de dinero.

#### 5. Tensión monetaria CIGOB (`desequilibrio_monetario`)

- La etiqueta principal mejoró, pero la matriz, sus ponderaciones y textos activos siguen interpretando compras netas como “fuga oculta/fuera del sistema”.
- La fuente no identifica el destino de las divisas; no permite afirmar salida del sistema local.
- Rediseñar el componente B y recalibrar la matriz, o conservarlo sólo como presión compradora sin la interpretación refutada.

#### 6. Pagos digitales y productividad (`icip`)

- El nombre de card es más descriptivo, pero continúa dentro de la dimensión Inversión y todo aumento de pagos transfronterizos eleva el score.
- `formulas.ts` y la narrativa activa todavía los llaman “inversión intangible” o “capitalización digital”.
- Los pagos de servicios digitales pueden ser consumo intermedio; no identifican formación de capital. Debe salir de Inversión o cambiar su primer insumo.

### Prioridad 1 — suspensiones correctas, depublicación incompleta

#### 7. Postura pública de AEA y UIA (`apoyo_empresario`)

- Ya no genera card ni peso: esa decisión es correcta.
- Sigue en `series.json`, CSV, `output/informe.json`, `output/informe.md` y fichas. El artefacto crudo lo marca `en_indice: true`.
- La descripción de Sector privado todavía promete dos vías cuando sólo queda una activa.

#### 8. Judicialización de la agenda (`judicializacion`)

- Ya no genera card ni peso: esa decisión es correcta.
- Su serie continúa publicada bajo el constructo refutado; `output/informe.json` todavía declara `en_indice: true` y `peso_efectivo: 0.03`.
- La descripción de Poder judicial todavía enumera cuatro vías cuando hoy son tres.

La solución para ambos casos no es borrar necesariamente la historia. Es definir un contrato inequívoco: una serie retirada puede preservarse como archivo, pero no debe aparecer como componente vigente ni conservar peso/estado activo en consumidores públicos.

### Prioridad 2 — dato vigente correcto, metadato o ficha incorrectos

#### 9. Subocupación demandante (`subocupacion_demandante`)

- ID, serie, valor 7,5%, unidad principal, score y peso están correctamente migrados; `pluriempleo` ya no subsiste en datos.
- `descripciones.ts` y la ficha generada todavía dicen “porcentaje de los ocupados”. INDEC define la tasa sobre la **PEA**.

#### 10. Ventas en supermercados (`consumo_supermercados`)

- Snapshot, serie y colector publican correctamente junio de 2026 = **82,1**, base 2017=100, índice 90,1.
- La ficha generada conserva mayo = 83,2, índice 91,2 y el espejo anterior.
- Regenerar la ficha desde el mismo snapshot y agregar una regresión que exija igualdad de período, valor y puntaje entre card y ficha.

## Estado de las 17 discrepancias originales

| Caso original | Estado post-cambios | Veredicto actual | Qué falta |
|---|---|---|---|
| Costo del Tesoro | Cambió 8,07% → 5,80%, pero persiste otro error en una reapertura | **Discrepante** | Usar TIREA de corte; resultado ~4,18% |
| Transferencias reales | Valor 0,8% → 1,6% corregido | **Discrepante** | Sincronizar fórmula y ficha públicas |
| Cobertura judicial | 69,63% conciliado como 665/955 | **Resuelto** | Mantener inventario y corte reproducibles |
| Ratio DNU | 1,92 → 1,48 con tipos jurídicos | **Discrepante** | Sincronizar definición pública con publicación/publicación |
| ICC UTDT | 39,9 CABA → 40,2 nacional | **Resuelto** | Actualizar texto general de Percepción |
| Supermercados | 82,1 de junio y base 2017 correctos | **Discrepante** | Regenerar ficha vieja |
| Concesiones | 28,7% → 100% con II-B y III | **Resuelto** | Sin deuda material del indicador |
| Apoyo empresario | Fuera de cards y score | **Discrepante** | Retirar estado activo de series/artefactos/fichas |
| Reestructuración | Fuera de cards y score | **Resuelto** | Limpiar descripción y analítica de redundancia |
| Sentimiento digital | Fuera de cards y score | **Resuelto** | Actualizar descripción general de Percepción |
| Crédito privado | Universo homogéneo en pesos; −1,5% | **Resuelto** | Mantener explícito punta vs. promedio |
| Trabajo independiente | Universo restringido enumerado | **Resuelto** | Acortar fuente textual ambigua |
| Subocupación | ID y serie migrados; 7,5% PEA | **Discrepante** | Corregir una definición residual |
| IDM | Rótulo descriptivo corregido | **Discrepante** | Recalibrar score y limpiar lectura causal activa |
| Tensión monetaria | Rótulo principal corregido | **Discrepante** | Rediseñar matriz/interpretación y limpiar “fuga” |
| ICIP | Rótulo principal corregido | **Discrepante** | Sacarlo de Inversión o cambiar insumo/signo |
| Judicialización | Fuera de cards y score | **Discrepante** | Retirar estado activo de artefactos públicos |

Resultado sobre este conjunto prioritario: **7 resueltos y 10 todavía incompletos**. No debe interpretarse “resuelto” como ausencia absoluta de deuda editorial; significa que la cifra, universo o decisión de score que originó la discrepancia quedó corregida.

## Residuos transversales que no agregan nuevas filas al conteo

Además de las diez discrepancias de indicador, quedan contratos descriptivos que deben alinearse con la topología efectiva:

- Política: Sector privado todavía dice dos vías y Poder judicial cuatro, aunque hoy tienen una y tres respectivamente.
- Impacto social: Percepción todavía se describe como ICC más búsquedas, aunque ICC absorbe correctamente el 100% interno activo y 8,25% efectivo.
- Gestión: Reforma del Estado todavía dice tres medidas, aunque hoy puntúan dos.
- Gestión: la analítica de redundancia declara 14 componentes y 76 pares e incluye `reestructuracion_organismos`, aunque sólo hay 13 cards activas.
- Las series históricas retiradas pueden conservarse, pero deben tener metadatos explícitos de suspensión y quedar fuera de toda analítica que describa el universo vigente.

Estos residuos no alteran los cuatro scores actuales salvo el error del costo del Tesoro, pero sí pueden inducir a consumidores y lectores a reconstruir una metodología distinta de la ejecutada.

## Integridad de pesos, scores y publicación

- Los cuatro cinturones publican 17, 17, 18 y 13 cards, respectivamente: **65 activas**.
- Los IDs activos de las dimensiones coinciden con los IDs de cards en los cuatro cinturones.
- Los pesos efectivos suman exactamente 1 dentro de cada cinturón.
- Los indicadores suspendidos no aportan a los scores efectivos.
- ITCM 64,1 / tensión 3,6; ITCP 70,9 / 2,9; ITCIS 93,8 / 6,2; ITCG 79,6 / 2,0; tensión global 3,7.
- El único impacto cuantitativo nuevo reproducido es costo del Tesoro: corregirlo elevaría aproximadamente ITCM 64,1 → 64,4.

## Validación ejecutada

| Control | Resultado |
|---|---|
| Verificador de remediación contra `linea_base_260825.json` | **OK** |
| Suite Python completa | **3024 passed, 3 skipped** |
| Pruebas focalizadas Macro | **67 passed** |
| Pruebas focalizadas Política | **96 passed** |
| Pruebas focalizadas Impacto social | **111 passed** |
| Build Astro | **OK, 83 páginas generadas** |
| Pesos y perímetros activos | **OK, cuatro cinturones suman 1** |

La suite completa se ejecutó en serie porque el entorno no tiene instalado `pytest-xdist`; el intento con `-n 6` fue rechazado por argumento desconocido, no por una falla de tests. El build sólo emitió la advertencia ya conocida de un chunk de Vite mayor a 500 kB.

Los tests demuestran integridad mecánica de la implementación actual, pero no validan por sí solos la semántica económica. El error de la reapertura S30N6 ilustra el hueco: la prueba existente cubre emisiones nuevas a la par, no reaperturas con precio distinto de la par.

## Expedientes detallados

- [Macroeconomía — 17/17](260825_reauditoria_post_cambios_macro.md)
- [Política — 19/19](260825_reauditoria_post_cambios_politica.md)
- [Impacto social — 19/19](260825_reauditoria_post_cambios_impacto_social.md)
- [Gestión — 14/14](260825_reauditoria_post_cambios_gestion.md)
- [Auditoría original — 69/69](260825_auditoria_completa.md)
- [Handoff original de las 17 discrepancias](260825_handoff_claude_remediacion_17_discrepancias.md)

Cada expediente contiene la matriz completa indicador por indicador, fuentes externas, cálculos, confianza y recomendación específica. Este consolidado no reemplaza esos expedientes: funciona como mapa de estado y orden de trabajo.

## Mandato recomendado para la próxima remediación

1. Corregir primero la TIREA de reaperturas del Tesoro y reconstruir su historia.
2. Sincronizar contratos públicos de DNU e IAF con la lógica ya corregida.
3. Completar la depublicación de apoyo empresario y judicialización con un estado histórico explícito.
4. Corregir denominador de subocupación y regenerar la ficha de supermercados.
5. Tomar una decisión metodológica explícita sobre IDM, tensión monetaria e ICIP: no alcanza con cambiarles el nombre.
6. Alinear descripciones de dimensiones y excluir suspendidos de redundancia, sensibilidad y validación externa vigentes.
7. Agregar pruebas de contrato entre colector, snapshot, fórmula, ficha y series para que período, valor, unidad, universo y estado activo no puedan divergir.

No editar valores directamente en JSON o Markdown generado. Toda corrección debe nacer en colector/configuración/metadato fuente, incorporar una regresión y recién después regenerar informe, fichas, series y snapshot.
