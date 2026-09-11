# Cotejo nominal del Senado al 8 de septiembre

Se consultó el [listado oficial de actas](https://www.senado.gob.ar/votaciones/actas)
mediante POST con `busqueda_actas[anio]=2026`, conservando método, formulario,
estado HTTP y hash de cada respuesta. El listado contiene 96 actas; 16
corresponden al intervalo inclusivo del 10-jun al 8-sep, definido por el
corte diario menos 90 días. Las 16 descargas respondieron HTTP 200.

La extracción independiente seleccionó la tabla nominal por sus encabezados
(Senador, Bloque, Provincia y voto), comprobó 72 nombres únicos por acta y
comparó sus filas con el parser del colector. Coinciden los 1.152 registros.
Se conservan los votos públicos, las solicitudes, los hashes de respuestas
y el listado completo en [cotejo-senado-nominal.json](cotejo-senado-nominal.json).
Los HTML completos quedan en `/tmp/cigob-senado-cotejo`; la evidencia del
repositorio no incluye cookies ni cabeceras de sesión.

## Resultados

- **Alineamiento: 59,3%, 24 provincias.** Se identifica el voto mayoritario
  de LLA en cada acta, se suman coincidencias y votos afirmativos/negativos
  de los demás bloques por provincia, y se promedian las 24 tasas sin
  ponderarlas por cantidad de votos. Coincide con la tarjeta actual.
- **Cohesión Senado: 100%, 16 actas**, con última fecha 27-ago. El índice
  de Rice se obtiene por acta de los votos afirmativos y negativos de LLA
  y luego se promedia. Coincide con el componente Senado publicado.

El cotejo cierra la comprobación del valor vigente de alineamiento y de la
parte Senado de cohesión. No verifica las actas de Diputados, cuya caché
continúa con 13 actas hasta el 24-jun; tampoco certifica todo el histórico.
El alineamiento mide votos senatoriales, no la postura de sus gobernadores.

No fue necesario cambiar los datos numéricos ni regenerar índices. La
corrección de [lecturas incompletas](senado-lectura-completa.md) se verificó
con pruebas específicas; esta captura confirma que las 16 respuestas usadas
en el cotejo actual están completas.
