# Calendario en factores, panel y regresión

Se extendió la corrección a factor_comun._difs; panel_validacion reutiliza esa función. Sólo se restan meses calendario consecutivos, sin imputación. La tendencia temporal de regresion_validacion usa meses transcurridos desde el primero, no el número de observación; un hueco ya no comprime el tiempo.

57 pruebas dirigidas aprobadas (0,12 s), incluyendo huecos compartidos por panel/factor y una tendencia calendario perfecta observada de manera irregular. Con los pares del factor conservados, las regresiones actuales se reproducen exactamente: aporte 0,056 social y 0,018 gestión.

Las series completas de las anclas del panel no se persisten en el resultado actual. Por tanto falta reconstruir sus insumos para comprobar el efecto sobre todas las correlaciones del panel. No se afirma que esos resultados estén recalculados ni que todas las diferencias sean iguales. No se modificaron salidas de datos ni se ejecutó el pipeline de fuentes en esta etapa.
