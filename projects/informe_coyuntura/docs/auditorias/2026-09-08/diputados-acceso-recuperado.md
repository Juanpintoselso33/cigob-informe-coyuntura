# Diputados: acceso recuperado y defecto de extracción

El 8-sep-2026 el navegador pudo abrir el listado oficial, con actas hasta
5995 del 27-ago. Una solicitud nativa `requests.get` al PDF respondió 200.
El ID 5960 devuelve 404 con «Acta no existe»: es un hueco, no prueba de
indisponibilidad. El ID 5996 también respondió 404. No se dedujo de ese
primer hueco que terminara el inventario: el máximo 5995 se observó en
el listado real.

La captura del walk vigente con ese máximo y una copia temporal del
caché terminó sin fallos: 42 actas con señal de LLA, última 27-ago,
Rice provisional 100%. La tarjeta todavía conserva 13 actas anteriores;
no se modificaron sus datos ni el caché productivo en esta etapa.

## Error observado que debe corregirse antes de integrar

La extracción independiente con `pdftotext -layout` del acta 5995 permitió
comparar el encabezado oficial con el parser: 220 afirmativos y 36
ausentes, más presidente sin votar. El parser devuelve 217 afirmativos y
36 ausentes. Omite Bregman, Del Caño y Del Pla porque el nombre largo de
su bloque deja una separación horizontal menor al umbral fijo antes de
la provincia. Son filas presentes en el PDF, no datos ausentes de fuente.

Corregir la separación de columnas con posiciones observadas de filas
válidas, agregar una regresión y comparar todas las actas nuevas. No
cambiar la definición de Rice ni incluir al presidente sin voto. Después,
integrar caché y tarjeta, completar clasificación de bloqueo/desafíos y
actualizar series cuando corresponda. Revisar que el descubridor pueda
usar el listado ahora accesible; cualquier rediseño debe conservar el
respaldo ante huecos, sin confundir primer 404 con máximo.

[Capturas y resultado provisional](cotejo-diputados-acceso-recuperado.json).
PDFs y caché provisional: `/tmp/cigob-diputados-actual`. No repetir las
descargas ya guardadas para probar el parser corregido.
