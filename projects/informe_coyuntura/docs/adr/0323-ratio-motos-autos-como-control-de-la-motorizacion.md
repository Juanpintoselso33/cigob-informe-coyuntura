---
madr: 4
id: '0323'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'vida'
indicadores: [motorizacion_total]
archivos: ['scripts/vida_cotidiana/collectors/motorizacion.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts']
relacionado: ['0224', '0271', '0223']
ambito: 'ITCIS · `motorizacion_total` · magnitud de control dentro de la card, no indicador nuevo'
origen: 'Juan, Slack #monitor-de-proyecto-de-gobierno, 15-sep-2026: "para controlar pongamos ratio de motos/autos"'
---

# ADR-0323 — El ratio motos/autos entra como control dentro de la card, no como indicador

## Contexto y planteo del problema

`motorizacion_total` (ADR-0224) puntúa autos+motos per cápita fusionados. La
composición ya viaja colgada de la card con `ratio_motos` —qué porción de
lo patentado son motos sobre el **total**— para explicar el color en la
matriz A×B.

Juan pide un control distinto: motos **sobre autos**, no sobre el total. La
diferencia importa para lo que quiere leer: con `ratio_motos` (motos/total),
un total que crece parejo en las dos patas puede mover el ratio poco aunque
la composición interna cambie; motos/autos aísla directamente si por cada
auto que se patenta se patentan más o menos motos que antes, que es la
pregunta operativa ("¿la gente compra auto o baja a moto?").

## Factores de decisión

- **Es un control de lectura, no una corrección de puntaje.** El indicador ya
  puntúa por ADR-0224 y esta tarea no lo reabre.
- **Regla del repo:** una magnitud que no puntúa no puede ser card propia
  (ADR-0153/0216) — tiene que vivir dentro de una card existente.

## Opciones consideradas

1. Agregar `ratio_motos_autos` a la `composicion` que ya cuelga de
   `motorizacion_total`, y mencionarlo en `_por_que_motorizacion`.
2. Card nueva sólo para el ratio.
3. No calcularlo, dejar que se infiera de `patentamiento_autos` y
   `patentamiento_motos` en el modal.

## Decisión

**Opción 1.** El colector `motorizacion.py` agrega dos campos a
`composicion`: `ratio_motos_autos` (motos_12m / autos_12m, último mes) y
`ratio_motos_autos_base` (el mismo cociente en la ventana del 4T-2023).
`_por_que_motorizacion` en `publicar.py` los vuelca en una frase adicional
("por cada auto patentado se patentan X motos, contra Y al arranque del
mandato") dentro del `por_que` que ya arma la matriz A×B. No se toca el
puntaje, el peso ni la serie de `motorizacion_total`.

Se descartó la Opción 2 por la regla ADR-0153/0216: un ratio que no aporta
puntaje propio no puede ser card. Se descartó la Opción 3 porque dejarlo
implícito repite el motivo por el que existe `_por_que_motorizacion`: el
lector no debería tener que hacer la cuenta en la cabeza para leer la
composición que la ficha ya se propone explicar.

### Verificación con datos de la corrida

Con el patentamiento del último mes con datos completos (referencia
2026-08: `patentamiento_autos: 44.790` · `patentamiento_motos: 75.214`,
consistente con lo confirmado por la corrida del 15-sep-2026), motos/autos ≈
1,68: por cada auto patentado se patentan casi 1,7 motos. El número exacto
publicado usa los acumulados móviles de 12 meses de `composicion`, no el mes
suelto — mismo criterio que el resto de la matriz.

### Confirmación

`tests/test_motorizacion_total.py` se extiende para cubrir que
`ratio_motos_autos`/`ratio_motos_autos_base` existen en `composicion` cuando
el colector corre en vivo, y que `_por_que_motorizacion` incluye la frase del
ratio cuando esos campos están presentes, y sigue funcionando (sin la frase)
cuando faltan — control negativo por mutación: borrar los dos campos hace
desaparecer la frase del `por_que` sin romper el resto del texto.

## Pros y contras de las opciones

**1. Campo dentro de `composicion`.** A favor: no crea superficie nueva de
fuente caída, respeta la regla de cards. En contra: un dato más escondido
dentro de un dict en vez de visible como número suelto.

**2. Card propia.** A favor: visibilidad directa. En contra: viola la regla
del repo — no puntúa, no puede ser card.

**3. Implícito.** A favor: cero código. En contra: no es un control si el
lector tiene que calcularlo.

## Más información

- [[0224-puntua-la-motorizacion-total-no-cada-vehiculo]] — decisión que funde
  autos y motos; este ADR no la reabre.
- [[0271-patentamientos-no-identifican-trayectorias-de-hogares]] — matiza qué
  distingue y qué no distingue la matriz A×B de motorización; el ratio
  motos/autos no cambia esa limitación, es otra vista del mismo dato
  agregado.
