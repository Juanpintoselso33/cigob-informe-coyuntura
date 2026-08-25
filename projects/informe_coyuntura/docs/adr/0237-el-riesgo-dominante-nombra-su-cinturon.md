---
madr: 4
id: '0237'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'transversal'
archivos: ['scripts/generar_informe.py', 'scripts/publicar.py', 'web/src/lib/datos.ts', 'web/src/components/Hero.astro', 'web/src/components/TensionPanel.astro', 'web/src/components/Bluf.astro', 'web/src/components/Archivo.astro', 'web/public/overrides.css', 'tests/test_riesgo_dominante_nombra_su_cinturon.py', 'tests/test_estado_un_solo_criterio.py']
relacionado: ['0181', '0190', '0195', '0204', '0208']
ambito: 'Cómo se expone el veredicto de portada · qué cinturón produjo el barbarismo dominante y qué dice la píldora de estado sistémico'
origen: 'Diego Dequino preguntó en #informe-de-coyuntura si había una inconsistencia en la exposición, con la portada del 25-ago-2026 marcada en dos lugares'
---

# ADR-0237 — El riesgo dominante nombra su cinturón

## Contexto y planteo del problema

El 25 de agosto de 2026 la portada publicaba, en este orden:

- una píldora que decía **«Estable»**,
- la barra general en **«Sin tensión relevante · 3,9/10»**,
- al pie de la barra, **«Riesgo dominante: Político»**,
- y un scroll más abajo, cuatro cards: Macroeconomía 3,6 · **Política 3,3** ·
  **Impacto social 6,1 «Tensión alta»** · Gestión 2,7.

Un lector que ve «Riesgo dominante: Político» busca la card Política, la
encuentra en 3,3 y verde —la segunda más floja del tablero— y concluye que el
veredicto se contradice con su propia tabla.

**No se contradice, y ahí está el problema.** `BARBARISMO_MAP` manda **dos**
cinturones al mismo barbarismo: `politica` y `vida_cotidiana` son los dos
«político». El dominante era Impacto social, con 6,1, y el barbarismo que
produce se llama igual que el otro cinturón. El cálculo era correcto —lo dejó
así [[0208-el-itvc-vive-en-su-modulo-y-el-intermedio-nace-bien]]— y la página
no daba manera de resolverlo: la única línea de todo el informe que ata
«Político» con «Impacto social» estaba en el panel de tensión sistémica, muy
abajo, y en la portada no aparecía.

El ADR-0208 arregló un veredicto **mal calculado**. Éste arregla un veredicto
**bien calculado y mal expuesto**, que desde la butaca del lector se ve igual.

La píldora agravaba la lectura. **«Estable» no es el estado de la tensión
general**: es `alerta_multicinturon ? "Alerta sistémica" : "Estable"`, o sea
«hay menos de dos cinturones tensionados». Pegada a la barra se lee como
veredicto del país, y convivía con un cinturón en tensión alta.

## Factores de decisión

- **El veredicto tiene que poder verificarse contra la tabla que está abajo.**
  Es el criterio con el que se leyó el ADR-0208 y sigue valiendo.
- **Un dato derivado se publica, no se re-deriva.** Si la web tuviera que
  reconstruir qué cinturón produjo el barbarismo, habría una segunda
  implementación de la regla, desincronizable. Es la lección del ADR-0208.
- **El arreglo es de exposición.** Ningún score, banda ni umbral se toca; el
  snapshot regenerado tiene que diferir en el campo nuevo y en nada más.
- **No inventar una escala nueva.** Ya conviven dos particiones sobre la misma
  tensión 0-10 (ver «Lo que queda afuera»); este ADR no agrega una tercera.

## Opciones consideradas

1. **Desambiguar `BARBARISMO_MAP`**: darle a `vida_cotidiana` un barbarismo
   propio para que la palabra identifique al cinturón. Es un cambio de
   metodología —los barbarismos son categorías del marco PES, no etiquetas de
   UI— y con cuatro cinturones y tres barbarismos la colisión es de diseño, no
   un error.
2. **Derivar el cinturón dominante en el front** desde `barbarismo_activo` y
   los scores. Sale sin tocar Python, y deja la regla escrita dos veces.
3. **Publicar `cinturon_dominante` y nombrarlo en la portada** (elegida).

## Decisión

`detectar_barbarismo()` pasa a devolver **`(barbarismo, cinturon_dominante,
alerta)`**: ya elegía el cinturón dominante, sólo lo tiraba. La clave se
publica en el snapshot, en el artefacto intermedio y en el `.md`.

`publicar.py` gana **`recomputar_barbarismo()`**, que corre después de
`recomputar_vida_y_global()` y re-deriva el veredicto sobre los scores ya
finales. Hasta hoy el snapshot **heredaba** el barbarismo calculado en
`generar_informe.py` sobre scores que `publicar.py` todavía podía mover: la
forma exacta del ADR-0208, del lado que aquel ADR no cerró. Hoy es no-op —si
imprime algo, algo se movió—. Y `_reconciliar_intermedio()` copia el veredicto
junto con los scores, para que el artefacto intermedio no quede afirmando un
riesgo dominante que sus propios números ya no sostienen.

En la web, `cinturonDominante()` lee el campo publicado y sólo lo deriva
cuando falta, para los snapshots del archivo anteriores a agosto de 2026 —una
derivación exacta, no aproximada: entre los cinturones que comparten el
barbarismo activo, el de mayor score es el de mayor score de todos—.

Con eso, la portada dice **«Riesgo dominante: Político — Impacto social
(6,1/10)»**, el panel de tensión sistémica repite el nombre en su título y
marca la fila con un tag *Dominante* —distinto del tag *Tensionado*, porque
puede haber dominante sin ningún cinturón tensionado—, y la síntesis
automática y el archivo lo nombran igual.

La píldora deja de decir «Estable» y dice lo que cuenta: **«Sin cinturones
tensionados» · «1 cinturón tensionado» · «Alerta sistémica»**, que es el
insumo literal de la regla matusiana. El caso intermedio usa `is-draft`, el
ámbar que ya existía sin uso en `dashboard.css`: el verde con pulso queda para
cuando no hay ninguno, que no es el mismo estado.

De paso, la línea de frescura decía **«1 indicadores con rezago declarado»**.

### Lo que queda afuera, a propósito

Sobre la misma tensión 0-10 conviven **dos particiones que no coinciden**: los
cortes del semáforo (verde ≤4 · amarillo ≤6 · naranja ≤8 · rojo >8, ADR-0181)
y el campo `estado` (estable ≤3 · en_tension ≤6 · tensionado >6). Por eso
macro en 3,6 se publica como «Sin tensión relevante» y en el snapshot figura
`en_tension`. `CinturonCard.astro` y `TensionPanel.astro` ya documentan que es
**una inconsistencia de metodología, no de front**, y que el rediseño la dejó
de exhibir unificando el canal visual.

Este ADR no la resuelve. Unificarla es una decisión editorial sobre los
umbrales del marco, con efecto sobre la serie histórica y sobre BigQuery, y no
corresponde tomarla dentro de un arreglo de exposición. Queda anotada porque
el global de agosto está en 3,9: **a un decimal** de cambiar de tramo y volver
visible la discrepancia.

### Consecuencias

- El veredicto de portada se puede verificar contra la tabla sin bajar al
  panel de tensión sistémica.
- El snapshot gana un campo; BigQuery lo ignora hasta que alguien lo agregue a
  `bigquery_export.py`, que no es necesario para este arreglo.
- `detectar_barbarismo()` cambió de aridad: cualquier llamador nuevo devuelve
  tres valores.

### Confirmación

- `tests/test_riesgo_dominante_nombra_su_cinturon.py`: el dominante es el de
  mayor score, lo publicado lo nombra en los **dos** artefactos, y el primer
  test verifica la premisa —que dos cinturones sigan compartiendo barbarismo—,
  así que si `BARBARISMO_MAP` se vuelve 1-a-1 el ADR queda marcado como
  revisable en vez de quedar mudo.
- Regeneración de `generar_informe.py` + `publicar.py` sobre el caché de la
  corrida del 25-ago: el snapshot difiere en `cinturon_dominante` y
  `generated_at`, **en ningún otro campo** (diff plano, 0 claves perdidas).
- `recomputar_barbarismo()` y `_reconciliar_intermedio()` no imprimieron nada:
  el veredicto heredado ya coincidía con los scores finales.
- `gate_calidad.py` publica; la suite completa en verde.

## Pros y contras de las opciones

### Opción 1 — desambiguar `BARBARISMO_MAP`

- Bueno: la palabra sola alcanzaría para encontrar el cinturón.
- Malo: cambia la metodología para arreglar un problema de exposición.
- Malo: los barbarismos son tres por definición del marco; forzar un cuarto
  para vida cotidiana inventa una categoría que Matus no tiene.

### Opción 2 — derivar en el front

- Bueno: sale sin tocar el pipeline.
- Malo: dos implementaciones de la misma regla, y la del front no la ve ningún
  test de Python. Es el patrón que el ADR-0208 dejó documentado como caro.

### Opción 3 — publicar el campo (elegida)

- Bueno: una sola implementación, del lado que ya la tenía.
- Bueno: habilita el cinturón de seguridad en `publicar.py`, que faltaba desde
  el ADR-0208.
- Malo: agrega un campo al esquema del snapshot.

## Más información

Lo levantó Diego Dequino en `#informe-de-coyuntura` el 25-ago-2026, con la
portada marcada en dos lugares: el pie de la barra y la card de Impacto
social. Luis Babino agregó que había varias.
