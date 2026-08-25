---
madr: 4
id: '0254'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'macro'
indicadores: [idm]
archivos: ['scripts/macro.py', 'scripts/itcm.py', 'scripts/descargar_series.py', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/pages/[slug].astro', 'tests/test_constructos_no_prometen_de_mas.py']
relacionado: ['0009']
ambito: 'Cinturón macro · ITCM · `idm` · por qué comparar dos agregados no es medir un exceso sobre la demanda'
origen: 'Auditoría externa de indicadores, 25-ago-2026: «qué no mide: oferta monetaria efectiva menos una demanda de dinero estimada»'
---

# ADR-0254 — La brecha M3–M2 no es oferta menos demanda

## Contexto y planteo del problema

`idm` se publicaba como **«Exceso de pesos sobre la demanda (IDM)»**, expansión
de «Índice de Desequilibrio Monetario». La descripción pública decía que
detecta «si sobran pesos respecto de lo que la economía quiere retener» y que una
brecha negativa es «remonetización traccionada por demanda real de dinero».

Lo que calcula es la **diferencia entre el crecimiento real interanual del M3
privado y el del M2 privado transaccional**. Los dos son **agregados
monetarios**. M2 no es una demanda de dinero: es un stock observado.

La diferencia no es semántica. Una **demanda de dinero** es una función
estimada: hay que elegir las variables que la explican (ingreso, tasa de
interés, inflación esperada), una forma funcional, un período de estimación y
una validación. Nada de eso existe acá, y sin eso la palabra «exceso» no tiene
contra qué medirse.

Vale decir que la implementación ya había corregido un error anterior de la
propuesta original —restar una tasa real de una nominal, que daba rojo
permanente— y eligió la versión real-real interanual, que es la correcta para lo
que compara. El cálculo está bien. Lo que no estaba bien era lo que se decía que
el cálculo significa.

## Factores de decisión

- **Una brecha entre dos agregados es un dato observable y útil**; una demanda
  estimada es otra cosa y no está.
- **El cálculo no cambia**, así que la serie histórica sigue siendo comparable.
- **La afirmación estaba en cinco lugares**, incluida la página de metodología.

## Opciones consideradas

- **A — Renombrar** a «Brecha de crecimiento real M3–M2», mantener la fórmula y
  corregir la lectura.
- **B — Estimar una función de demanda de dinero** y medir el exceso de verdad.

## Decisión

**Opción A**, la mínima que propuso la auditoría. El indicador pasa a llamarse
**«Brecha de crecimiento real M3–M2»** y su lectura pública cambia de «sobran
pesos» a lo que efectivamente muestra: **hacia dónde se mueven los pesos dentro
del sistema**. Positivo = el agregado amplio crece más rápido que el
transaccional, o sea que los pesos se van a plazo y a instrumentos remunerados
en vez de quedarse en transacciones. Negativo = lo contrario.

La sigla `idm` se conserva como identificador; cambia su expansión.

La opción B es la sustantiva, y la auditoría pide explícitamente no
implementarla sin un diseño y un ADR previos. Con razón: una función de demanda
mal especificada produciría un «exceso» con aire de rigor y sería peor que la
brecha honesta.

### Consecuencias

- **El valor, la fórmula, la banda y el peso no cambian.** La serie histórica
  sigue siendo la misma y sigue siendo comparable hacia atrás.
- La descripción de la dimensión `estabilidad_monetaria` decía «el desequilibrio
  entre oferta y demanda transaccional de pesos (IDM)» y también se corrige.
- La página pública de metodología describía el indicador como «brecha entre la
  oferta amplia y la demanda transaccional»; ahora dice que los dos son
  agregados.
- **Queda una pregunta abierta que este ADR no resuelve**: la banda del
  indicador se calibró leyendo la brecha como exceso monetario —«>5 → 10»
  castiga fuerte el positivo—. Esa lectura sigue siendo defendible por otra vía
  (los pesos yéndose de las transacciones), pero **la calibración merece
  revisarse** ahora que el constructo se llama por su nombre.

### Confirmación

`tests/test_constructos_no_prometen_de_mas.py`:

- **«demanda de dinero», «exceso de pesos» y «excedente de pesos» no pueden
  afirmarse** en el código ni en la capa pública;
- el rótulo nombra los dos agregados y no menciona demanda;
- la fórmula y el peso no cambiaron, que es lo que mantiene comparable la serie.

Probado rompiéndolo: repuesto el rótulo «Exceso de pesos sobre la demanda»,
fallan dos guardas.

## Pros y contras de las opciones

### A — Renombrar y corregir la lectura

- Bueno, porque el nombre pasa a describir el cálculo y la serie no se toca.
- Malo, porque la banda quedó calibrada bajo la lectura anterior. Queda anotado.

### B — Estimar una demanda de dinero

- Bueno, porque mediría el fenómeno que el nombre prometía.
- Malo, porque exige variables, forma funcional, período y validación explícitos.
  Hecho a las apuradas daría un número con aire de rigor y menos defendible que
  la brecha que ya se observa.

## Más información

- Auditoría externa de indicadores, 25-ago-2026:
  `docs/auditoria_indicadores/260825_macro.md`.
