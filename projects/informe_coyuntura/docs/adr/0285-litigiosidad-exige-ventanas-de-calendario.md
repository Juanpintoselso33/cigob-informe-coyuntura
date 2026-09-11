---
madr: 4
id: '0285'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'gestion'
indicadores: [litigiosidad_laboral]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
ambito: 'Ventanas y alcance de la litigiosidad SRT'
origen: 'Auditoría integral solicitada por Juan'
---

# ADR-0285 — Litigiosidad exige ventanas de calendario

## Contexto y planteo del problema

Tomar las últimas 24 observaciones comprimía huecos: un mes faltante podía
reemplazarse silenciosamente por otro más antiguo. La tarjeta y su serie
duplicaban ese cálculo. La ficha además presentaba el indicador como resultado
del Fondo de Asistencia Laboral, aunque mide juicios de riesgos del trabajo.

## Decisión

Compartir el cálculo de dos períodos móviles de doce meses consecutivos.
Rechazar huecos, valores no finitos o negativos y denominador cero. Un cero
observado sigue siendo válido. La tarjeta falla al respaldo si su última
ventana es incompleta; la historia omite las ventanas sin cálculo válido.

Conservar bandas y pesos. Explicitar que la serie SRT no identifica el efecto
del FAL ni el mérito de los reclamos; revisar el constructo se registra aparte.

## Más información

La vigencia se contrasta con la sección de últimos datos SRT. No se compara la
variación de un mes aislado con el cociente móvil de 12 meses del monitor.
