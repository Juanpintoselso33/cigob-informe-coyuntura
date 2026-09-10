# Producción legislativa: correcciones y cobertura pendiente

El [recurso original HCDN](https://datos.hcdn.gob.ar/api/3/action/resource_show?id=68dfd7f8-91f3-4ecf-aebf-a860d1ca1a98)
declara modificación el 18 de agosto de 2026. La consulta paginada de la API y
el CSV original coinciden en las 1.340 filas tras normalizar tipos y nulos.
La última sanción registrada es del 24 de junio de 2026.

Hay 1.337 números de ley distintos: 27580 y 26723 repiten fecha; 27083 tiene
dos fechas en diciembre de 2014. El promedio declarado era incorrecto porque
incluía 19 leyes de 2026 y tres duplicados: para 2008-2025 hay 1.318 leyes
distintas, 73,22 por año. El umbral de diseño 74 se conserva y se presenta
como referencia aproximada, sin afirmar que es el promedio exacto.

ADR-0306 corrige la ventana a doce meses completos y excluye el mes en curso.
ADR-0308 agrega siete sanciones definitivas de agosto ausentes de CKAN,
verificadas en el diario de sesiones: la tarjeta pasa de 22 a **29 leyes**.
La historia ITCP 2026 queda en 65,7; 64,7; 66,9; 62,6; 67,4; 68,4; 67,8; 68,2.
Julio cae 0,6 y agosto sube 0,4. No cambia ningún peso ni umbral.

El contraste ITCP–EPU da −0,284 en niveles (32 meses) y −0,259 en diferencias
(31). La brecha del panel es 0,165 en diferencias y −0,075 en niveles.
Agosto coincide en dirección con ICG tras integrar las sanciones omitidas;
no constituye una prueba de que ambos indicadores midan el mismo fenómeno.

El informe de la Dirección de Información Parlamentaria enumera 64 leyes entre el 10-dic-2023 y el 28-feb-2026; CKAN sólo contiene 62 para ese intervalo. Las faltantes 27748 y 27774 se cotejaron en sus originales del BO: sanciones del 14-ago-2024 y 1-oct-2024. Se integran desde `data/politica/leyes_sancionadas_complementarias.json`, deduplicadas contra CKAN. La referencia corregida con esos complementos es 1.320 / 18 = 73,33. El registro conserva su fecha de revisión manual.

La última sanción del registro ampliado es del 27 de agosto. El cotejo posterior incorpora las leyes 27.824 y 27.825, además de las cinco de Diputados (27.819–27.823). Los otros tres tratados del Senado pasan a Diputados y el PCT vuelve al Senado: no se cuentan. La cobertura vigente asciende a 29 y pasa a `comprobado_con_salvedad`: la reserva remanente corresponde a exhaustividad del catálogo histórico usado como referencia, no a estas siete sanciones verificadas.

Evidencia: [cotejo inicial API/CSV](cotejo-produccion-calendario.json) y
[sesiones y cinco sanciones de Diputados](cotejo-sesiones-sanciones.json), más [dos del Senado y números legales verificados](cotejo-senado-sanciones.json).

InfoLeg contiene 25 leyes publicadas en su ventana de 365 fechas
(9-sep-2025/8-sep-2026): 22 coinciden con el inventario de producción anterior
y tres fueron sancionadas antes (27793, 27795, 27796). Las siete sanciones de
agosto agregadas desde los diarios y boletines aún no aparecen en ese inventario de
publicaciones. Se concilian fechas y universos, no se exige igualdad entre
cantidad sancionada y cantidad publicada.
