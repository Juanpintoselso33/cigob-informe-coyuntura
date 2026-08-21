---
madr: 4
id: '0221'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'gestion'
indicadores: [litigiosidad_laboral]
archivos: ['tests/test_gestion_dotacion_fuerzas.py', '.github/workflows/data-pipeline.yml', 'tests/test_bigquery_backfill.py']
relacionado: ['0098', '0142', '0209', '0228']
ambito: 'ITCG · guardia de la dimensión de reforma laboral · dónde se pone el umbral'
origen: 'Cuatro noches seguidas de nocturno caído (18 al 21 de agosto de 2026), investigadas al revisar por qué no se commiteaba el snapshot'
---

# ADR-0221 — Un cable trampa mira la banda, no el puntaje

## Contexto y planteo del problema

El nocturno falló **cuatro noches seguidas** —18, 19, 20 y 21 de agosto de
2026— en el gate G4-G5, que corre antes de commitear el snapshot y antes de
espejar la corrida en BigQuery. Cuatro corridas que no se publicaron y no
entraron al archivo, sin que ningún dato estuviera mal.

Una de las dos causas es la guardia heredada de [[0098-...]] y retocada por
[[0142-...]], que exigía `puntaje(litigiosidad_laboral) < 60,0`. Disparó con
60,8 y su mensaje decía que *"la industria del juicio se habría enfriado de
verdad"*.

**No se enfrió.** Los juicios laborales siguen creciendo: 127.363 en doce meses
contra 124.767 en los doce previos, o sea +2,1%. Lo único que pasó es que llegó
un mes nuevo de la serie de la SRT y la tasa de crecimiento se desaceleró 0,7
puntos porcentuales —de 2,8% a 2,1%— **dentro de la misma banda**. El puntaje
interpolado cruzó un número redondo y el mensaje afirmó un hecho del mundo que
no ocurrió.

El problema es dónde estaba puesto el umbral: **60,0 cuando el valor era 59,4**.
Un cable trampa a un punto del valor actual dispara con el ruido mensual normal
de un cociente de doce meses contra doce meses.

## Factores de decisión

- **Una guardia que dispara por ruido se termina ignorando**, que es la peor
  manera de perderla: sigue en verde en la lista de tests y ya nadie la lee.
- **El umbral no puede quedar pegado al valor del día en que se escribió.** Ése
  es el modo en que se calibran mal: se mira el número de hoy y se pone el corte
  un poquito más allá.
- **El mensaje de una guardia afirma un hecho.** Si dice "los juicios se
  enfriaron" y los juicios crecen, la guardia miente aunque el código sea
  correcto.
- **La paramétrica ya define categorías.** Reinventar un corte propio al lado de
  las bandas es tener dos metodologías para la misma pregunta.

## Opciones consideradas

1. Mirar la **banda** de la paramétrica en vez del puntaje interpolado.
2. Subir el umbral del puntaje de 60 a 65.
3. Sacar la guardia.
4. Dejarla y re-correr el nocturno cada vez que dispare.

## Decisión

**Opción 1.** La guardia deja de mirar el puntaje interpolado y mira la
variación contra el **piso de la banda «sin cambio apreciable»** de
`BANDAS_ITCG`, que hoy es −5%.

El piso se **lee de la paramétrica**, no se escribe a mano en el test: si alguien
recalibra las bandas, la guardia se mueve con ellas en vez de quedar apuntando a
un número viejo — que es exactamente la forma en que se rompió.

Mientras la variación interanual siga dentro de (−5%, +5%) no pasó nada que
mirar: es la categoría que la propia metodología llama "sin cambio apreciable".
Si cae por debajo de −5%, la litigiosidad se enfrió de verdad y ahí sí hay una
pregunta editorial que contestar.

### Consecuencias

- La guardia pasa con el 2,1% que venía rompiendo el nocturno, y con −4,9%.
  Falla con −5,1% y con −12%. Verificado inyectando los cuatro valores.
- Deja de haber dos varas para la misma pregunta: la del test es la de las
  bandas.
- El mensaje de error ahora nombra la variación y el piso, así que dice qué pasó
  en vez de afirmar una conclusión.

### La otra causa de las cuatro noches, que no es de metodología

`test_la_historia_en_git_no_tiene_corridas_rotas` cuenta las corridas que hay en
git para verificar el supuesto del backfill ([[0209-...]]). En CI encontraba
**una**, porque `actions/checkout` clona con `fetch-depth: 1`: no es que la
historia estuviera rota, es que no había historia que leer. Fallaba con
`assert 1 >= 225`, un mensaje que apunta al lugar equivocado y manda a buscar un
problema de datos que no existe.

Se arregló por los dos lados: el workflow pasa a `fetch-depth: 0` —el repo pesa
16 MB y 913 commits, traer todo no cuesta— y el test detecta el clon shallow y
lo dice con todas las letras en vez de fallar por el motivo equivocado.

### Confirmación

Los cuatro valores inyectados (2,1 · −4,9 · −5,1 · −12,0) dan el resultado
esperado en cada caso. La suite completa queda en verde.

## Pros y contras de las opciones

**1. Mirar la banda.** A favor: usa la categoría que la metodología ya define,
se mueve sola si se recalibran las bandas, y el disparo pasa a significar algo
del mundo y no un cruce de interpolación. En contra: pierde sensibilidad a
movimientos dentro de la banda — deliberado, porque ésos son ruido.

**2. Subir el umbral a 65.** A favor: un cambio de un caracter. En contra: es el
mismo error otra vez, sólo que corrido cinco puntos; volvería a disparar en unos
meses y sin significar nada.

**3. Sacarla.** A favor: no molesta más. En contra: la pregunta que hace es
legítima — si la litigiosidad se desploma hay que mirar por qué, y sin la
guardia nadie lo mira.

**4. Dejarla y re-correr.** A favor: ninguno. En contra: es lo que venía
pasando, cuatro noches sin publicar y sin archivo.

## Más información

- El indicador es de **contexto** del ITCG: la variación 12m/12m de juicios de
  la serie histórica de litigiosidad de la SRT.
- La otra guardia de este test —que el FAL sostiene la dimensión— queda intacta.
