# Senado: una lectura incompleta no actualiza el promedio

Los colectores vigentes de cohesión y alineamiento omitían actas cuya descarga
fallaba y podían publicar un promedio parcial como actualización exitosa.
Ahora una descarga fallida o un HTML sin filas de votos devuelve fallo; el
flujo existente conserva el dato anterior y aplica su regla de antigüedad,
sin renovar artificialmente la fecha de lectura exitosa. También se excluyen
actas futuras de las tarjetas. Los descargadores anuales rechazan igualmente
el HTML sin votos, para no almacenar como completo un año con agujeros.

Se distingue fallo de ausencia de señal: un acta leída con votos pero sin
posición definida de LLA puede no aportar al promedio según el método.
No cambian fórmulas ni conservación por receso.

Ocho pruebas nuevas cubren red, HTML vacío, fechas futuras y año incompleto.
La selección final con las suites existentes de cohesión y reconstrucción:
**148 aprobadas en 1,93 s**. La primera selección había aprobado 122.

No se ha demostrado que el promedio publicado al corte sea incorrecto:
su comprobación nominal independiente sigue pendiente. No se cambian series
con datos sintéticos. Las salvedades de acceso a Diputados siguen abiertas;
la dirección alternativa `votaciones.hcdn.gov.ar` también terminó con fallo
de conexión (curl 35, HTTP 000), no con ausencia del acta 5960.
