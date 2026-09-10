# Sesiones y sanciones: conciliación del índice oficial

El índice HCDN permite seleccionar 53 reuniones legislativas desde 2023 hasta
la consulta del 8-sep-2026. CKAN omite la reunión del 26 de agosto y contiene
fechas dos días anteriores a las del índice en 72 coincidencias del inventario
general. El colector usa las fechas individuales del índice; no desplaza
automáticamente las fechas del catálogo. La convocatoria del 9 de septiembre
es futura y se excluye.

En la ventana vigente se cuentan diez reuniones, una en minoría: **10%**, frente
al anterior 11,1% (una de nueve). El indicador describe minorías registradas;
no incluye todas las formas posibles de bloqueo parlamentario ni atribuye
falta de quórum a toda convocatoria no efectuada.

La reunión iniciada el 26 de agosto termina el 27 a las 3:47. Su diario
registra estas sanciones definitivas omitidas del catálogo:

| Expediente de revisión | Asunto | Página impresa |
|---|---|---:|
| 0026-S-2026 | Mercosur–Singapur | 291 |
| 0028-S-2026 | San Miguel de Tucumán, capital simbólica | 361 |
| 0022-S-2026 | Cámara Federal de Tucumán | 364 |
| 0021-S-2026 | Cámara Federal de Mar del Plata | 369 |
| 0041-S-2025 | Camino de Brochero | 374 |

El BAT posterior permite verificar los números 27.819 a 27.823; el boletín del Senado añade 27.824 y 27.825. La fecha se conserva junto con
la fecha de inicio de sesión y su nota de procedencia; el indicador computa
meses completos. El PCT vuelve al Senado con modificaciones y queda excluido.
La deduplicación reconoce expediente/proyecto cuando el catálogo incorpora
posteriormente el número de ley.

El total pasa a **29 leyes** en septiembre de 2025–agosto de 2026. El ITCP de
portada pasa a **71,9** y el cierre histórico de agosto a **68,2**, frente a
67,8 en julio. Son revisiones del registro, sin cambios de pesos ni anclas.
La suba mensual coincide con el ICG de Di Tella; no demuestra que midan lo
mismo. El [cotejo del Senado](senado-sanciones-corregidas.md) resuelve el pendiente de sus tratados y deja explicitada la salvedad sobre la referencia histórica.

Fuentes: [índice HCDN](https://www.hcdn.gob.ar/sesiones/),
[diario original](https://www3.hcdn.gob.ar/dependencias/dtaquigrafos/diarios/periodo-144/diario_202608266.pdf),
[información institucional sobre las sanciones](https://www.hcdn.gob.ar/prensa/noticia/EN-SESION-ESPECIAL-LA-CAMARA-DE-DIPUTADOS-APROBO-UNA-BATERIA-DE-PROYECTOS/).
La [evidencia reproducible](cotejo-sesiones-sanciones.json) conserva registros,
huellas de archivos, tarjetas y series anteriores y corregidas.

Fecha legal: los cinco textos comunicados por Diputados están fechados el **26 de agosto**, aunque la sesión terminó y las noticias se publicaron el 27. El registro corregido usa el 26; ambas fechas caen en el mismo mes y la corrección no cambia el total mensual.
# Cotejo nominal posterior del dato vigente

El [inventario nominal independiente](cotejo-quorum-nominal.json) conserva las
diez reuniones del denominador y las exclusiones del índice oficial dentro
de la ventana. Sólo la reunión del 23-jun-2026 aparece en minoría: 1/10 = 10%.
La definición usa doce meses calendario, octubre-2025 a septiembre-2026,
cortados al 8-sep; no 365 días retrospectivos. Por eso no entra la sesión del
17-sep-2025. Se cierra la comprobación del dato vigente, sin atribuirle alcance
sobre todas las formas de bloqueo político ni modificar la serie.
