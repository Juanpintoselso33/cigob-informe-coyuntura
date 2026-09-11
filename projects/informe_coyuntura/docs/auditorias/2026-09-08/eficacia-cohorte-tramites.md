# Eficacia: cotejo independiente de Trámites Parlamentarios

Consulta del 8-sep-2026. Se revisaron los índices parlamentarios 2024 y
2025, que abarcan marzo a febrero, y las 18 páginas diarias con entradas
PE/JGM dentro de 8-sep-2024 a 8-sep-2025. Las 28 entradas se clasificaron
por su contenido: 14 proyectos de ley y 14 comunicaciones, vetos,
resoluciones o remisiones administrativas. Los 14 proyectos coinciden
exactamente con los expedientes de la cohorte CKAN vigente. El cociente
actual sigue en 2/14 = 14,3%.

PE 17/2024 comunica el veto de financiamiento universitario. PE 2/2025
es una resolución sobre la Fragata Libertad. PE 4, 5 y 6/2025 comunican
vetos. Los JGM excluidos remiten decisiones, planes, información de avance
o cuenta de inversión; no son proyectos de ley. El presupuesto 2025,
JGM 12/2024, sí está incluido. No se debe inferir tipo de iniciativa sólo
por la presencia de las palabras «proyecto de ley» en el texto de un veto.

## Discrepancias de fechas e integración

| Expediente | PUBLICACION_FECHA CKAN | Índice TP |
|---|---|---|
| 0023-PE-2024 | 2025-01-22 | 2025-01-20 (TP 223) |
| 0024-PE-2024 | 2025-01-22 | 2025-01-20 (TP 223) |
| 0007-PE-2025 | 2025-07-30 | 2025-08-06 (TP 109) |

Los PUBLICACION_ID del catálogo remiten a esos mismos trámites. Los PDFs
originales de PE 23 y 24 contienen notas y mensajes firmados el 17-ene:
no confundir firma con publicación. El sumario de Ficha Limpia dice
«de fecha 20 de enero», discrepante con su mensaje firmado; el índice TP
fecha la publicación el 20. El PDF de PE 7 contiene la remisión firmada el
6-ago-2025 a las 10:14, concordante con TP 109 e incompatible con dar por
publicado ese documento una semana antes. La corrección se integró mediante `_fecha_publicacion_proyecto`, compartida entre tarjeta e historia, sin alterar las filas brutas del catálogo.

La integración usa una única corrección documentada de fecha de
publicación en tarjeta e historia, conserva el dato bruto y verifica
bordes de cohorte. El traslado julio/agosto cambia julio de 2026;
las fechas de enero pueden afectar cortes diarios aun sin cambiar cierres
mensuales. No presentar esta comprobación como validación histórica completa.

## Alcance y evidencia

Se cierra la identidad del denominador actual registrado en Diputados.
Queda comprobar proyectos con origen en Senado no representados en estos
trámites antes de afirmar exhaustividad de todo el Ejecutivo. La matriz
conserva esta salvedad; las fechas ya se corrigieron.

[Fuentes, hashes, clasificación y comparación](cotejo-cohorte-tramites.json).
Los HTML de trabajo permanecen en `/tmp/cigob-cohorte-tp`; la evidencia
necesaria para retomar está en el JSON versionable, sin credenciales.

## Resultado integrado

La comparación de toda la serie contra los datos publicados cambia sólo
julio-2026: eficacia 13,3 → 14,3%, ITCP 67,8 → 67,9. Agosto sigue 68,2,
por lo que su aumento mensual es 0,3 puntos. La tarjeta actual mantiene
2/14 = 14,3% e ITCP 71,9. El contraste EPU en diferencias pasa a −0,261;
la brecha discriminante del panel político en diferencias queda 0,166.
Se regeneraron publicación, fichas políticas, sensibilidad, censo y
contribuciones mensuales. No cambia la interpretación cualitativa general.

Las frases de requisitos de integración anteriores describen el criterio
aplicado: ya no son un pendiente. Sigue abierta la exhaustividad de origen
Senado; no se afirma validación integral de toda la fuente.

Cierre posterior: [el cotejo del Senado](eficacia-cohorte-senado.md) resuelve la salvedad de origen para la cohorte vigente. Los tres proyectos hallados están en CKAN y fuera de la ventana.
