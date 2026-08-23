---
madr: 4
id: '0232'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'politica'
indicadores: [conflictividad_nacional, jornadas_individuales_no_trabajadas_12m]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'scripts/gate_calidad.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0033', '0045', '0048', '0052', '0092', '0094', '0109', '0182']
ambito: 'ITCP · dimensión de conflicto social'
origen: 'Barrido de dimensiones sostenidas por un solo indicador'
---

# ADR-0232 — La intensidad laboral complementa la calle

## Contexto y planteo del problema

`conflictividad_nacional` cuenta eventos de protesta y disturbios de ACLED en
todo el país. Da cobertura territorial y frecuencia, pero una concentración
pequeña y un paro masivo pesan un evento cada uno. La dimensión de conflicto
social dependía enteramente de esa limitación.

La Secretaría de Trabajo publica desde 2006 las **jornadas individuales no
trabajadas**: huelguistas multiplicados por la duración del paro. Su metodología
declara que esta magnitud sí puede sumarse entre meses, a diferencia de la
cantidad de conflictos o huelguistas, donde habría repeticiones.

El último acumulado de doce meses, a mayo de 2026, es **4.760.195 jornadas**.
La relación con ACLED no es estable ni nula: sobre ventanas móviles la
correlación de Pearson en niveles es +0,065, Spearman +0,404 y en primeras
diferencias +0,330. Por eso agrega información, pero no se trata como una señal
ortogonal.

## Factores de decisión

- **Una dimensión con un solo componente renormaliza todo su peso sobre él**, y
  acá ese componente tiene un sesgo conocido: cuenta eventos, así que una
  concentración de veinte personas y un paro general pesan lo mismo.
- **La intensidad y la extensión son cosas distintas** y el índice sólo veía
  una.
- **Las anclas no pueden calibrarse con el período que se evalúa**, o la regla
  se elige para producir el resultado.
- **El candidato no puede ser otro conteo de eventos**, o se duplica el sesgo
  en vez de corregirlo.

## Opciones consideradas

1. Sumar las jornadas no trabajadas al 40%, con anclas fijadas pre-mandato.
2. Ponderar los eventos de ACLED por tamaño estimado de la concentración.
3. Sumar cantidad de huelguistas en lugar de jornadas.
4. Dejar la dimensión con un solo componente.

## Decisión

Se incorpora `jornadas_individuales_no_trabajadas_12m` con **40%** de conflicto
social. `conflictividad_nacional` conserva **60%** por cubrir toda la calle,
incluidos los conflictos no laborales. El peso nominal de la dimensión sigue
en 10% del ITCP.

El nuevo componente usa el acumulado móvil de doce meses y polaridad invertida:
menos jornadas implica menos tensión. Sus anclas son **5,0 · 6,5 · 8,0 · 10,0
millones**, fijadas sobre los diecisiete años completos 2006-2022, antes del
mandato. Esos cortes dejan 4/2/4/3/4 años en las cinco bandas y evitan calibrar
la regla con el resultado que se quiere evaluar.

### Consecuencias

- **La dimensión pasa de 52,9 a 71,7**, y el **ITCP de 65,0 a 67,0** con la
  tensión de 3,5 a 3,3. El cinturón queda con 19 componentes.
- **El componente entra en 100, que es el máximo de su escala**, porque
  4.760.195 jornadas quedan por debajo del ancla más exigente (5,0 millones).
  Eso no es un error de calibración —sobre los 234 meses de la serie el tramo
  superior se toca en el 20%—, pero **sí es una limitación que hay que
  declarar**: durante el mandato el componente marca 100 en **14 de 30 meses y
  en 10 de los últimos 12**, con un rango de 78,5 a 100. Mientras siga ahí no
  aporta información mes a mes, y carga el 40% de la dimensión.
- **Los dos puntos que sube el ITCP son, en su mayor parte, de método**: entra
  un componente en el tope de su escala a diluir uno que puntúa 52,9. La
  lectura sustantiva que lo respalda es real —el conflicto laboral medido en
  jornadas está en mínimos de diecisiete años— pero un lector que compare
  contra ayer tiene que poder distinguir las dos cosas.
- **Qué haría bajar al componente**: cruzar 5,0 millones de jornadas en el
  acumulado móvil. Estuvo en 5,1 y 5,2 dos veces en los últimos doce meses, así
  que el umbral no es remoto.

### Confirmación

`tests/test_segundas_patas.py` cuida que la dimensión no vuelva a quedar con un
solo componente, que el reparto siga siendo 60/40, que las anclas sigan siendo
las fijadas sobre 2006-2022 y que la polaridad siga invertida.

## Más información

- Conflicto social combina extensión territorial/frecuencia e intensidad
  laboral, sin duplicar dos conteos de eventos.
- La serie pública contiene 234 ventanas mensuales, de diciembre de 2006 a mayo
  de 2026.

## Pros y contras de las opciones

**1. Jornadas no trabajadas al 40%.** A favor: mide intensidad, que es
exactamente lo que el conteo de eventos no ve; tiene 234 meses de historia; la
propia metodología de la fuente declara que la magnitud es sumable entre meses,
a diferencia de la cantidad de conflictos o de huelguistas. En contra: entra
saturada en el tope de su escala y ahí no discrimina, y su publicación depende
de una serie de la Secretaría de Trabajo con rezago propio.

**2. Ponderar los eventos de ACLED por tamaño.** A favor: corregiría el sesgo
sin sumar una fuente. En contra: ACLED no publica tamaño de concentración de
forma consistente para Argentina; habría que estimarlo, y sería una estimación
nuestra dentro de un componente que se presenta como conteo de un tercero.

**3. Huelguistas en lugar de jornadas.** A favor: más intuitivo de leer. En
contra: la propia fuente advierte que ese agregado tiene repeticiones entre
meses y no debe sumarse — usarlo sería publicar una suma que la fuente declara
inválida.

**4. Dejarla con un componente.** A favor: cero trabajo. En contra: deja el 10%
del ITCP colgado de un conteo de eventos que no distingue una concentración de
un paro general.
- La planilla vigente se descubre desde la página oficial; si falla, el
  colector mantiene la card previa y el backfill conserva las filas existentes.
- Se declara la limitación del nivel absoluto: una futura serie oficial mensual
  de asalariados permitiría evaluar jornadas por trabajador sin cambiar a
  escondidas la métrica vigente.
