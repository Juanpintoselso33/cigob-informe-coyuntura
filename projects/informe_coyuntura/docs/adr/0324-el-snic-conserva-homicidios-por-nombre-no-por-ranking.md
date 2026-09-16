---
madr: 4
id: '0324'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'vida'
indicadores: [inseguridad_snic]
archivos: ['scripts/vida_cotidiana/collectors/snic.py']
relacionado: ['0032', '0325']
ambito: 'Contraste anual del IVI · SNIC · qué tipos de delito se conservan del desglose'
origen: 'Juan, Slack #monitor-de-proyecto-de-gobierno, 15-sep-2026: "para seguridad, buscar datos de homicidios y rapiñas"'
---

# ADR-0324 — El SNIC conserva homicidios por nombre, no por ranking de volumen

## Contexto y planteo del problema

`inseguridad` (el componente que puntúa, IVI del LICIP-UTDT, mensual,
ADR-0032) tiene como contraste al SNIC: es anual, con ~5 meses de rezago
desde el cierre del año, y el propio `itvc.py` ya declara la fuente única
como limitación. No puntúa ni va a puntuar acá — es contraste, no un segundo
componente del índice.

El colector `snic.py` desglosa el total anual por tipo de delito en
`tipos_principales`, pero se queda con el **top-5 por cantidad de hechos**.
Verificado contra el CSV oficial 2025: eso conserva "Robos (excluye los
agravados por el resultado de lesiones y/o muertes)" (360.946 hechos, el #1
nacional) y descarta "Homicidios dolosos" (1.613 hechos), que queda muy por
debajo del quinto puesto (~100.000). El dato de homicidios ya se descarga del
CSV oficial y se tira antes de llegar a ningún lado — exactamente lo que
Juan pidió buscar.

## Factores de decisión

- El SNIC es anual y llega con meses de rezago: **no sirve para puntuar** un
  tablero mensual, y esta tarea no lo convierte en indicador.
- Homicidios es el tipo de delito más citado en cualquier lectura pública de
  seguridad, y es justamente el que un corte por volumen excluye siempre —
  por diseño, nunca va a estar entre los cinco delitos más frecuentes.
- El nombre exacto de cada categoría en el CSV no es estable entre lo que
  dice la documentación y lo que trae la columna real (verificado: el CSV usa
  `codigo_delito_snic_nombre` con los nombres largos oficiales, no
  abreviaturas).

## Opciones consideradas

1. Reemplazar el corte por volumen por una lista fija de nombres relevantes.
2. Mantener el top-5 y agregar homicidios como categoría extra siempre
   presente.
3. Convertir el SNIC en componente que puntúa, con los tipos relevantes.

## Decisión

**Opción 1.** `tipos_principales` pasa a conservar una lista fija de
categorías por **nombre exacto** (`TIPOS_RELEVANTES` en `snic.py`), verificada
contra el CSV 2025:

- `Homicidios dolosos`
- `Robos (excluye los agravados por el resultado de lesiones y/o muertes)`
- `Robos agravados por el resultado de lesiones y/o muertes`
- `Hurtos`
- `Abusos sexuales con acceso carnal (violaciones)`

Si el CSV de un año no trae alguno de estos nombres (cambio de nomenclatura
de la fuente), el colector lo loguea como advertencia y sigue con los que sí
están — no revienta la corrida por una categoría, porque el resto del
desglose sigue siendo útil aunque una nomenclatura cambie.

Se descartó la Opción 2 (top-5 + homicidios) porque agregar una excepción
puntual no resuelve el problema de fondo: cualquier otro tipo de delito de
bajo volumen y alta relevancia (por ejemplo violaciones) seguiría cayendo por
la misma razón. Se descartó la Opción 3 explícitamente: el brief pide **no**
convertir esto en indicador que puntúe, y el propio `itvc.py` ya declara
pendiente sumar una segunda medida de seguridad sin resolverlo acá.

### Confirmación

Verificado contra el CSV oficial descargado en vivo el 15-sep-2026: el año
2025 trae exactamente las cinco categorías de `TIPOS_RELEVANTES`, con
Homicidios dolosos en 1.613 hechos y Robos en 360.946 — la brecha de dos
órdenes de magnitud que antes garantizaba la exclusión de homicidios del
top-5.

## Pros y contras de las opciones

**1. Lista fija por nombre.** A favor: resuelve el problema de fondo (no sólo
homicidios), es explícito sobre qué se conserva y por qué. En contra: una
lista fija no se actualiza sola si cambia qué es "relevante".

**2. Top-5 + homicidios.** A favor: cambio mínimo. En contra: parche puntual,
no arregla el mecanismo que también dejaría afuera a otras categorías de bajo
volumen y alta relevancia.

**3. SNIC puntúa.** A favor: usaría el dato ya descargado. En contra: viola
la restricción explícita de esta tarea y la limitación ya declarada de
frecuencia anual con rezago para un tablero mensual.

## Más información

- `scripts/itvc.py` sigue declarando la fuente única de `inseguridad` (IVI)
  como limitación pendiente; este ADR no la resuelve, mejora el contraste
  existente.
