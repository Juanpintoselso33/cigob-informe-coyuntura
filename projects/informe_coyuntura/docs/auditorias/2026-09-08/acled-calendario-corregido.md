# Protestas ACLED: corte y agrupación mensual

La [metodología de ACLED](https://acleddata.com/use-access/how-use-acleds-aggregated-data) define `week` como el sábado inicial de una semana sábado–viernes. El monitor lo interpretaba como cierre. El archivo hasta la semana del 29 de agosto de 2026 cubre el 4 de septiembre, por lo que agosto ya tiene todas sus semanas. El [calendario de actualización](https://acleddata.com/use-access/when-are-acled-data-updated) sitúa las entregas latinoamericanas los lunes.

Se descargó el original mediante el acceso autenticado existente y se cotejó por separado del colector. El archivo contiene 6.919 filas argentinas de protestas y disturbios; todas tienen un sábado como referencia. La base de grupos de 2023 suma 2.605 eventos; septiembre de 2025–agosto de 2026 suma 1.977: **−24,1%**. CABA suma 240 y 280 respectivamente, **+16,7%**; es contexto y no puntúa como cortes de calle.

La [evidencia](cotejo-acled-calendario.json) conserva la URL, el SHA-256 del original, el recuento independiente, la serie y los resultados de tarjeta. No conserva credenciales. El original tiene SHA-256 `37bf793ad8586806c2eddb3cb0dfc1735333646fea94becf002f04dde38c3155`.

La agrupación mensual conserva el mes del sábado inicial, incluso cuando la semana cruza un mes o un año. Son doce grupos mensuales completos, no doce meses reconstruidos por fecha diaria del evento. Esa limitación se explicita en ficha y tarjeta; no se inventa una distribución diaria. Se exige calendario consecutivo y base completa. El corte se obtiene de todo el archivo regional, evitando confundir una semana sin protestas argentinas con una semana sin cobertura.

La historia política incorpora agosto. Tras integrar también las correcciones posteriores de sesiones y sanciones (ADR-0308), pasa de **67,8 en julio a 68,2 en agosto**, con los mismos componentes disponibles. ACLED recupera conflicto social; cinco sanciones omitidas aportan la revisión legislativa posterior. El ICG sube de 1,94 a 2,06, coincidencia de dirección que no acredita identidad de constructos. ITCP de portada: 71,9; combina últimos datos y no equivale al cierre retrospectivo de agosto.

El colector también conserva el sello del archivo y lo marca desactualizado cuando falla la consulta. La ficha, la serie, el contraste y los manuales fueron regenerados bajo [ADR-0303](../../adr/0303-acled-semana-inicia-el-sabado.md).
