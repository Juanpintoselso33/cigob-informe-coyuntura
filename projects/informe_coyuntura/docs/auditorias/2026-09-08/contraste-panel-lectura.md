# Lectura del panel externo

Se corrigió `panel_validacion.lectura`: los promedios son de correlaciones en valor absoluto, por lo que no indican dirección común. Una brecha positiva en diferencias no significa que se mantenga la separación de niveles: en los resultados actuales, ITCIS e ITCP tienen brecha negativa en niveles y positiva en diferencias. Se retiraron también las garantías de eliminación de tendencia y se explicita el alcance descriptivo, sin prueba de significación, causalidad o predicción.

El README invierte la dirección del aporte de R²: se corrigió para aclarar que el ITCIS agrega 0,056 al modelo de tendencia que explica el factor social dentro de la muestra. No es el factor el que se agrega para explicar el ITCIS.

25 pruebas del panel aprobadas; lectura propagada mediante publicar.py y verificada en los tres cinturones; build 81 páginas correcto. Censo regenerado. No se recalcularon datos ni correlaciones. El JSON intermedio de validación conserva su lectura de corrida; publicar.py la reconstruye desde los resultados numéricos y el texto vigente.

Se detectó además que panel_validacion._difs y factores externos mantienen cálculo por filas, y la regresión usa posiciones como tendencia temporal. Revisar el efecto de meses faltantes en esas rutas antes del cierre; todavía no corregidas en esta etapa.
