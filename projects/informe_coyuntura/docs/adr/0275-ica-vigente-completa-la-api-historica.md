---
madr: 4
id: '0275'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'macro'
indicadores: [saldo_comercial_12m]
archivos: ['scripts/ica.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'tests/test_ica_vigente.py']
relacionado: ['0056', '0272']
ambito: 'Actualidad y ventanas completas del intercambio comercial'
origen: 'Contraste integral contra la publicación oficial de julio de 2026'
---

# ADR-0275 — El cuadro ICA vigente completa la API histórica

## Contexto y planteo del problema

La API terminaba en junio mientras el informe INDEC del 20-ago ya incluía julio.
La tarjeta y la serie compartían un atraso que una descarga exitosa no detectaba.
Además, la tarjeta sumaba posiciones sin exigir meses consecutivos y el fallback
de saldo directo permitía una suma parcial, mucho más vieja y sin composición.

## Factores de decisión

- Conservar saldo de bienes original en USD, no desestacionalizado.
- Sumar doce meses completos y comparar con los doce anteriores para la regla
  de superávit explicado por contracción de importaciones.
- Compartir fuente entre tarjeta, serie mensual y acumulado móvil.
- Incorporar revisiones, sin redondear cada mes antes de acumular.

## Opciones consideradas

- Esperar a que la API incorpore julio.
- Agregar manualmente el saldo de julio: no repara corridas futuras ni incorpora revisiones.
- Descubrir el cuadro 1 vigente y completar con él la API histórica.

## Decisión

El catálogo oficial enlaza la planilla con fecha de publicación. Se lee su
cuadro 1 por encabezados, años y nombres de meses; se omiten futuros vacíos
y totales acumulados. Sus dos años originales reemplazan las observaciones
coincidentes de la API. Los meses más antiguos mantienen su origen histórico.
El último cuadro validado se conserva con URL y fecha de consulta. Ante fallo
se declara advertencia, sin retroceder silenciosamente de julio a junio.

La tarjeta exige 24 meses consecutivos; el gráfico exige doce para cada punto.
Se retira el fallback que sumaba meses faltantes o una serie muy rezagada como
si fuera un saldo anual actual. El mecanismo general conserva la tarjeta previa
si no puede obtenerse una ventana íntegra.

El workflow versiona el almacén ICA para conservarlo entre runners. La lectura
de ese almacén ante una caída mantiene la fecha de la última consulta exitosa
y no incrementa el contador de fuentes frescas del colector.

## Pros y contras de las opciones

Recupera actualidad y revisiones con una sola función compartida. La historia
combina canales oficiales con diferentes fechas de revisión; el origen queda
declarado. Un cambio de estructura o un catálogo que retrocede debe advertirse.

## Más información

- [Cuadros julio 2026](https://www.indec.gob.ar/ftp/cuadros/economia/ica_cuadros_20_08_26.xls).
- [Publicación del 20-ago](https://www.indec.gob.ar/ftp/ica_digital/ica_d_08_26E158B1D119/).
- Contraste independiente dentro del cuadro: total anual 2025 menos acumulado
  enero-julio 2025 más acumulado enero-julio 2026 reproduce los doce meses.
  Exportaciones USD 97.974 millones, importaciones 74.243 y saldo **23.731**.
  La diferencia con agregar julio al snapshot anterior incluye revisiones de
  meses previos; no es un cambio de fórmula o peso.
