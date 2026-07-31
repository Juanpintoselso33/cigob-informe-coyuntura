---
madr: 4
id: '0134'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
ambito: 'cinturón político (ITCP), bloque judicial'
---

# ADR-0134 — Parálisis de denuncias: la fuente sirve, y el dato contradice la hipótesis

- **Relacionados**: ADR-0131 (protocolo de codificación del bloque judicial),
  ADR-0042 (nacer discriminando), ADR-0045 (no recalibrar para que dé mejor),
  ADR-0095 (publicar el resultado incómodo)

## Contexto y planteo del problema

El aporte externo al cinturón político propone un indicador de **parálisis de
denuncias**: medir si el mecanismo de control disciplinario de los jueces —las
comisiones de Disciplina y de Acusación del Consejo de la Magistratura— está
funcionando o está trabado. Este ADR aplica el protocolo de ADR-0131: primero
encontrar la fuente, después construir el universo, después leerlo, y recién
entonces discutir la métrica.

### La fuente que parecía obvia no es la correcta

El sitio del Consejo publica un **«Registro Público de Denuncias presentadas
contra Magistrados/as»**. No sirve: es específicamente el registro de
**situaciones vinculadas a violencia de género**, creado por Resolución 8/2021.
Mide otro fenómeno. El nombre abreviado del enlace induce a error y por eso
queda anotado en el registro del universo, para que nadie vuelva a recorrer el
mismo camino.

Tampoco hay actas de sesión parseables: los PDF de la sección son reglamentos,
digesto y resoluciones institucionales.

### La fuente que sí sirve, y por qué se puede confiar en ella

Cada sesión de comisión se publica como una nota fechada y **numerada** en la
categoría `comisiones` del sitio. Se recorrió la categoría **hasta agotarla**:
36 páginas, 356 notas, desde el 13-sep-2019 hasta el 15-jul-2026.

Es un blog institucional, no un registro público, y eso normalmente lo
descalificaría: si el Consejo sesiona y no publica, el indicador no se entera.
**Lo que lo vuelve usable es la numeración correlativa.** Un salto en la
numeración delataría una sesión no publicada. Desde la separación de las
comisiones la numeración **no tiene saltos**: Disciplina va 2→9 completa y
Acusación 1→15 con un solo número sin identificar, el 7, que casi con seguridad
es la nota sin numerar del 20-dic-2023. La cobertura de sesiones ordinarias es
completa, y por lo tanto **los huecos largos del calendario son huecos reales**.

Si el Consejo cambiara el esquema de numeración, el indicador pierde su control
de cobertura y hay que revisarlo. Queda dicho acá.

### Hasta 2022 era una sola comisión

Hasta jul-2022 existió una única **Comisión de Disciplina y Acusación**; desde
entonces son dos comisiones separadas, cada una renumerando desde el principio.
Las sesiones previas (numeradas 3, 4, 7, 8 y 9 bajo el slug
`disciplina-y-acusacion`) **no son comparables** con las posteriores y quedan
fuera de todo conteo. Contarlas juntas habría inflado la historia temprana y
producido exactamente la conclusión contraria a la verdadera.

La parálisis **existe y es grande**, pero es **anterior al período que mide el
informe**:

| Comisión | Sesiones | Hueco medio | Hueco máximo |
|---|---|---|---|
| Disciplina | 8 (desde jul-2022) | 6,7 meses | **20,9 meses** (ago-2022 → may-2024) |
| Acusación | 15 (desde jul-2022) | 3,4 meses | 10,6 meses (nov-2022 → sep-2023) |

La Comisión de Disciplina **no tuvo una sola sesión ordinaria entre agosto de
2022 y mayo de 2024**: veintiún meses. La serie de sesiones en 12 meses móviles
toca su mínimo justamente en dic-2023 – abr-2024, con **2 sesiones**, y a
partir de ahí **sube y se estabiliza en 5 a 7**, donde sigue hoy.

Es decir: medido así, **el control disciplinario funciona hoy bastante mejor
que al inicio de la gestión**, y el vacío que el indicador buscaba capturar
corresponde al período de crisis de composición del Consejo de 2022-2023.

**Esto contradice la hipótesis del aporte externo**, que esperaba parálisis
creciente. Se documenta tal cual, por el mismo criterio de ADR-0095: el dato
manda sobre la expectativa, y un indicador que se elige o se orienta según el
resultado que produce no es un indicador.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

1. **La fuente queda validada y el universo versionado** en
   `data/politica/denuncias_comisiones_universo.json`: 356 notas relevadas,
   sesiones ordinarias con su número, sesiones sin numerar aparte, acciones
   concretas aparte, huecos calculados y la serie mensual completa.
2. **No se incorpora todavía ningún indicador al ITCP.** Faltan dos decisiones
   editoriales que no corresponde que tome quien construye:
   - **Qué medir.** Sesiones de ambas comisiones en 12m (la serie ya calculada,
     estable, rango 2-7); meses desde la última sesión de Disciplina (más
     directo como «parálisis», más volátil); o acciones concretas en 12m (mide
     control efectivo y no mera reunión, pero son 4 eventos en 20 meses — un
     indicador de evento, con el mismo problema que el veto de
     constitucionalidad de ADR-0131).
   - **Con qué orientación**, que es lo más delicado. Hay que definir qué
     significa para el ITCP que las comisiones de control sesionen más. No es
     obvio que más control disciplinario sea mejor ni peor para la capacidad
     política del gobierno, y ponerle signo sin resolver eso sería arbitrario.
3. **Las dos comisiones no se promedian sin decirlo.** Se comportan distinto:
   Acusación sesiona cada 3,4 meses y produce acciones concretas; Disciplina
   cada 6,7 meses y no publicó ninguna. Si el indicador busca parálisis,
   Disciplina sola es la señal fuerte.

### Consecuencias

- El indicador **nacería discriminando** (ADR-0042): rango 2-7, movimiento mes
  a mes, y hay historia desde jul-2022 para calibrar bandas con datos reales en
  vez de inventarlas.
- Incorporarlo tiene un costo: el ITCP quedó cerrado con auditoría externa 7/7
  el 20-jul-2026, con 6 dimensiones y 12 indicadores puntuando. Sumar uno obliga
  a reponderar y a rehacer la validación externa contra el EPU.
- Queda un supuesto declarado y acotado: asignarle el nº7 de Acusación a la nota
  sin numerar del 20-dic-2023. Quitarlo mueve la serie en una sesión entre
  dic-2023 y dic-2024, y no cambia ninguna conclusión.
