# Coherencia de portada y gráficos

8 de septiembre de 2026. Correcciones locales, sin cambios de datos ni despliegue.

La síntesis automática usaba el estado sistémico de tres categorías para describir las cuatro bandas de las tarjetas. Ahora aplica `colorPorTension` y `LECTURA_SEMAFORO`, como las barras: macro 3,6 sin tensión relevante e impacto social 6,4 tensión alta. Se conserva la selección de editorial del mes cuando existe.

El marco de impacto social describe condiciones materiales y percepciones; ya no afirma medir validación electoral. La síntesis metodológica del ITCIS refiere las referencias de cada componente, evitando atribuir a todos una base 4T-2023 uniforme.

Los gráficos prometían eje común 0–10, pero ApexCharts autoajustaba cada serie. `sparkChart` acepta rango opcional, aplicado únicamente a los gráficos `__tension_`; las otras series conservan su escala automática.

## Verificación

- Build: 81 páginas, 1,36 s.
- 18 pruebas de semáforos aprobadas. Única advertencia: pytest no pudo escribir su caché dentro del sandbox; no afectó la ejecución.
- `codex review` acotado al parser Diputados, sensibilidad y estos cinco archivos web: sin regresiones concretas; dos pruebas focalizadas del parser y redondeo aprobadas. La revisión web fue estática; el build y navegador se verificaron aparte.
- Navegador Playwright local: cuatro SVG completos, 32/32/33/32 puntos, curvas no planas y cero errores JavaScript. [Captura estable](portada-graficos-verificados.png) y [geometría renderizada](portada-graficos-verificados.json).
- Se leyeron los tres mosaicos de la portada completa. PixelBrowse puede capturar las curvas durante su animación y mostrarlas planas; la espera explícita de 1,5 segundos después de aparecer los SVG confirma que no era pérdida de datos. La captura con ancla tuvo un mosaico vacío y no se usa como prueba completa.
- `git diff --check` sin errores; avisos CRLF en archivos preexistentes.

Quedan por revisar la prosa histórica de bloqueo, el alcance de la descripción de controles y los pendientes de fuentes judiciales/FAL/privatizaciones. No constituye cierre integral de la auditoría.
