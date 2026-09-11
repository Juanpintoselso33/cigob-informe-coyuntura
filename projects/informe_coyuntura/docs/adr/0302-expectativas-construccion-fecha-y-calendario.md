---
madr: 4
id: '0302'
estado: 'aceptado'
fecha: 2026-09-08
cinturon: 'politica'
indicadores: [brecha_obra_publica]
archivos: ['scripts/politica.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'tests/test_brecha_expectativas_calendario.py']
ambito: 'Referencia temporal y promedio móvil de expectativas'
---

# ADR-0302 — Expectativas de construcción: horizonte y calendario

El Cuadro 7.1 del ISAC pregunta por un trimestre futuro. La edición del 8 de
septiembre de 2026 consulta agosto–octubre. El colector usaba octubre como
fecha del dato, desplazando la historia dos meses y aparentando una
observación futura. Además, el patrón omitía filas con «de» antes del año,
como «mayo 2020 - julio de 2020». Su promedio de doce registros podía abarcar
más de doce meses.

La serie se referencia al inicio del horizonte y la tarjeta explicita ambos
extremos. Es una convención de período para expectativas, no la fecha de
campo ni la de publicación: no acredita que el dato estuviera disponible al
comienzo del horizonte. El contraste histórico sigue siendo retrospectivo;
una validación en tiempo real requiere conservar las fechas de publicación.

Se admite la preposición del original, se exige horizonte de tres meses,
porcentajes finitos entre cero y cien, ausencia de duplicados y calendario
mensual consecutivo. El promedio conserva doce meses y los pesos no cambian.
Las filas de notas no se interpretan como observaciones. Una inconsistencia
falla explícitamente y utiliza el mecanismo de caché del colector.

Se regenera toda la historia y se recalculan los contrastes afectados. Las
correlaciones impresas de versiones anteriores no se mantienen como si
pertenecieran a la serie corregida. La tarjeta y la historia comparten lector.
