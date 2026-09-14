---
madr: 4
id: '0309'
estado: 'aceptado'
fecha: 2026-09-14
cinturon: 'transversal'
archivos: ['scripts/aviso_slack.py', 'scripts/cotejo_manual.py', '.github/workflows/data-pipeline.yml', 'tests/test_avisos_hilos.py']
relacionado: ['0270']
ambito: 'Operación · ciclo de vida de los avisos del Monitor en Slack'
origen: 'Tres noches seguidas del mismo 🟡 sin decir de qué producto ni que era la misma falla, y ningún aviso cuando se resolvió'
---

# ADR-0309 — Un hilo por problema en los avisos

## Contexto y planteo del problema

ADR-0270 hizo que el aviso diga **qué** falló. Faltaba lo otro: que diga **de
qué** habla y **cuándo terminó**. Del 12 al 14-sep-2026 un indicador del
cinturón político quedó congelado por un error de código, y #alertas recibió
el mismo 🟡 tres noches seguidas, como tres mensajes sueltos. Cuando se
arregló no llegó nada: una corrida limpia no manda mensajes, y ese silencio no
se distingue de un bot que no corrió.

El 🟢 existía, pero sólo después de un 🔴 y como mensaje suelto. Los 🟡 no
tenían cierre ni memoria. Y ningún aviso nombraba el producto: «el pipeline» o
«la web» a secas, en un canal que no tiene por qué ser sólo del Monitor.

## Factores de decisión

- Un problema que sigue abierto se tiene que leer como **uno**, no como N.
- Todo problema tiene que terminar con un aviso visible de que se resolvió.
- ADR-0270 sigue valiendo: sólo lo accionable entra al canal.
- El estado entre corridas no puede depender de que la corrida commitee: la
  corrida caída es justo la que abre el aviso.
- Sin permisos nuevos para la app de Slack (reinstalar obliga a rotar el token).

## Opciones consideradas

1. Mensajes sueltos, como estaba, con el nombre del producto en la cabecera.
2. Un hilo por problema con estado en un JSON commiteado a `main`.
3. Un hilo por problema con estado leído del historial del canal.
4. Un hilo por problema con estado en la cache de GitHub Actions.

## Decisión

Opción 4. Cada problema tiene una clave estable (`corrida` para el 🔴,
`err:<indicador>`, `caida:<colector>`, `presupuesto:<colector>`,
`cotejo:<indicador>`, `bigquery`) y un mensaje raíz:

- **aparece** → mensaje nuevo con el producto, qué ve la gente en la web, por
  qué y qué hacer; el indicador se nombra con el rótulo de su card
  (`datos.ts`), no con su clave;
- **sigue abierto** → se edita la raíz con «lleva N corridas» (`chat.update`
  no notifica); si cambió el diagnóstico, se responde en el hilo;
- **desaparece** → respuesta en el hilo con `reply_broadcast`, que sale
  también en el canal («✅ se resolvió…»), y la raíz pasa a ✅ con cuánto duró.

Una corrida caída sólo puede cerrar el hilo `corrida`: las degradaciones esa
noche no se midieron. Si Slack no confirma un cierre, el problema queda
abierto y se reintenta en la próxima corrida.

Lo que agregó la revisión de Codex antes de mergear:

- **Los hilos son de `main`.** Una corrida manual sobre otra rama no publica
  producción, así que no restaura ni guarda el estado y no puede dar por
  resuelto nada; si avisa, avisa suelto.
- **Una corrida a la vez** (`concurrency`, sin cancelar): dos solapadas
  leerían el mismo estado y duplicarían hilos.
- **El cierre son dos pasos que se reintentan por separado**: si el ✅ salió
  al canal pero falló la edición de la raíz, la próxima corrida sólo reintenta
  la edición.
- **Si la raíz ya no existe** (`message_not_found` y afines), se abre otra con
  el cuerpo completo en vez de seguir editando un mensaje que no está.

El canal pasa a llamarse #monitor-alertas. El ID no cambia, así que ni el
secreto ni el bot se tocan.

### Consecuencias

- El 🟢 suelto del loop que cierra el issue desaparece: su lugar lo ocupa el
  cierre del hilo `corrida`. El issue de GitHub se sigue abriendo y cerrando
  igual; es el registro, el hilo es la notificación.
- Si la cache se pierde (GitHub la borra tras 7 días sin uso, o sea con el
  pipeline parado una semana), un problema abierto se vuelve a anunciar como
  nuevo y su hilo viejo queda sin ✅. Degrada a lo que había antes, no a
  silencio.
- Los mensajes viejos de #alertas, anteriores a esto, no se cierran.

### Confirmación

`tests/test_avisos_hilos.py` fija el ciclo con un Slack falso: problema nuevo,
tres corridas con un solo mensaje, cambio de diagnóstico en el hilo, cierre
con broadcast, corrida caída que no cierra degradaciones, cierre no confirmado
que queda abierto, edición del cierre reintentada sin repetir el ✅, raíz
borrada que se reabre, y que el workflow restaura, pasa y guarda el estado
siempre, sólo en `main` y con `concurrency`.
Dos mutaciones (cerrar degradaciones desde una corrida caída; no editar la
raíz) hacen fallar la suite.

## Pros y contras de las opciones

- **1. Sueltos:** trivial, pero no resuelve ni la repetición ni el cierre.
- **2. JSON en `main`:** auditable, pero los avisos corren después del commit
  y una corrida caída no commitea; habría que commitear aparte y cada push a
  `main` dispara un build de Vercel.
- **3. Historial del canal:** sin estado propio, pero exige `channels:history`,
  que la app no tiene documentado; sumarlo obliga a reinstalar y rotar el token.
- **4. Cache de Actions:** funciona en fallas y cancelaciones, no toca `main`
  ni Vercel; su única debilidad es la expiración, que degrada a mensajes
  sueltos.

## Más información

- ADR-0270: qué dice el aviso.
- `CLAUDE.md`, sección «Avisos del pipeline».
