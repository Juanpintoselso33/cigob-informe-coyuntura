---
madr: 4
id: '0299'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [ipi_manufacturero, iai, despacho_cemento]
archivos: ['scripts/indec_actividad.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'scripts/vida_cotidiana/collectors/indec_series.py', 'web/src/lib/fichas.ts']
ambito: 'Actualización compartida de industria y construcción'
---

# ADR-0299 — Actividad usa las planillas originales vigentes

El 8 de septiembre INDEC publicó julio de IPI e ISAC, con revisiones anteriores.
Las API seguían en junio: no sólo faltaba un mes, también diferían los niveles
revisados. Agregar un punto manual habría dejado versiones incompatibles.

Un lector compartido descubre las planillas anuales desde la página oficial de
cada operación. Valida el cuadro, base, variantes, niveles positivos y calendario
mensual consecutivo cerrado. Conserva precisión completa. Macro, historia y
colector social resuelven los cuatro identificadores de IPI/ISAC a este lector.
El archivo se descarga una vez por operación y proceso. Un fallo se propaga al
tratamiento de caché del colector; no vuelve silenciosamente a la API atrasada.

IPI conserva su promedio de tres variaciones interanuales; ISAC social conserva
el nivel desestacionalizado y su base 4T-2023; IAI conserva la intersección mensual
con bienes de capital. La revisión también alcanza el ICIP informativo, fuera
del índice, por su componente industrial. No cambian pesos ni anclas.

Se corrige el rezago declarado: la publicación del IPI ocurre al inicio del
segundo mes posterior y antes del EMAE del mismo período; no siempre un mes
entero antes. El suavizado añade un mes de rezago efectivo.

Doce pruebas iniciales cubren identidad, variante, revisión, calendario, enlace
vigente y ruta compartida por los tres consumidores. El lector completo se
cotejó con las dos planillas originales: 127 meses de IPI y 175 de ISAC hasta
julio. Evidencia: `docs/auditorias/2026-09-08/cotejo-ipi-isac-julio.json`.

Queda separado el cotejo de vigencia de bienes de capital: actualizar ISAC no
convierte automáticamente el IAI en un dato de julio.
