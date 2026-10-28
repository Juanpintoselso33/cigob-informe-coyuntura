---
madr: 4
id: '0393'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [inseguridad]
archivos: ['scripts/itvc.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
modifica: ['0032']
relacionado: ['0032', '0273', '0392', '0394', '0396']
ambito: 'ITCIS · dimensión Seguridad · base de la victimización'
origen: 'Revisión del 28-oct-2026, a pedido de Juan, de que toda serie que dice «fines de 2023» use octubre-diciembre de 2023 y no un solo mes.'
---

# ADR-0393 — La victimización se rebasea al 4T-2023

## Contexto y planteo del problema

Juan pidió verificar que todo lo que se compara contra fines de 2023 use el promedio
del cuarto trimestre, no un solo mes. Se midió, con los datos reales, qué meses usa
cada rebase del índice de impacto social:

- los diez componentes mensuales usan los tres meses;
- los trimestrales (informalidad, subocupación) usan el punto del cuarto trimestre;
- las series que llegan ya en índice (carnes, motorización, alimentos, alquiler,
  construcción) promedian 100 en octubre-diciembre de 2023;
- tres excepciones ya declaradas: pobreza (segundo semestre de 2023, porque el INDEC
  no publica trimestres), homicidios y robos (mediana, [[0327]]) y ocupación de la
  EPH (mismo trimestre de 2023, decisión de Juan).

La única que no cumplía era la victimización, rebaseada a enero de 2024
([[0032]]) porque no se tenían los informes de 2023. [[0273]] los recuperó en
septiembre, y el código dejó anotado que el cambio requería medir el efecto y decidir.

## Factores de decisión

- Una sola base para todo el índice.
- La encuesta tiene ±3 puntos de error muestral por mes.

## Opciones consideradas

- **Promedio de octubre-diciembre de 2023 (elegida).**
- Mantener enero de 2024.

## Decisión

La base de la victimización es el promedio de octubre, noviembre y diciembre de 2023
(34,1 · 32,8 · 27,8 % de hogares; promedio 31,6), como el resto del índice.

### Consecuencias

- Con julio de 2026 (27,3 %), el componente pasa de 104,8 a 115,6. Pesa 2,68 % del
  índice de impacto social: unos 0,3 puntos.
- Octubre y noviembre de 2023 fueron altos y diciembre bajo; el promedio de tres meses
  atenúa ese ruido mejor que un mes solo. Va en la ficha.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_itvc.py` corre el rebase por defecto; `validacion_externa.py` ya no tiene
bases propias.

## Pros y contras de las opciones

- 4T-2023: misma regla que el resto; tres meses de encuesta en lugar de uno.
- Enero de 2024: continuidad con lo publicado, pero otra base y un solo mes.
