# Auditoría externa completa de indicadores

**Fecha de corte:** 25 de agosto de 2026
**Snapshot auditado:** `web/src/data/informe.json`
**Cobertura:** 69 de 69 indicadores publicados
**Cinturones:** Macroeconomía, Política, Impacto social y Gestión

> **Actualización final — tercer barrido:** los tres casos residuales también fueron cerrados. El balance definitivo es **27 confirmados, 25 compatibles, 17 discrepantes y 0 no verificables**. Ver [segundo barrido de los 15](260825_segundo_barrido_15.md) y [tercer barrido de los tres residuales](260825_tercer_barrido_3.md).

## Resultado global de la primera ronda

| Cinturón | Indicadores | Confirmados | Compatibles | Discrepantes | No verificables independientemente |
|---|---:|---:|---:|---:|---:|
| Macroeconomía | 17 | 6 | 3 | 2 | 6 |
| Política | 19 | 4 | 7 | 2 | 6 |
| Impacto social | 19 | 8 | 5 | 4 | 2 |
| Gestión | 14 | 7 | 5 | 1 | 1 |
| **Total** | **69** | **25** | **20** | **9** | **15** |

Los 25 confirmados coinciden en cifra, período, unidad y definición dentro del redondeo. Los 20 compatibles tienen evidencia externa favorable, pero no el mismo universo o cálculo. Los 15 no verificables no se presumen falsos: carecen de un benchmark independiente equivalente o no publican insumos suficientes. Los 9 discrepantes requieren corrección, redefinición o conciliación explícita.

## Método común

1. Se congeló como objeto de auditoría lo que veía el usuario en el snapshot del 25-08-2026, no una corrida posterior.
2. Para cada card se comprobó cifra, período, unidad, cobertura geográfica, universo y transformación.
3. La fuente oficial original funcionó como control primario, pero no bastó por sí sola para afirmar independencia.
4. Se buscaron comparables en universidades, centros de investigación, observatorios, consultoras y prensa seria con cifras trazables.
5. En índices CIGOB se reprodujeron fórmula e insumos. La aritmética correcta no se confundió con validación externa del constructo.
6. Las noticias que sólo copiaban un comunicado se usaron para controlar transcripción, no como una segunda medición.

Tavily devolvió límite de cuota `432`; el barrido se completó con búsqueda web integrada y descargas públicas. Esa contingencia no redujo cobertura.

## Las nueve discrepancias

| Prioridad | Cinturón | Indicador | Problema comprobado | Acción |
|---:|---|---|---|---|
| 1 | Gestión | Concesiones viales | Publica 28,7% y Etapa III no adjudicada, pero la Resolución 1379/2026 adjudicó formalmente sus ocho tramos antes del corte | Sumar más de 3.900 km; con el denominador actual pasa como mínimo a ~71,6% |
| 2 | Impacto social | Supermercados | Conserva may-2026 = 83,2 y base 2004; al corte ya existía jun-2026 = 82,1, mayo revisado = 83,0 y base 2017 | Redescargar serie, corregir unidad y recalcular ITCIS |
| 3 | Macro | Costo real del Tesoro | Usa TIREA 32,17%; la LECAP comparable publicó 28,32% | Sustituir TIREA y recalcular: ~4,92% real, no 8,07%; reauditar historia |
| 4 | Impacto social | ICC | Publica 39,9 como nacional; 39,87 es CABA y el nacional es 40,23 | Leer la columna nacional y reconstruir su base |
| 5 | Política | Cobertura judicial | Publica 69,63% pero explica 604/955, que es 63,25% | Conciliar cortes; si 69,63% es correcto, publicar numerador actualizado (~665/955) |
| 6 | Política | Transferencias federales reales | Publica +0,8%; IARAF y Politikon estiman +1,6/+1,7% para el mismo agregado anual | Deflactar mes a mes y documentar IPC/ponderación |
| 7 | Macro | Crédito privado real | +2,5% es válido para variable 26 en pesos equivalentes, pero incorpora revaluación del crédito en USD y no representa crédito en pesos | Separar universos o neutralizar efecto cambiario; relabelar |
| 8 | Impacto social | Trabajo independiente | Excluye monotributo social aunque el rótulo dice porcentaje del empleo registrado SIPA | Incluirlo o declarar un denominador restringido y reconstruir la base |
| 9 | Impacto social | Subocupación demandante | El 7,5% es correcto, pero es porcentaje de la PEA, no de los ocupados; `pluriempleo` es otro concepto | Corregir definición e identificador; revisar textos y metadatos |

## Orden de intervención recomendado

### Inmediato — dato publicado incorrecto o vencido

1. Concesiones viales.
2. Supermercados.
3. Costo real del Tesoro.
4. ICC nacional.
5. Cobertura judicial.

### Metodológico — cifra dependiente del universo

6. Transferencias federales reales.
7. Crédito privado real.
8. Trabajo independiente.
9. Subocupación demandante.

### Transparencia — no son discrepancias probadas, pero impiden auditoría plena

- Política: no puntuar postura empresaria con 14 comunicados pendientes; publicar inventarios de DNU, leyes, proyectos, sesiones y matrices de votación; renombrar “judicialización de la agenda”, porque hoy mide menciones cautelares en todo SAIJ.
- Macro: identificar las reservas como convención CIGOB y mostrar rangos privados; publicar insumos y z-scores del IdC; reconciliar TCRM 85,47 vs 85,87; exponer planillas de los índices compuestos.
- Impacto social: congelar artefactos y parámetros de Google Trends; publicar muestra e intervalo del IVI; explicitar universos AMBA/EPH/SIPA/SRT; retirar identificadores legados `despacho_cemento` y `pluriempleo`.
- Gestión: publicar las 11 altas y justificar la meta 45 de reestructuración; no equiparar sin advertencia la partida presupuestaria 5.1.4 con ausencia total de intermediación operativa; exponer el tipo de cambio de apertura comercial.

## Expedientes por cinturón

- [Macroeconomía — 17/17](260825_macro.md)
- [Política — 19/19](260825_politica.md)
- [Impacto social — 19/19](260825_impacto_social.md)
- [Gestión — 14/14](260825_gestion.md)

Cada expediente contiene la matriz completa, evidencia detallada, enlaces directos, confianza y acción recomendada por indicador.

## Qué no concluye esta auditoría

- “No verificable independientemente” no significa “incorrecto”. Significa que un tercero no puede reproducir el decimal con lo publicado o que no existe una medición externa equivalente.
- “Compatible” no significa confirmado. Puede compartir tendencia y magnitud con un comparable que usa otro universo.
- La auditoría valida datos y definiciones del snapshot; no valida automáticamente pesos, bandas, colores ni la teoría causal de cada índice.
- Corregir una card exige después regenerar el índice, el informe, las series y el snapshot web para medir el efecto agregado. Esa implementación no forma parte de este barrido.
