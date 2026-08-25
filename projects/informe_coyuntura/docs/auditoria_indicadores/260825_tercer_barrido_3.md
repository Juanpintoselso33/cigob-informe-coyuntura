# Tercer barrido de los tres indicadores residuales

**Fecha de corte:** 25 de agosto de 2026
**Snapshot auditado:** `web/src/data/informe.json`
**Alcance:** IdC, Conflictividad social nacional y Sentimiento digital; los tres casos que permanecían sin verificación independiente después de la segunda ronda.

## Resultado ejecutivo

Los tres expedientes quedaron cerrados. Esto no significa que los tres indicadores sean correctos: dos resultaron compatibles y uno quedó refutado como constructo puntuable.

| Indicador | Segundo barrido | Tercer barrido | Confianza | Decisión |
|---|---|---|---|---|
| Capacidad prestable (IdC) | No verificable | **Compatible** | Alta para cifra y reconciliación; media para el nombre | Mantener, pero renombrar como condiciones de fondeo/intermediación o rediseñar descontando encajes |
| Conflictividad social nacional (ACLED) | No verificable | **Compatible** | Alta | Mantener con paquete de trazabilidad; aclarar que compara ventanas de 52 semanas, no meses calendario estrictos |
| Sentimiento digital | No verificable | **Discrepante** | Alta | Retirar del score; conservar sólo como atención descriptiva de seis búsquedas hasta rediseñarlo |

El balance definitivo de los 69 indicadores queda en:

| Cinturón | Indicadores | Confirmados | Compatibles | Discrepantes | No verificables |
|---|---:|---:|---:|---:|---:|
| Macro | 17 | 6 | 6 | 5 | 0 |
| Política | 19 | 6 | 8 | 5 | 0 |
| Impacto social | 19 | 8 | 6 | 5 | 0 |
| Gestión | 14 | 7 | 5 | 2 | 0 |
| **Total definitivo** | **69** | **27** | **25** | **17** | **0** |

## 1. Capacidad prestable (IdC)

### Reconciliación del aparente 82,9% versus 67%

El dato de CIGOB usa saldos de fin de mes del sector privado:

`$103.375.772 M de préstamos privados / $124.667.259 M de depósitos privados = 82,921%`.

La holgura `1 − ratio` es **17,079%**, que reproduce el 17,1% del IdC. Las variables 117 y 100 del BCRA pertenecen al sector privado no financiero.

El 67% de Criteria proviene de otro universo. La planilla mensual del BCRA informa promedios de $102.663.784,903 M de préstamos **totales al sector no financiero** y $152.696.766,806 M de depósitos **totales del sector no financiero**:

`102.663.784,903 / 152.696.766,806 = 67,234%`.

Al comparar promedio privado con promedio privado, el resultado es **83,559%**. La diferencia de aproximadamente 16 puntos no surge de punta frente a promedio: se explica por incorporar unos $31 billones de depósitos públicos al denominador total y menos de $1 billón de préstamos no privados al numerador. El IPOM del BCRA publica además cerca de 83,6% para la relación privada en pesos, prácticamente igual a CIGOB.

**Veredicto:** **Compatible, confianza alta**. El −0,32σ continúa siendo un índice CIGOB sin homónimo externo, pero el componente discutido quedó reconciliado y la escala está corroborada.

**Límite conceptual:** el BCRA define capacidad prestable descontando la integración de efectivo mínimo de los depósitos totales. `1 − préstamos privados/depósitos privados` mide margen de fondeo o intensidad de intermediación, no fondos legalmente disponibles para prestar. La corrección mínima es renombrar; el rediseño estricto debe incorporar encajes.

Fuentes: [BCRA — variable 117, préstamos privados](https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/117?Desde=2026-07-31&Hasta=2026-07-31), [BCRA — variable 100, depósitos privados](https://api.bcra.gob.ar/estadisticas/v4.0/Monetarias/100?Desde=2026-07-31&Hasta=2026-07-31), [planilla monetaria de julio](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/indicadores-informe-monetario-mensual-2026-07.xlsx), [Criteria — ratio de julio](https://criteria.com.ar/informes-monetarios-mensuales/informe-monetario-bcra-julio-2026-que-paso-con-la-base-monetaria-el-credito-y-las-reservas/), [BCRA — IPOM segundo trimestre](https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/informes/informe-politica-monetaria-2026-T2.pdf).

## 2. Conflictividad social nacional (ACLED)

### Nueva extracción y réplica

El snapshot se reproduce desde la serie derivada y versionada:

`1.978 / 2.605 − 1 = −24,0691%`, que redondea a **−24,1%**.

Se descargó lícitamente, con las credenciales académicas ya configuradas y sin eludir controles, la edición de ACLED de la semana siguiente, corte 15-08-2026. Bajo los mismos filtros produjo:

- base 2023: `Protests 2.421 + Riots 184 = 2.605`, sin revisión;
- ventana agosto de 2025-julio de 2026: `Protests 1.858 + Riots 121 = 1.979`;
- resultado actualizado: `1.979 / 2.605 − 1 = −24,0307%`, que redondea a **−24,0%**;
- 24 jurisdicciones presentes;
- revisión localizada: julio de 2026 pasó de 89 a 90 eventos; agosto parcial pasó de 82 a 114 y se excluyó correctamente.

El archivo de control tuvo SHA-256 `6d44a38ef359e243d2e7c93ce5c4ff7b267a553f6aa73feb55d31eef53d55189`. Sus 1.979 eventos se reconcilian también por subtipo: 1.804 protestas pacíficas, 53 con intervención, 1 con fuerza excesiva, 105 manifestaciones violentas y 16 episodios de violencia de turba.

**Veredicto:** **Compatible, confianza alta**. La diferencia de un evento —0,05% del numerador— es una revisión normal de una base viva, no un error material del tablero. No se lo llama confirmado porque ambas extracciones provienen del mismo productor.

**Hallazgo temporal:** las filas de ACLED están agregadas por semanas sábado-viernes y el código atribuye todo el bloque al mes del sábado inicial. Las comparaciones son ventanas homogéneas de 52 semanas, pero no meses calendario estrictos. El rótulo y la documentación deben decirlo.

**Condición operativa:** conservar internamente URL, fecha/hora, tamaño y hash del XLSX bajo la licencia aplicable; publicar un manifiesto no reversible con filtros, 24 jurisdicciones, tipos/subtipos, filas y sumas. Si el siguiente cierre no puede generar ese paquete, suspender el indicador hasta recuperar trazabilidad.

Fuentes: [ACLED — guía de datos agregados](https://acleddata.com/use-access/how-use-acleds-aggregated-data), [ACLED — codebook](https://acleddata.com/methodology/acled-codebook), [ACLED — política de atribución](https://acleddata.com/attributionpolicy), [ACLED — EULA](https://acleddata.com/eula), [FLACSO — conflictividad durante el segundo año](https://politicaspublicas.flacso.org.ar/wp-content/uploads/2026/03/Informe-No-49_-La-conflictividad-social-durante-el-segundo-ano-del-gobierno-de-Javier-Milei-OPPRE-FLACSO-Argentina.pdf).

## 3. Sentimiento digital

### La tubería funciona; la interpretación no

El 58,2 queda confirmado como aritmética: cada término se rebasa contra su propio 4T-2023 y los seis índices se promedian con igual peso. Cinco capturas entre el 21 y el 25 de agosto promediaron **58,055**, con desvío 0,284 y coeficiente de variación 0,49%. La inestabilidad de muestreo reciente es pequeña y no explica el problema.

La canasta de seis términos nació cuatro días antes del corte y reconstruyó hacia atrás 67 meses con una consulta actual; no son 67 vintages históricos. Además, la validación del diseño anterior —otra canasta y otra forma de consulta— no puede heredarse automáticamente.

### Validación externa adversa

Con diez ondas argentinas de *What Worries the World* de Ipsos, rebasando encuesta y Trends a diciembre de 2023=100 para inflación, desempleo/empleo, crimen/inseguridad y corrupción:

- correlación en niveles posteriores a la base: **r = −0,788**, cuando debía ser positiva;
- correlación de cambios: **r = −0,542**;
- sólo **3 de 9** movimientos compartieron dirección;
- en julio de 2026, Ipsos dio 103,3 y Trends 79,6.

Contra confianza del consumidor, donde se esperaba signo negativo:

- Ipsos diciembre de 2025-julio de 2026: **r = +0,216** en niveles y +0,061 en cambios;
- ICC UTDT, 59 meses: **r = −0,126** en niveles y +0,082 en cambios;
- la ventana favorable de 18 meses citada por el diseño anterior fue la mejor de 42 ventanas: 34 de las 42 tuvieron el signo opuesto y la mediana fue +0,194.

Contra inflación del INDEC la correlación completa fue +0,655, pero cayó a **−0,119** en los últimos 18 meses. Es una relación de régimen dominada por la aceleración 2022-2023, no una validación estable de sentimiento.

**Veredicto:** **Discrepante, confianza alta** como indicador de sentimiento o urgencia puntuable. El volumen de búsquedas mide atención y saliencia; no aporta por sí mismo dirección positiva/negativa. `empleo`, por ejemplo, puede reflejar búsqueda de vacantes mientras las encuestas preguntan preocupación por desempleo.

**Decisión:** retirarlo temporalmente del ITCIS. Puede conservarse como card contextual llamada **“Atención de búsquedas en seis términos”**, mostrando el desglose, sin inversión, semáforo ni lectura de bienestar. Para volver a puntuar debe predeclarar términos/topics, congelar múltiples vintages, definir una encuesta objetivo y superar validación temporal fuera de muestra.

Fuentes: [Google Trends — muestreo y normalización](https://support.google.com/trends/answer/4365533?hl=es), [Google — términos frente a temas](https://support.google.com/trends/answer/17309543?hl=es), [API oficial de Trends en alfa](https://developers.google.com/search/apis/trends), [Hölzl et al. — revisión de 360 estudios](https://madoc.bib.uni-mannheim.de/68637/1/1-s2.0-S0049089X24001212-main.pdf), [Ipsos Argentina — julio de 2026](https://www.ipsos.com/es-ar/argentina-2026-mejora-la-percepcion-economica-pero-el-empleo-gana-centralidad), [El País — sondeos sobre empleo y salarios](https://elpais.com/argentina/2026-08-21/los-salarios-y-el-empleo-son-las-nuevas-preocupaciones-de-los-argentinos-segun-los-sondeos.html).

## Conclusión final

Después de tres rondas no queda ningún indicador en la categoría «No verificable independientemente». Esto no convierte al tablero en validado sin observaciones: quedan **17 discrepancias**, algunas numéricas y otras de universo o constructo. El tercer barrido aporta tres decisiones concretas:

1. **IdC:** mantener y renombrar/rediseñar.
2. **ACLED:** mantener con trazabilidad reforzada y unidad temporal corregida.
3. **Sentimiento digital:** retirar del score y conservar sólo como atención descriptiva hasta una validación prospectiva.

## Expedientes detallados

- [Macro — tercer barrido del IdC](260825_macro.md#tercer-barrido--capacidad-prestable-idc)
- [Política — tercer barrido de ACLED](260825_politica.md#tercer-barrido--conflictividad-social-nacional-acled)
- [Impacto social — tercer barrido de sentimiento](260825_impacto_social.md#tercer-barrido--sentimiento-digital)

Este barrido modifica veredictos de auditoría, no código, colectores, fórmulas ni snapshots. Las correcciones de producto requieren una implementación separada con regeneración y pruebas.
