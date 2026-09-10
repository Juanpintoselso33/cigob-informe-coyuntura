# Calendario del contraste externo

Se corrigieron `_difs` y `_lag` en `scripts/validacion_externa.py`: antes restaban o desplazaban filas ordenadas. Con enero y marzo, una diferencia de dos meses podía rotularse mensual y el adelanto de enero podía aterrizar en marzo. Ahora las diferencias exigen el mes inmediatamente anterior y los desplazamientos usan meses calendario. No se imputan los meses faltantes; los extremos desplazados se conservan y la correlación toma la intersección de fechas.

Validación: 14 pruebas dirigidas aprobadas (0,23 s), incluidas tres regresiones de huecos, cruce de año, conservación del extremo y desplazamiento negativo/cero. Sobre las nueve series numéricas mensuales del resultado guardado, todas las diferencias permanecen idénticas. Las cinco correlaciones con adelantos ITCM/Líder e ITCP/EPU conservan exactamente r y n. Las series actuales no presentan huecos internos; el defecto afectaba la interpretación cuando los hubiera.

Sin cambios de datos, índices o resultados publicados. No se ejecutó el pipeline de fuentes ni build web. `git diff --check` sin errores. La tabla estadística del informe coincide con las correlaciones guardadas para ITCM/Líder e ITCP/EPU; el cotejo general continúa y no se presenta como prueba causal o predictiva.
