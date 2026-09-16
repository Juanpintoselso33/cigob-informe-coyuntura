---
madr: 4
id: '0328'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'vida'
indicadores: [ratio_motos_autos]
archivos: ['scripts/vida_cotidiana/collectors/motorizacion.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'config.py']
relacionado: ['0224', '0271', '0322', '0323']
ambito: 'ITCIS · dimensión de ingresos y consumo · el ratio motos/autos pasa de magnitud colgada a indicador propio'
origen: 'Juan, 16-sep-2026: revierte ADR-0323 — "los dos tienen que ser indicadores que puntúen, con su card y su peso"'
---

# ADR-0328 — El ratio motos/autos entra a puntuar como indicador propio

## Contexto y planteo del problema

ADR-0323 (15-sep-2026) agregó el ratio motos/autos como magnitud colgada de la
card de `motorizacion_total`, explícitamente SIN puntaje propio, invocando la
regla "una magnitud que no puntúa no puede ser card propia" — pero esa regla
(ADR-0153/0216) dice lo contrario de cómo se aplicó: dice que si algo no
puntúa, no puede publicarse como card. No dice que haya que evitar que puntúe
para no convertirlo en card; dice que si se lo quiere visible, tiene que
puntuar. El pedido original de Juan fue sumar un indicador, no una nota al
pie dentro de otra card.

## Factores de decisión

- **Polaridad, confirmada por el usuario**: más motos por auto es
  **deterioro**. `motorizacion_total` cuenta todo patentamiento como señal
  positiva sin distinguir de qué vehículo viene; el ratio existe para
  detectar que ese crecimiento sea un corrimiento hacia la moto —el vehículo
  más barato— y no una mejora pareja del parque. Confirmado explícitamente:
  sin dejarlo como pregunta abierta.
- **No duplica a `motorizacion_total`**: ese componente mide el NIVEL del
  flujo combinado (autos + motos per cápita); éste mide la COMPOSICIÓN
  (motos por cada auto). Son dos preguntas distintas sobre el mismo flujo, no
  la misma señal repetida.
- El colector ya calculaba `ratio_motos_autos`/`ratio_motos_autos_base` por
  mes dentro de `composicion` (ADR-0323): sólo hace falta exponer la serie
  histórica completa (`serie_ratio_motos_autos`) y dejar que `itvc.py` la
  rebasee, igual que hace con `mora_familias` o `inseguridad`.

## Opciones consideradas

1. El ratio pasa a indicador propio: card, ficha y peso dentro de la
   dimensión de ingresos y consumo (donde vive `motorizacion_total`).
2. Card nueva fuera de esa dimensión.
3. Mantener la decisión de ADR-0323 (magnitud colgada, sin puntaje).

## Decisión

**Opción 1.** Entra `ratio_motos_autos` a la dimensión de ingresos y consumo,
con 2,5% de cesión proporcional sobre los seis componentes que ya había
(`alta_proporcional`, mismo mecanismo de ADR-0130/0153/0225/0322):

```
alta_proporcional(<...seis previos...>, "ratio_motos_autos", 0.025)
→ ratio_motos_autos 0,025 (2,5% interno · 0,7% del ITCIS)
```

2,5% y no 3% es el valor exacto con el que la cesión, redondeada a 4
decimales en cada componente por separado, sigue sumando 1,0 exacto (mismo
requisito que fijó los decimales de ADR-0322). El peso queda por debajo del
que le toca a `motorizacion_total` en la misma dimensión tras esta cesión
(3,09%): es un control sobre la composición del mismo flujo que ya puntúa, y
no debería pesar más que lo que controla.

El colector expone `serie_ratio_motos_autos` (motos móvil-12m / autos
móvil-12m, mismas ventanas que `total_12m`), SIN rebasear.
`itvc.indices_desde_series` la rebasea contra el 4T-2023 con
`invertido=True`:

```python
idx["ratio_motos_autos"] = rebase_de_serie(series, "ratio_motos_autos", invertido=True)
```

**Esto es reversible en una línea**: sacar `invertido=True` invierte la
lectura completa (más motos por auto pasaría a leerse como mejora). Es una
decisión de contenido, confirmada por el usuario para esta versión, no un
hecho aritmético — si el criterio editorial cambia, el cambio es local a esa
línea.

Se descartó la Opción 2 porque el ratio es una vista de la MISMA fuente y el
MISMO flujo que `motorizacion_total`; separarlo de esa dimensión repetiría el
error que ADR-0224 corrigió al fusionar autos y motos por separado. Se
descartó la Opción 3 (mantener ADR-0323) porque contradice el pedido
explícito de Juan de que sea un indicador que puntúe.

### Cuantificación del efecto en el ITCIS

Con el peso de `ratio_motos_autos` en 2,5% de la dimensión de ingresos y
consumo (30,58% del ITCIS antes de la redistribución de `percepcion`
suspendida), su aporte nominal al ITCIS es 0,7%. Ver el cuerpo del PR para el
valor del ITCIS antes/después de esta corrida y el movimiento de la serie
histórica reconstruida.

## Pros y contras de las opciones

**1. Indicador propio en la misma dimensión.** A favor: usa el peso, la
ficha y la card como cualquier otro componente; no repite el error de
ADR-0323. En contra: un componente más para el que la fuente (DNRPA) puede
caerse — mitigado porque es el MISMO colector que ya alimenta
`motorizacion_total`, sin superficie nueva de falla.

**2. Card fuera de la dimensión.** A favor: ninguno claro. En contra: separa
artificialmente dos vistas del mismo flujo.

**3. Statu quo (ADR-0323).** A favor: cambio mínimo. En contra: contradice el
pedido explícito de que puntúe.

## Más información

- [[0224-puntua-la-motorizacion-total-no-cada-vehiculo]] — funde autos y
  motos en el componente que puntúa; este ADR no lo reabre.
- [[0322-la-vacuna-vuelve-a-puntuar-junto-al-resto-de-las-carnes]] — mismo
  mecanismo de cesión ×N sobre lo que haya, con los decimales elegidos para
  que el redondeo siga sumando 1,0.
- [[0323-ratio-motos-autos-como-control-de-la-motorizacion]] — decisión que
  este ADR revierte: el ratio deja de ser una magnitud colgada y pasa a
  puntuar.
