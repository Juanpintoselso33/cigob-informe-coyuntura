---
madr: 4
id: '0214'
estado: 'aceptado'
fecha: 2026-08-20
cinturon: 'vida'
indicadores: [informalidad]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'tests/test_web_declara_los_pesos_del_itvc.py']
modifica: ['0130']
cierra: ['0033']
relacionado: ['0115', '0154']
ambito: 'ITCIS · dimensiones de ingresos y consumo y de prospectivas de empleo'
origen: 'Pendiente abierto de ADR-0033, reclamado por el editor en agosto de 2026'
---

# ADR-0214 — La informalidad es una condición del empleo, no del ingreso

## Contexto y planteo del problema

[[0033-itvc-doble-conteo-y-winsorizacion]] cerró su barrido dejando anotado un
pendiente que llamó **D10**, con estas palabras:

> «Prospectivas de empleo» no contiene medidas directas de empleo (IPI +
> cemento + subocupación; **la informalidad vive en Ingresos**).

El diagnóstico era doble y sólo se resolvió una mitad.
[[0130-la-dimension-empleo-pasa-a-medir-empleo]] atacó la primera —que la
dimensión no medía empleo— **agregando** `empleo_registrado` como componente
principal. La segunda quedó abierta: `informalidad` siguió puntuando dentro de
"Ingresos y consumo", donde entró por herencia del documento fundacional y no
por una decisión sobre qué mide.

Y mide otra cosa. `informalidad` es la proporción de asalariados sin descuento
jubilatorio: no dice cuánto entra en el hogar, dice **bajo qué condiciones se
consigue el trabajo**. Un salario informal y uno registrado del mismo monto dan
el mismo ingreso y no son la misma situación — la diferencia es aporte, cobertura
y estabilidad, que son atributos del empleo.

Dejarla en ingresos tenía además un costo de lectura concreto: la dimensión de
ingresos publicaba una barra que mezclaba poder de compra con calidad del
empleo, y la de empleo publicaba otra donde, tras ADR-0130, **sólo uno de sus
cuatro componentes miraba trabajo directamente** — los otros tres son actividad
industrial, construcción y subocupación.

## Factores de decisión

- **Una dimensión tiene que poder describirse en una frase.** Es la prueba que
  usó [[0110-percepcion-seguridad-y-consumo]] para renombrar, y la que
  [[0115-reorganizacion-de-la-dimension-de-percepcion]] usó para partir una
  dimensión en tres.
- **Mover no es recalibrar.** ADR-0115 fijó la regla: al mudar un indicador se
  **conserva su peso efectivo** y los nominales se derivan de ahí. Y
  [[0045-comisiones-caidas-recalibracion-bandas]] prohíbe tocar
  un peso mirando el efecto sobre el índice.
- **El índice publicado no debería moverse por una decisión de taxonomía.** Si
  se moviera, la serie histórica registraría un salto que no ocurrió en la
  realidad.
- **La dimensión que recibe queda desbalanceada hacia el nuevo componente**, y
  eso hay que declararlo antes, no descubrirlo después.

## Opciones consideradas

1. Mover `informalidad` a empleo conservando el peso efectivo de todos.
2. Moverla y conservar los pesos NOMINALES de las dos dimensiones,
   renormalizando adentro.
3. Dejarla en ingresos y renombrar la dimensión para que la incluya.
4. Dejar todo como está.

## Decisión

**Opción 1.** `informalidad` pasa a **Prospectivas de empleo** con su peso
efectivo intacto: 9,19% del índice, el mismo que tenía. Los pesos nominales de
las dos dimensiones se derivan de los efectivos que quedan a cada lado:

| Dimensión | Antes | Ahora |
|---|---|---|
| Ingresos y consumo | 37,25% | **28,06%** |
| Prospectivas de empleo | 15,00% | **24,19%** |

Ningún otro componente cambia lo que aporta. La única diferencia es
`empleo_registrado`, que pasa de 6,03% a **6,04%** por redondeo a cuatro
decimales.

### Consecuencias

- **El ITCIS no se mueve: 90,7 antes y después, tensión 6,9.** No es suerte, es
  aritmética: el índice es el promedio ponderado de los pesos efectivos, así que
  mover un componente entre dimensiones conservando el suyo es neutro por
  construcción. La serie histórica no registra ningún salto.
- **Lo que sí cambia son las dos barras de dimensión que publica la página del
  cinturón.** Ingresos pasa de 111,3 a 116,9 (tensión 2,7 → 1,6) porque se le va
  su componente más castigado; empleo pasa de 92,4 a 93,1 (tensión 6,5 → 6,4).
  Las dos barras ahora dicen lo que sus nombres prometen.
- **`informalidad` queda como el componente más pesado de su nueva dimensión**
  (37,99% interno), por encima de `empleo_registrado` (24,95%), que ADR-0130
  había instalado como principal. Es consecuencia aritmética del traslado, no
  una decisión de jerarquía: los dos miden empleo desde los dos lados —cuánto
  hay y de qué calidad es— y esa es justamente la dimensión que ADR-0033 pedía.
- **Empleo pasa a ser la segunda dimensión del índice**, detrás de ingresos y
  por delante de precios. Un cinturón que evalúa la validación social de un
  proyecto de gobierno pesando el empleo casi tanto como el poder de compra es
  una posición metodológica, y queda declarada acá.
- **La neutralidad vale con los dieciséis componentes presentes, no con
  huecos.** La renormalización ante faltantes opera DENTRO de cada dimensión,
  así que si falta un dato el agrupamiento sí cambia el resultado: el juego de
  prueba del módulo, al que le faltan tres componentes, pasa de 87,0 a 86,9. En
  producción no aplica —`_carry_forward` completa el último valor bueno de cada
  indicador antes de calcular—, pero queda declarado: en el camino degradado
  este ADR no es neutro.
- ADR-0130 había instalado a `empleo_registrado` como componente principal de
  la dimensión. Deja de serlo, y por eso este ADR lo **modifica**: lo que se
  conserva de aquella decisión es que la medida directa de empleo pese más que
  los tres proxies de entorno, y el test lo verifica en esos términos.
- El pendiente D10 de ADR-0033 queda cerrado.

### Confirmación

`tests/test_web_declara_los_pesos_del_itvc.py` verifica que los pesos que
declara la prosa de las fichas —tanto el **interno** como el **efectivo**—
coincidan con los que calcula `itvc.DIMENSIONES_ITVC`, así que un traslado que
no actualice los textos falla. Es el mismo test que agarró los dos pesos
vencidos de `brecha_salario_cbt` y `consumo_carne`.

Y la corrida de verificación: `ITCIS = 90,7`, `score = 6,9`, `score_global =
4,2`, idénticos a los de antes del cambio, con los pesos de dimensión sumando
1,0000 y los internos de cada una sumando 1,0000.

## Pros y contras de las opciones

**1. Conservar el peso efectivo.** A favor: neutro sobre el índice publicado y
sobre la serie histórica; sigue la regla que ya fijó ADR-0115; el costo es sólo
de taxonomía. En contra: cambia los pesos nominales de dos dimensiones, que son
los números que la gente lee en la metodología.

**2. Conservar los nominales.** A favor: las dimensiones siguen pesando lo
mismo, que es más fácil de explicar. En contra: **no es neutro** — el ITCIS
subiría de 90,7 a 92,9 y la tensión bajaría de 6,9 a 6,4, y el peso efectivo de
`brecha_salario_cbt` saltaría de 17,06% a 22,65% mientras todo empleo se
diluye. Sería mover el número publicado con una decisión de taxonomía, que es
exactamente lo que prohíbe ADR-0045.

**3. Renombrar la dimensión en vez de mover.** A favor: cero riesgo. En contra:
es lo que ADR-0110 hizo con la dimensión de percepción, y ADR-0115 tuvo que
volver tres meses después a arreglar la estructura igual. El rótulo puede tapar
una mezcla; no la deshace.

**4. No hacer nada.** A favor: ninguno más allá del ahorro. En contra: deja
publicada una dimensión de empleo donde un solo componente de cuatro mide
empleo, y el pendiente sigue abierto un año más.

## Más información

- El pedido llegó del editor en agosto de 2026 con la memoria de que el cambio
  ya se había hecho. Se rastreó a fondo —git, reflog, objetos colgados, los dos
  checkouts de la torre, GitHub y los historiales de sesión de las dos
  máquinas— y **nunca se había implementado**: existía como diagnóstico en
  ADR-0033 y como arreglo parcial en ADR-0130. Queda asentado para que la
  próxima vez la respuesta esté escrita.
- [[0154-endeudamiento-e-indice-lider-salen-del-itvc]] es el precedente de la
  operación inversa —sacar componentes y renormalizar— con la misma regla.
