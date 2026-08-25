# Segundo barrido de los 15 indicadores sin verificación independiente

**Fecha de corte:** 25 de agosto de 2026
**Snapshot auditado:** `web/src/data/informe.json`
**Alcance:** los 15 indicadores que quedaron como «No verificable independientemente» en la primera auditoría de 69 indicadores.

> **Actualización — tercer barrido:** los tres bloqueos residuales fueron cerrados: IdC y ACLED pasan a compatibles; Sentimiento digital pasa a discrepante. El balance definitivo es **27 confirmados, 25 compatibles, 17 discrepantes y 0 no verificables**. Ver [tercer barrido de los tres](260825_tercer_barrido_3.md).

## Resultado ejecutivo

La investigación adicional cerró **12 de los 15 expedientes**:

| Reclasificación de los 15 | Cantidad |
|---|---:|
| Confirmados | 2 |
| Compatibles | 3 |
| Discrepantes | 7 |
| Siguen sin verificación independiente | 3 |
| **Total** | **15** |

Aplicando las revisiones al universo completo, el tablero pasa de **25 confirmados, 20 compatibles, 9 discrepantes y 15 no verificables** a:

| Cinturón | Indicadores | Confirmados | Compatibles | Discrepantes | No verificables |
|---|---:|---:|---:|---:|---:|
| Macro | 17 | 6 | 5 | 5 | 1 |
| Política | 19 | 6 | 7 | 5 | 1 |
| Impacto social | 19 | 8 | 6 | 4 | 1 |
| Gestión | 14 | 7 | 5 | 2 | 0 |
| **Total revisado** | **69** | **27** | **23** | **16** | **3** |

«Discrepante» no significa necesariamente que la división esté mal hecha. En cinco de los siete casos nuevos, la cuenta local se reproduce, pero el nombre o interpretación atribuye a los insumos un fenómeno que no identifican.

## Matriz de los 15 casos

| # | Cinturón | Indicador | Primera ronda | Segundo barrido | Evidencia decisiva | Acción |
|---:|---|---|---|---|---|---|
| 1 | Macro | Capacidad prestable (IdC) | No verificable | **No verificable**, confianza media | El −0,32σ se reproduce, pero CIGOB obtiene préstamos/depósitos de 82,9% y Criteria 67%; no se publican universos comparables | Publicar saldos, medias, desvíos y conciliar ambos universos |
| 2 | Macro | Base imponible real | No verificable | **Compatible**, confianza media | El 88,2 se reconstruye con DGI+COMARB; CEPA e IARAF confirman la contracción real, aunque no el mismo empalme | Publicar serie combinada y factores estacionales |
| 3 | Macro | Exceso de pesos sobre demanda (IDM) | No verificable | **Discrepante**, confianza media-alta | 4,73 pp es la brecha de crecimiento real M3−M2; no compara oferta efectiva con una demanda monetaria estimada | Renombrar como brecha M3−M2 o modelar demanda de dinero |
| 4 | Macro | Dolarización dentro y fuera del sistema | No verificable | **Discrepante**, confianza alta | El 50,86 se reproduce, pero la compra neta de dólares no identifica fondos fuera del sistema; BCRA estima que cerca de 80% queda depositado localmente | Renombrar el flujo o reemplazarlo por activos externos fuera del sistema |
| 5 | Macro | Capitalización digital (ICIP) | No verificable | **Discrepante**, confianza alta | El 8,36% se reproduce; pagos externos por informática/nube suelen ser consumo intermedio y no formación de capital | Usar inversión en software, bases y equipos TIC o cambiar el constructo |
| 6 | Macro | Resultado primario / recaudación | No verificable | **Compatible**, confianza alta | $11,4057 / $205,6663 billones = 5,54575%; IIEP y OPC confirman signo y magnitud fiscal con otro denominador | Mostrar numerador y denominador de doce meses |
| 7 | Política | Ratio DNU / leyes | No verificable | **Discrepante**, confianza alta | De 48 coincidencias textuales, sólo 37 están tipificadas como DNU; 25 son leyes publicadas y 22 sancionadas. El ratio es 1,48 o 1,68, no 1,92 | Filtrar por subtipo DNU y homogeneizar la fecha jurídica |
| 8 | Política | Postura pública de AEA y UIA | No verificable | **Discrepante**, confianza alta | El −0,429 cierra sobre siete textos, pero había 14 pendientes, incluidos apoyos y críticas sustantivos | Suspender hasta cerrar y publicar el corpus completo |
| 9 | Política | Conflictividad social nacional | No verificable | **No verificable**, confianza media-baja | 1.978/2.605 y −24,1% son coherentes con ACLED, pero el XLSX fechado devuelve 404 y la descarga exige sesión | Versionar XLSX, hash, filtros y sumas mensuales |
| 10 | Política | Eficacia legislativa del Ejecutivo | No verificable | **Confirmado**, confianza alta | La cohorte pública contiene 13 expedientes PE/JGM y sólo dos llegaron a las leyes 27.783 y 27.799: 2/13=15,4% | Publicar las 13 filas para trazabilidad |
| 11 | Política | Judicialización de la agenda | No verificable | **Discrepante**, confianza alta en definición | 114/7.273 mide menciones de «medida cautelar» en sumarios SAIJ heterogéneos, no causas contra políticas del PEN | Renombrar o construir un universo de causas contra el Ejecutivo |
| 12 | Política | Actividad de comisiones de control | No verificable | **Confirmado**, confianza alta | Se identificaron cuatro sesiones numeradas de Acusación y tres de Disciplina, sin huecos: total 7 | Publicar las siete convocatorias; no inferir productividad sustantiva |
| 13 | Impacto social | Victimización IVI | No verificable | **Compatible**, confianza media | IVI informa 28,0% con n=996; antecedentes nacionales independientes dieron 26,4% (UCA) y 27,5% (INDEC) | Publicar muestra, intervalo, microdatos/ponderadores y base del rebase |
| 14 | Impacto social | Sentimiento digital | No verificable | **No verificable**, confianza baja | El artefacto reproduce 58,2, pero una reconsulta dio 57,3 y el proxy Ipsos diverge fuertemente, sobre todo en empleo | Renombrar, congelar extracciones repetidas y validar contra encuestas |
| 15 | Gestión | Reestructuración de organismos | No verificable | **Discrepante**, confianza alta | 11 cuenta normas que cierran unas 18 entidades; 45 es una convención de documentos y la consulta omite cierres presentes en padrones externos | Sacar del índice hasta definir numerador y denominador homogéneos |

## Los tres bloqueos residuales al cierre de la segunda ronda

### 1. Capacidad prestable (IdC)

No falta el cálculo CIGOB: está íntegramente reproducido. Falta una publicación externa que use exactamente préstamos privados en pesos, depósitos privados en pesos, fecha de punta y la misma ventana de estandarización. El benchmark disponible informa 67%, contra 82,9% local, sin saldos que permitan reconciliar universos. Hasta entonces debe presentarse como **IdC CIGOB**, con sus insumos visibles.

### 2. Conflictividad social nacional

El resultado depende de un archivo ACLED versionado que ya no está disponible por URL pública y cuya descarga actual exige sesión. Para cerrarlo se necesita preservar el XLSX exacto, hash, fecha de extracción, filtros `Argentina × Protests/Riots`, reglas de deduplicación y las sumas mensuales. La evidencia pública sostiene el orden de magnitud, no los totales 1.978 y 2.605.

### 3. Sentimiento digital

La aritmética del snapshot está confirmada, pero Google Trends usa muestras normalizadas y el indicador no ha demostrado que seis términos exactos con igual peso midan un constructo común de «sentimiento». Para validarlo hacen falta extracciones repetidas, mediana e incertidumbre, pruebas con términos/temas y validación fuera de muestra contra encuestas contemporáneas. Hasta entonces el nombre defendible es **atención de búsqueda en seis términos**, no sentimiento.

## Correcciones prioritarias surgidas de esta ronda

1. Corregir el ratio DNU/leyes: usar 37 DNU y una fecha jurídica homogénea.
2. Suspender postura AEA/UIA hasta resolver los 14 casos pendientes.
3. Retirar o rediseñar reestructuración de organismos: el 24,4% no tiene unidad homogénea.
4. Renombrar o reconstruir judicialización, IDM, dolarización e ICIP; hoy interpretan más de lo que miden.
5. Incorporar los dos indicadores confirmados —eficacia legislativa y sesiones de control— con sus inventarios públicos.

## Expedientes detallados

- [Macro — segundo barrido de seis casos](260825_macro.md#segundo-barrido--los-seis-casos-inicialmente-no-verificables)
- [Política — segundo barrido de seis casos](260825_politica.md#segundo-barrido-de-los-seis-casos-inicialmente-no-verificables)
- [Impacto social — segundo barrido de dos casos](260825_impacto_social.md#segundo-barrido-de-los-indicadores-no-verificables)
- [Gestión — segundo barrido de un caso](260825_gestion.md#segundo-barrido-de-los-casos-no-verificables)

## Alcance de la conclusión

Este segundo barrido no modificó colectores, fórmulas, snapshots ni valores publicados. Reclasificó evidencia. Cuando una fuente periodística replica una fuente oficial, se utilizó para controlar cifra y contexto, no como independencia estadística plena. Las correcciones de producto deben hacerse en una tarea separada, con regeneración y pruebas del informe.
