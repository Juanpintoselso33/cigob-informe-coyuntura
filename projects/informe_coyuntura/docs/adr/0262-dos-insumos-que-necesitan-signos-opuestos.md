---
madr: 4
id: '0262'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [icip]
archivos: ['scripts/itcm.py', 'tests/test_idm_e_icip_no_puntuan.py', 'tests/test_itcm.py']
relacionado: ['0009', '0045', '0192', '0253', '0264', '0265']
ambito: 'Cinturón macro · ITCM · `icip` · por qué mudarlo de dimensión no arregla nada'
origen: 'Reauditoría externa post-cambios, 25-ago-2026: «continúa dentro de la dimensión Inversión y todo aumento de pagos transfronterizos eleva el score. Debe salir de Inversión o cambiar su primer insumo»'
---

# ADR-0262 — Dos insumos que necesitan signos opuestos

## Contexto y planteo del problema

ADR-0253 estableció que los pagos al exterior por servicios de informática son
**consumo intermedio** en cuentas nacionales, no formación bruta de capital, y
le cambió el nombre a `icip`. Dejó la estructura intacta y lo anotó: *«queda
anotado que el indicador combina dos cosas heterogéneas —pagos al exterior y
productividad laboral— y que esa mezcla es anterior a esta corrección. No se
toca acá»*.

La reauditoría marcó lo que faltaba: sigue en la dimensión **Inversión** y toda
suba de pagos transfronterizos sube el puntaje. Su recomendación: *«debe salir
de Inversión o cambiar su primer insumo»*.

**La primera mitad de esa disyuntiva no es un arreglo**, y eso es lo que este
ADR viene a mostrar.

### El defecto no es dónde está: es qué suma

`icip = 0,57 × Δ pagos al exterior por servicios de informática + 0,43 ×
Δ productividad laboral (IPI/empleo)`, las dos interanuales.

- El **segundo** insumo tiene signo y no está en discusión: más producto por
  ocupado es menos tensión.
- El **primero** no tiene signo. La OCDE lo trata como consumo intermedio y
  puede sustituir inversión propia; una suba admite leerse como adopción
  tecnológica, como precio, como tipo de cambio o como dependencia importadora.
  Si algo firmara, siendo una importación de servicios firmaría un **débito**.

El compuesto los suma **con el mismo signo**. Sea cual sea el signo que se le
asigne al total, uno de sus dos insumos entra al revés. Y eso **no depende de la
dimensión**: mudarlo cambia el rótulo del capítulo, no la aritmética.

### Tres mediciones

**1. El compuesto es, en los hechos, la serie de pagos.** Sobre 33 meses,
σ(icip) = **60,6 pp**. La contribución del segundo insumo es a lo sumo
`0,43 × σ(IPI i.a.) ≈ 3,3 pp`. **Más del 90% de la dispersión del indicador
viene del insumo que no tiene signo**; la productividad, que sí lo tiene,
apenas lo mueve.

**2. La banda casi no discrimina.** Su ancla superior está en +20% i.a. y la
serie corre hasta +189%: **17 de 33 meses puntúan exactamente 100**, y entre
abr-2024 y feb-2026 son 15 de 23. Más de la mitad del tiempo el indicador
inyecta un máximo constante en su dimensión — el blanqueo de señal que ADR-0045
prohíbe. Recalibrar la banda lo haría discriminar mejor, que es exactamente lo
que **no** conviene mientras el signo no esté establecido.

**3. Empíricamente se comporta como actividad, no como capital.** Contra el IPI
manufacturero: `r = +0,476 / +0,625 / +0,790` a 0, 1 y 3 meses, los tres
significativos. Contra el IAI: `+0,416 / +0,537 / +0,815`. Contra el índice
líder a tres meses: `+0,521`. Es procíclico porque las importaciones de
servicios lo son.

> `iai` e `icip` **no entran a la matriz de redundancia** del ITCM (tiene 15
> indicadores de 17): la dimensión Inversión nunca fue mirada por esa analítica.
> Es un hueco aparte y no se cierra acá.

## Factores de decisión

- **El signo del compuesto es la pregunta, no la dimensión.** Cualquier opción
  que sólo lo mude deja el defecto donde estaba.
- **No tocar `macro.py`**, que es donde vive el compuesto: cambiarlo es diseñar
  un indicador nuevo, y ADR-0253 ya explicó por qué eso pide su propio proceso.
- **El dato sirve igual** leído contra el IAI: inversión física contra gasto en
  digitalización. Eso no necesita un puntaje.

## Opciones consideradas

- **A — Dejarlo en Inversión** y corregir sólo los textos.
- **B — Mudarlo a Competitividad externa**, donde una importación de servicios
  tiene sentido conceptual.
- **C — Mudarlo a Actividad**, que es lo que empíricamente parece medir.
- **D — Cambiar el primer insumo** por formación de capital digital de cuentas
  nacionales.
- **E — Retirarlo del ITCM** y publicarlo como contexto.

## Decisión

**Opción E.** `icip` sale de `BANDAS_ITCM` y de `DIMENSIONES_ITCM`, y entra a
`INDICADORES_CONTEXTO`. Se sigue calculando y publicando; lo que se retira es su
contrato con el score.

La dimensión **Inversión conserva su 12%** y queda con el IAI al 100%, que es lo
que `parametrica.calcular_indice` hace solo al renormalizar. No es la primera
dimensión de un indicador solo: competitividad externa ya lo era. **El peso de
la dimensión no se toca a propósito**: lo que perdió justificación es que unos
pagos al exterior midan formación de capital, no cuánto vale la inversión física
dentro del ITCM. Revisarlo sería otra decisión y pide su propio ADR.

### Consecuencias

- **El ITCM baja 0,7 puntos** con los valores del 25-ago-2026, de 64,8 a 64,1
  medido solo (65,3 junto con ADR-0261). `icip` puntuaba 73,4 contra 59,2 del
  IAI, así que la dimensión cae de 64,9 a 59,2. **Va en sentido contrario al de
  ADR-0261 y las dos casi se cancelan; se declaran por separado a propósito** —
  que el neto sea medio punto no es un argumento a favor de ninguna.
- **La lectura conjunta IAI vs ICIP sobrevive** fuera del score, que es donde
  siempre tuvo sentido.
- **`icip` DEJA DE PUBLICARSE COMO CARD**, por lo mismo que `idm` en ADR-0261:
  o integra el índice o no es card (ADR-0153, ADR-0216). Entre los dos, macro
  pasa de **17 a 15 cards** y el perímetro publicado de 65 a 63. La serie sigue
  publicada en `output/series/macro.csv`, en `series.json` y en BigQuery — es el
  puntaje lo que se retira, no el dato, y la lectura IAI vs ICIP se puede hacer
  igual desde la serie.
- **La cañería que lo hace efectivo se arregla en `publicar.py`**, que pasa a
  derivar `MACRO_OCULTOS` de `itcm.INDICADORES_CONTEXTO` en vez de tenerlo
  hardcodeado. Ver ADR-0261, que lo documenta.

### Confirmación

`tests/test_idm_e_icip_no_puntuan.py`. La guarda propia de este caso es
**condicional a propósito**, porque encoda el argumento y no el resultado: si
alguien devuelve `icip` a una dimensión, `macro.ICIP_PESOS` tiene que haber
dejado de ser `{servicios_tech: 0,57, productividad: 0,43}`. Volver por la vía
de mudarlo de capítulo falla; volver con el insumo cambiado, no.

Probado rompiéndolo: devuelto `icip` a Inversión con su banda y el compuesto
intacto, fallan cuatro guardas, incluida ésa.

## Pros y contras de las opciones

### A — Dejarlo en Inversión

- Bueno: no cambia nada publicado.
- Malo: la dimensión se llama Inversión y su segundo componente es consumo
  intermedio. Es la discrepancia tal cual la marcó la auditoría.

### B — Mudarlo a Competitividad externa

- Bueno: conceptualmente una importación de servicios pertenece ahí. Medido: el
  ITCM no se movería (64,8) y la dimensión subiría de 48,7 a 54,9.
- Malo: para que signifique algo ahí, más pagos al exterior tendría que ser
  **peor**, y el 43% de productividad entraría invertido. Conservar el signo
  actual obliga a afirmar que pagar más nube mejora la competitividad externa,
  que es una tesis causal sin nada detrás.

### C — Mudarlo a Actividad

- Bueno: es lo que empíricamente parece medir. Medido: ITCM 64,3.
- Malo: doble conteo flagrante. Su propio 43% **es** IPI/empleo, y
  `ipi_manufacturero` ya está en esa dimensión, con `r` hasta +0,790 entre los
  dos. Es la clase de acoplamiento por la que ADR-0192 sacó a
  `presion_dolarizacion`.

### D — Cambiar el primer insumo

- Bueno: sería el arreglo de fondo y mediría inversión digital de verdad.
- Malo: ADR-0253 ya lo evaluó — otra fuente, otra frecuencia, otro rezago, otra
  banda. Es un indicador nuevo. Y vive en `macro.py`, fuera del alcance de esta
  entrega.

### E — Retirarlo del ITCM *(elegida)*

- Bueno: es la única que ataca el defecto real —el signo del compuesto— sin
  inventar un fundamento. Deja el dato disponible y deja la puerta abierta a D.
- Malo: el ITCM pierde un componente y la dimensión Inversión queda con uno
  solo. Y arrastra la deuda de `MACRO_OCULTOS`.

## Más información

**Queda abierto y declarado**: si alguna vez se implementa la opción D, la
dimensión Inversión vuelve a tener dos componentes y habrá que revisar si su 12%
sigue siendo el peso correcto — hoy se conserva sin discutirlo, que es lo que
corresponde cuando no es lo que se vino a decidir.

- ADR-0253, que dejó la deuda: `0253-pagar-la-nube-no-es-capitalizar.md`
- Reauditoría: `docs/auditoria_indicadores/260825_reauditoria_post_cambios_macro.md`, caso 14.
