# Reverificación post-remediación — Gestión

**Fecha de corte:** 26 de agosto de 2026

**Estado auditado:** `e1dfab84`; snapshot generado el 25/08/2026 a las 21:39:35 (UTC−3)

**Perímetro:** los mismos 14 indicadores de la auditoría original: 13 cards activas y el retiro de `reestructuracion_organismos`

## Resultado

| Veredicto | Cantidad |
|---|---:|
| Confirmado | 8 |
| Compatible | 6 |
| Discrepante | 0 |
| No verificable | 0 |
| **Total** | **14** |

Entre las 13 cards vigentes hay 7 confirmadas y 6 compatibles. El octavo confirmado es la decisión de retirar `reestructuracion_organismos`: continúa fuera de cards y score, y el artefacto crudo lo identifica como archivo con `en_indice: false`, sin peso ni puntaje.

Ningún valor de Gestión cambió respecto de la reauditoría del 25 de agosto. Se repitieron la comparación de snapshot, pesos, fichas y fuentes web; los trece resultados conservan el mismo veredicto. ITCG continúa en 79,6 y tensión 2,0.

## Matriz completa 14/14

| # | Indicador | Estado actual | Contraste de reverificación | Veredicto | Confianza |
|---:|---|---|---|---|---|
| 1 | Brecha cambiaria | 5,91%, 25-08-2026 | TN informó CCL $1.600,29 y mayorista $1.511,50; la brecha de cierre es 5,87%, compatible con una captura intradiaria de 5,91% | **Compatible** | Alta |
| 2 | Apertura comercial | 6,18%, jun-2026 | INDEC confirma USD 15.916 M de intercambio; ARCA, $881.128 M DEX y $545.789 M DIM. Convertido por A3500 reproduce el orden y redondeo | **Compatible** | Alta |
| 3 | Desregulación normativa | 16.771 artículos, jul-2026 | La página oficial publica 719 normas, 2.803 normas afectadas y 16.771 artículos | **Confirmado** | Alta |
| 4 | Dotación del Estado | −20,36% vs. dic-2023, jun-2026 | Universo APN explícito, sin empresas públicas; la dotación publicada y la base reproducen la variación | **Confirmado** | Alta |
| 5 | Gasto de funcionamiento | −31,37% real vs. jun-2023 | CEPA obtiene una contracción de magnitud equivalente para el agregado comparable | **Confirmado** | Alta |
| 6 | Reestructuración de organismos | Retirado | Continúa fuera de dimensión, card y peso; se conserva sólo como archivo rotulado | **Confirmado el retiro** | Alta |
| 7 | Fondo de Asistencia Laboral | 50/100, 25-08-2026 | Ley y Decreto dictados; el artículo 27 del Decreto 408/2026 difiere la vigencia al 01-11-2026; 50 por construcción, cero por vigencia/adopción | **Confirmado** | Alta |
| 8 | Litigiosidad laboral | +2,1%, 12m a may-2026 | La serie SRT y los flujos mensuales sostienen magnitud y signo, pero no hay réplica externa publicada de las dos sumas móviles completas | **Compatible** | Media-alta |
| 9 | Privatizaciones | 51,4%, corte 30-06-2026 | Las fuentes confirman estados heterogéneos de la cartera; la codificación CIGOB 0–4 y el promedio no tienen réplica independiente exacta | **Compatible** | Media |
| 10 | Inversiones RIGI | 23,5%, 25-08-2026 | 21 proyectos aprobados por USD 46.708 M y 23 pendientes por ~USD 152.271 M reproducen aproximadamente 23,5% | **Confirmado** | Alta |
| 11 | Concesiones viales | 100% = 9.091/9.091 km | Resoluciones 1149/2026 y 1379/2026 confirman las adjudicaciones de II-B y III y completan las cuatro etapas | **Confirmado** | Alta |
| 12 | Asistencia directa | 100% | La estructura presupuestaria respalda pago directo, pero la partida 5.1.4 por sí sola no demuestra ausencia total de intermediación operativa | **Compatible** | Media-baja |
| 13 | Orden público | 74,2% de reducción en CABA | 240 cortes en 2025 y la participación de CABA en 2023 permiten reconstruir aproximadamente 74,2% | **Confirmado** | Alta |
| 14 | Libertad de opción en salud | 31,8%, mar-2026 | La normativa y los benchmarks sectoriales sostienen numerador y orden de magnitud, no el padrón RNEMP exacto usado como denominador | **Compatible** | Media |

## Fuentes web reabiertas

- Brecha: [TN, cotizaciones del 25 de agosto](https://tn.com.ar/economia/2026/08/25/dolar-a-cuanto-cotizan-el-oficial-y-las-otras-opciones-cambiarias-este-martes-25-de-agosto/) y [La Nación, mayorista/CCL](https://www.lanacion.com.ar/economia/el-dolar-mayorista-abrio-la-semana-superando-la-barrera-de-los-1500-nid24082026/).
- Comercio: [INDEC, ICA junio](https://www.indec.gob.ar/ftp/ica_digital/ica_d_07_26EF37859542/) y [ARCA, información agregada](https://arca.gob.ar/operadoresComercioExterior/informacionAgregada/informacion-agregada.asp).
- Desregulación: [Ministerio de Desregulación, datos acumulados a julio](https://www.argentina.gob.ar/desregulacion).
- Gasto: [CEPA, SPN a junio de 2026](https://centrocepa.com.ar/documentos/informes/821-analisis-de-los-ingresos-gastos-y-resultados-del-sector-publico-nacional-datos-de-junio-2026).
- FAL: [Decreto 408/2026](https://www.argentina.gob.ar/normativa/nacional/norma-426272/texto).
- RIGI: [plataforma oficial](https://www.argentina.gob.ar/economia/rigi) y [contraste de proyectos y montos](https://www.lanacion.com.ar/economia/rigi-hay-mas-de-20-proyectos-aprobados-con-una-inversion-total-de-casi-us50000-millones-nid15082026/).
- Concesiones: [Resolución 1379/2026](https://www.boletinoficial.gob.ar/detalleAviso/primera/346271/20260824) y [Red Federal de Concesiones](https://www.argentina.gob.ar/transporte/vialidad-nacional/red-federal-de-concesiones).
- Orden público: [La Nación, monitoreo de piquetes](https://www.lanacion.com.ar/politica/los-piquetes-se-redujeron-mas-del-527-desde-que-asumio-milei-hay-menos-protestas-de-las-nid13012026/).
- Salud: [libre elección y derivación directa](https://www.argentina.gob.ar/node/451904).

## Integridad del score y del retiro

- El snapshot tiene 13 cards de Gestión y las dimensiones del ITCG contienen exactamente los mismos 13 IDs.
- Los pesos efectivos suman 1,0000.
- Reforma del Estado contiene sólo `reduccion_estado` y `gasto_funcionamiento`, con pesos efectivos 14,58% y 10,42%.
- `reestructuracion_organismos` aparece en `output/informe.json` con `en_indice: false`, bloque `suspendido` y sin campos de score.
- La descripción pública de Reforma del Estado ya dice dos medidas y explica el retiro histórico.

## Dos residuos fuera del conteo de indicador

### Analítica de redundancia todavía usa un universo retirado

La explicación pública de redundancia del ITCG sigue declarando **14 componentes y 76 pares**. `output/validacion_externa.json` incluye `masa_salarial` y `reestructuracion_organismos` en la matriz, aunque ambos están suspendidos y el ITCG vigente tiene 13 cards. Además, `n_indicadores = 14` no coincide con las 13 claves visibles de esa matriz.

Esto no altera ITCG 79,6: el bloque es validación derivada. Sí vuelve ambigua o falsa la afirmación pública sobre “los componentes” del índice vigente. Debe recalcularse con los IDs activos o rotularse expresamente como análisis histórico de un universo anterior.

### DOCX institucional desactualizado

`scripts/fichas/verificar.py` marca 12 diferencias en `Fichas Semaforo Gestion.docx`, entre ellas ITCG 73,2 frente a 79,6 y concesiones 28,7% frente a 100%. El ADR-0260 declara que los DOCX son copias manuales de la última versión enviada y no espejos automáticos; por eso no es una discrepancia de web/Markdown. Aun así, ese archivo no debe reenviarse sin regenerarlo y volver a verificarlo.

## Conclusión

Gestión conserva **0 discrepancias entre sus 14 decisiones originales**. Las dos discrepancias que existían —concesiones y reestructuración— permanecen correctamente resueltas. Quedan una deuda de universo en la analítica de redundancia y un DOCX institucional viejo, sin impacto en las cards o en el score vigente.
