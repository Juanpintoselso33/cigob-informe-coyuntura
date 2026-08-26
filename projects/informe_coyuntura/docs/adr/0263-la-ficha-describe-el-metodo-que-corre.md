---
madr: 4
id: '0263'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'politica'
indicadores: [ratio_dnu, iaf_transferencias, subocupacion_demandante]
archivos: ['web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'web/src/lib/datos.ts', 'tests/test_contrato_publico_dice_lo_que_corre.py']
relacionado: ['0239', '0241', '0249', '0220']
ambito: 'Capa pública · `ratio_dnu`, `iaf_transferencias`, `subocupacion_demandante` · sincronizar la descripción, la fórmula y la ficha con el cálculo que efectivamente corre'
origen: 'Reauditoría post-cambios, 25-ago-2026: discrepancias 2, 3 y 9 — «números corregidos, contrato público todavía viejo»'
---

# ADR-0263 — La ficha describe el método que corre

## Contexto y planteo del problema

Tres ADR de esta misma jornada corrigieron el cálculo de tres indicadores y
dejaron intacto el texto que dice qué miden. La reauditoría los volvió a marcar
como discrepantes **sin que ningún número esté mal**:

- **`ratio_dnu`** (ADR-0241) publica 1,48 = 37/25, contado por el tipo jurídico
  que declara InfoLeg y con la publicación en el Boletín Oficial en los dos
  lados. `descripciones.ts`, `formulas.ts` y la ficha seguían diciendo «DNU
  dictados / leyes sancionadas» y describiendo la búsqueda textual descartada:
  tres convenciones distintas —dictado, sanción, publicación— conviviendo en la
  misma card.
- **`iaf_transferencias`** (ADR-0239) publica +1,6% real deflactando cada flujo
  mensual por el IPC de su propio mes. La fórmula pública seguía mostrando el
  cociente de dos sumas anuales dividido por un IPC promedio —el método que se
  reemplazó justamente porque daba la mitad— y la ficha seguía declarando el CSV
  anual como fuente de los montos.
- **`subocupacion_demandante`** (ADR-0249) publica 7,5% con unidad `% de la
  PEA`. `descripciones.ts` decía «qué porcentaje de los ocupados», que es otro
  denominador. Y el renombre había entrado a la ficha por reemplazo literal de
  la palabra `pluriempleo`, dejando en `operacion` la frase «tasa de subocupación
  demandante (aproximación declarada del subocupacion_demandante)».

El estándar del repositorio es que un indicador mida lo que su nombre y su texto
dicen. Un texto que describe un método que el código ya no usa es del mismo tipo
de error que un número mal calculado, con el agravante de que ningún gate lo
mira: los tres pasaron la suite completa, el gate de calidad y el build.

## Factores de decisión

- **El contrato público tiene que ser único.** Un cociente cuyo numerador se
  describe de tres maneras no se puede reproducir.
- **La verdad es el colector, no el ADR.** Un ADR describe la decisión; lo que
  corre puede haberse implementado con matices (acá: el lado de las leyes sigue
  leyendo el total de resultados, mientras el de los DNU trae el listado entero
  y lo filtra).
- **Los cinco términos de una variación real** —universo, clase de flujo,
  ventana, deflactor y base común— tienen que estar dichos, o la diferencia con
  cualquier otra estimación pública no es discutible.
- **No se toca ningún valor.** Este ADR es de texto: si algún número se moviera,
  el diagnóstico sería otro.

## Opciones consideradas

- **A — Sincronizar los textos y agregar una guarda que compare cada afirmación
  contra el colector.**
- **B — Sincronizar los textos solamente**, confiando en la revisión humana del
  próximo cambio.
- **C — Generar la ficha desde el colector**, de modo que no pueda divergir.

## Decisión

**Opción A.** Los tres contratos quedan escritos una sola vez y en los mismos
términos en las cuatro capas —`descripciones.ts`, `formulas.ts`, `fichas.ts` y
la unidad de `datos.ts`— y se agrega
`tests/test_contrato_publico_dice_lo_que_corre.py`, que cruza cada afirmación
contra el colector o el snapshot que la sostiene.

Los contratos, tal como quedan:

- **`ratio_dnu`** = DNU **publicados** en el Boletín Oficial / leyes
  **publicadas** en el Boletín Oficial, ventana móvil de 365 días, misma
  convención de fecha en los dos lados. Los DNU se identifican por el rótulo
  `Decreto DNU` de la grilla de InfoLeg; la búsqueda por «necesidad y urgencia»
  queda declarada como lo que hoy es, un filtro previo que acota el listado y no
  decide.
- **`iaf_transferencias`** = variación real interanual de los recursos de origen
  nacional girados a **Provincias, C.A.B.A. y Fondo Compensador** (incluida la
  compensación del Consenso Fiscal; afuera Tesoro Nacional, Seguridad Social y
  Fondo A.T.N.), transferencias **automáticas**, **dos años calendario
  completos**, deflactando **cada flujo mensual por el IPC nacional del INDEC de
  su propio mes** (base diciembre de 2016 = 100) antes de sumar los doce.
- **`subocupacion_demandante`** = porcentaje de la **población económicamente
  activa** que trabaja menos horas de las que quisiera y además busca otro
  empleo. El denominador es el mismo que el de la tasa de desocupación.

La opción C es la buena a largo plazo y no entra acá: la ficha tiene secciones
—limitaciones, revisiones, rezago— que ningún colector conoce, así que
generarla entera exigiría moverlas de lugar primero.

### Consecuencias

- **Ningún valor, banda, peso ni serie cambia.** Cambia lo que el texto afirma
  que se midió.
- La ficha de `iaf_transferencias` pierde la limitación «el nombre del archivo
  oficial cambia cada año: hay que apuntar la descarga de nuevo cada enero»:
  desde ADR-0239 el colector resuelve la URL desde la página oficial. Queda en su
  lugar la dependencia que sí existe, la del formato del cuadro.
- La ficha de `ratio_dnu` pierde la limitación «el buscador no expone un listado
  con fecha por norma»: hoy sí lo expone, y de ahí sale el inventario que la card
  publica. Queda la que sí sigue valiendo: no hay descarga masiva, así que la
  serie mensual necesita dos consultas por mes.
- El comentario y el respaldo de `periodoDato()` en `datos.ts` decían que
  `iaf_transferencias` trae «fecha de corrida pero dato anual» y calculaban el
  período como `año − 1`. Desde ADR-0240 su `fecha_dato` es el cierre del año de
  referencia, así que el respaldo apuntaba un año atrás. No se veía porque el
  camino normal usa el campo `periodo`.

### Confirmación

`tests/test_contrato_publico_dice_lo_que_corre.py`, contra el colector y el
snapshot publicado:

- ninguna de las cuatro capas de `ratio_dnu` dice «dictados» ni «sancionadas»,
  y las tres que describen el cociente nombran la publicación en el Boletín
  Oficial;
- el patrón con el que el colector tipifica un DNU sigue siendo el rótulo de la
  grilla, y la ficha lo declara así;
- la fórmula de `iaf_transferencias` deflacta dentro de la suma y no fuera, y
  ficha y fórmula nombran las tres jurisdicciones del universo y el IPC mensual;
- ninguna capa de `iaf_transferencias` sigue prometiendo un IPC promedio anual
  ni el CSV anual como fuente de los montos;
- ninguna capa de `subocupacion_demandante` dice «de los ocupados», y las tres
  que definen el universo dicen PEA;
- la unidad de `datos.ts` coincide con la unidad que el colector escribió en el
  snapshot, para los tres.

Probado rompiéndolo: repuesta la fórmula vieja del IAF, repuesto «de los
ocupados» en la descripción de subocupación y repuesto «DNU dictados» en la
fórmula del ratio, fallan una guarda por cada mutación y ninguna otra.

## Pros y contras de las opciones

### A — Sincronizar y agregar la guarda

- Bueno, porque el próximo cambio de método vuelve a fallar en vez de publicar
  una ficha que describe el método anterior.
- Malo, porque la guarda es por frase y hay que extenderla cuando entra un
  indicador nuevo. Es el costo conocido de este tipo de prueba.

### B — Sincronizar solamente

- Bueno, porque es lo mínimo y cierra las tres discrepancias de hoy.
- Malo, porque es exactamente lo que se hizo en julio con el deflactor del IAF:
  se cambió el método dos veces y el rótulo siguió diciendo `(dic-dic)`.

### C — Generar la ficha desde el colector

- Bueno, porque la divergencia se vuelve imposible.
- Malo, porque la ficha dice cosas que el colector no sabe. Es un rediseño, no
  una corrección.

## Más información

- Reauditoría post-cambios, 25-ago-2026:
  `docs/auditoria_indicadores/260825_reauditoria_post_cambios_completa.md`.
- [[0220-la-ficha-se-ata-al-colector-y-al-adr]] puso las tres guardas
  genéricas de ficha; ninguna podía ver esto, porque las tres comparan la ficha
  con el snapshot y acá el snapshot está bien.
