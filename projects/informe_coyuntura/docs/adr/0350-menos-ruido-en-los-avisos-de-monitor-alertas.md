---
madr: 4
id: '0350'
estado: 'aceptado'
fecha: 2026-10-08
cinturon: 'transversal'
archivos: ['scripts/aviso_slack.py', 'scripts/aviso_cambio_claude.py', '.github/workflows/data-pipeline.yml', '.github/workflows/cambios-desde-claude.yml', 'tests/test_avisos_menos_ruido.py', 'tests/test_aviso_cambio_claude.py', 'tests/test_avisos_hilos.py']
relacionado: ['0175', '0270', '0309', '0334']
ambito: 'Operación · qué llega al canal #monitor-alertas y qué se queda en el log, el issue o el hilo'
origen: 'Juan, 8-oct-2026: de las 91 notificaciones del canal desde el 25-ago, 52 no le pedían nada a nadie'
---

# ADR-0350 — Menos ruido en los avisos de #monitor-alertas

## Contexto y planteo del problema

La regla del canal es «sólo lo accionable» (ADR-0270) y cada problema tiene su
hilo (ADR-0309). Aun así, contadas el 8-oct-2026 las 91 notificaciones desde el
25-ago, **52 (57 %) no le pidieron nada a nadie**. Cinco casos explican casi
todas:

1. **Una causa, veintiún avisos.** El 22-sep un `config` roto hizo fallar 21
   indicadores con `cannot import name '…' from 'config'` (once nombres
   distintos, un solo error). Salieron 21 🟡 y, al arreglarse, 21 ✅: 42
   mensajes por un bug.
2. **Culpar a un cambio por lo que ya estaba roto.** Los PR #59 a #62 desde
   claude.ai dispararon cuatro 🔴 «se publicó con algo roto». Las tres pruebas
   rojas las dejaron #59 (una) y #60 (dos); los 🔴 de #61 y #62 las repetían y
   le echaban la culpa a cambios que no las rompieron (#62 sólo tocó
   `web/src/pages/[slug].astro`).
3. **Un tope que se leía como falla.** El 7-oct el aviso «después del cambio
   #57, el deploy de Vercel falló» era el tope diario de deploys del plan
   Hobby (el status del commit decía «Deployment rate limited — retry in 24
   hours»), y el aviso pedía «pedirle a Claude que lo deshaga».
4. **Lo que se arregla solo.** `validacion` («la fuente está caída entera» y
   su timeout) se arregló sola en dos noches; nadie podía hacer nada. «Postura
   pública de la UIA» lleva abierto desde el 17-sep por «AEA muda», cuyo propio
   texto dice que se resuelve solo y que AEA ya está fuera del cálculo
   (ADR-0334).
5. **Cada ✅ salía al canal.** La respuesta de cierre iba con broadcast para
   todo problema: 32 respuestas al canal.

## Factores de decisión

- Lo que sigue pidiendo algo tiene que seguir sonando igual que hoy: un error
  de código en la primera corrida (ADR-0175), un cotejo que hay que hacer, un
  🔴 de corrida caída y su cierre.
- Callar en Slack no es borrar: el log de la corrida y el issue de GitHub
  siguen siendo el registro completo.
- Nada que dependa de correr pytest dos veces (son ~4 minutos por cambio).
- Ningún permiso nuevo para la app de Slack.

## Opciones consideradas

1. Bajar el volumen con reglas por clase de aviso: agrupar por causa común,
   comparar contra el estado de `main`, umbral para lo que suele arreglarse
   solo, una lista explícita de cotejos callados y ✅ sin broadcast para los 🟡.
2. Un resumen diario en lugar de avisos sueltos.
3. Dejarlo como está y silenciar el canal a mano.

## Decisión

Opción 1, en cuatro reglas.

**1. Una causa común es un problema** (`aviso_slack.py`). Si
`UMBRAL_CAUSA_COMUN` (3) indicadores o más fallan en la misma corrida con la
misma firma de error que no es de red, se avisa un solo problema con clave
`causa:<firma>`: «N indicadores no se actualizan por el mismo error de código:
`<error>`», con los rótulos públicos de las cards (hasta `TOPE_ROTULOS`, 8, y
«y M más»). La firma es el tipo de excepción, si el mensaje lo trae, más el
mensaje sin rutas absolutas, URLs, ids, números ni el nombre concreto que falta
en `name '…'` / `attribute '…'` (los colectores escriben `str(e)`, sin tipo).
Un hilo, un ✅. Si el grupo se achica, se edita la raíz; mientras el hilo esté
abierto sigue agrupado aunque quede por debajo del umbral. Con menos de tres
indicadores, un hilo por indicador como hasta ahora.

**2. Los cambios desde claude.ai se comparan contra `main`**
(`aviso_cambio_claude.py`, `cambios-desde-claude.yml`).

- Cada cambio se mergea pase lo que pase, así que el conjunto de pruebas rojas
  con que termina su validación **es** el estado de `main`. Se guarda en un
  artifact de Actions (`estado-avisos-cambios`, 90 días) y el cambio siguiente
  lo compara: el 🔴 sólo nombra las pruebas que fallan ahora y no fallaban
  antes, y menciona cuántas ya estaban rojas. No se corre pytest dos veces.
  Artifact y no cache: la cache de un `pull_request` sólo la ve ese mismo PR.
- Si el cambio no rompió nada pero `main` ya tenía rojas, no se lo culpa: se
  abre **un** hilo 🟡 «main tiene N pruebas en rojo de antes» (clave = el
  conjunto), y cada cambio que cae encima edita la raíz («lleva N cambios
  encima: #61, #62») sin mensaje nuevo. Si el conjunto se achica, se edita;
  si aparecen heredadas que el hilo no tenía, el viejo se cierra con «main
  sigue con pruebas en rojo» (no con ✅) y se abre otro. Se cierra cuando un
  cambio pasa todo o cuando la corrida nocturna pasa pytest sobre `main` (modo
  `verde`). La corrida nocturna sólo corre pytest, así que borra del estado
  únicamente las fallas de pytest: las de tipos o build las limpia el próximo
  cambio en verde. Si Slack no confirma un cierre, queda en
  `cierres_pendientes` y se reintenta en la próxima corrida (estos tres
  ajustes vienen de la revisión de Codex, después del merge).
- Si el status de Vercel del commit dice que fue el tope de deploys («rate
  limited», «Resource is limited» o «api-deployments-free-per-day»), no es una
  falla del cambio: 🟡 aparte, uno por tope (los cambios que caen dentro se
  suman editando la raíz), que dice que la gente ve la versión anterior, que
  no hay nada que deshacer y cuándo se libera (la hora sale del «retry in N
  hours» del status; si no, «≈24 h»). Si la descripción no se puede leer, el
  🔴 de siempre.
- Sin estado previo, o con una validación caída cuyo log no se puede leer, se
  culpa al cambio por todo, como antes: es el lado seguro.
- El resto no cambia: cambio sensible, cambio grande, deploy caído de verdad,
  página que no carga, corrida de datos fallida.

**3. Callar lo que no pide nada** (`aviso_slack.py`).

- `COTEJO_SE_RESUELVE_SOLO`, la versión para cotejos de
  `DEGRADACION_ESPERADA`: incidencias `[COTEJO_MANUAL]` que se resuelven solas
  y ya están fuera del cálculo. Una entrada exige indicador, patrón del
  registro y el ADR que lo decidió, y además el motivo tiene que decir «fuera
  del cálculo» y «se resuelve solo»: si AEA vuelve al perímetro, el colector
  escribe otro motivo y el aviso vuelve a sonar sin tocar la lista. Arranca
  con una sola entrada, `apoyo_empresario` / «AEA muda desde …», decidida en
  ADR-0334. Un comunicado de UIA sin codificar, del mismo indicador, sigue
  avisando. Se calla sólo en Slack: sigue en el log y en el issue.
- Una fuente caída entera (exit=2) o un colector que agota su presupuesto
  salen al canal recién en la corrida `UMBRAL_CORRIDAS_FUENTE` (3) seguida;
  antes se cuentan en el estado y quedan en el log. Si se arreglan antes, no
  hay ni 🟡 ni ✅. Un presupuesto agotado ya no suma además un «fuente caída»
  del mismo colector: el workflow lo mapea a exit=2 y es el mismo evento.
  Una corrida caída en el medio no reinicia ni suma la cuenta. Los errores de
  código siguen avisando en la primera.

**4. Al canal, sólo los ✅ del rojo.** La raíz pasa a ✅ siempre. La respuesta
en el hilo sale también al canal (`reply_broadcast`) sólo si el problema era
🔴, que incluye «la corrida nocturna vuelve a publicar»; para un 🟡 queda en el
hilo, sin broadcast.

### Consecuencias

Reproducido con fixtures en el formato que produce el runner:

| Día | Antes | Ahora |
|---|---|---|
| 22 al 24-sep (21 indicadores, un error) | 21 🟡 + 21 ✅ al canal = 42 | 1 🟡 al canal; el ✅ queda en el hilo |
| 8-oct (#59 a #62) | 4 🔴, dos con la culpa equivocada | 2 🔴 (#59 y #60, cada uno con lo suyo) + 1 🟡 «main tiene 3 pruebas en rojo» editado por #62 = 3 |
| 7-oct (#57, tope de Vercel) | 1 🔴 que pedía deshacer el cambio | 1 🟡 que dice que no hay nada que deshacer |
| 17 al 19-sep (`validacion`) | 2 🟡 + 2 ✅ | nada |
| «AEA muda» desde el 17-sep | 1 🟡 abierto, editado cada noche | nada |

- El primer cambio desde claude.ai después del merge no tiene estado previo y
  avisa como antes. Lo mismo si el artifact vence (90 días sin cambios ni
  corrida nocturna en verde).
- Dos cambios desde claude.ai que terminan al mismo tiempo leen el mismo
  estado y el segundo pisa al primero. El costo es a lo sumo un aviso de más o
  de menos sobre pruebas heredadas; no se agrega `concurrency` global porque
  frenaría los merges.
- Un `main` que se arregla con un push humano (no desde claude.ai) cierra el
  hilo de pruebas rojas recién en la corrida nocturna siguiente.
- El hilo abierto de «Postura pública de la UIA» se cierra en la primera
  corrida nocturna después del merge, con la raíz en ✅ y la respuesta en el
  hilo, sin broadcast (si para entonces no hay un comunicado de UIA sin
  codificar, que sí seguiría abierto).
- Una fuente que cae tres noches sigue avisando en la tercera; las dos
  primeras sólo están en el log. Se aceptó a cambio de las 4 notificaciones
  de `validacion`.

### Confirmación

- `tests/test_avisos_menos_ruido.py`: el 22-sep agrupado con rótulos y tope,
  el grupo que se achica, menos del umbral por indicador, errores distintos
  separados, la fuente caída hasta la tercera corrida, la que vuelve antes sin
  decir nada, el presupuesto como un solo problema, la corrida caída que no
  toca la cuenta, el error de código que avisa en la primera, AEA callada, el
  comunicado de UIA que sí avisa, AEA dentro del perímetro que vuelve a sonar,
  la lista que sale de un ADR aceptado, el issue que sí lleva el cotejo y el
  ✅ de la corrida que sí sale al canal.
- `tests/test_aviso_cambio_claude.py`: el 8-oct completo, el cierre por un
  cambio en verde y por la corrida nocturna, el conjunto que cambia, sin
  estado previo, sin log legible, el tope de Vercel (amarillo, una vez por
  tope, la hora o «≈24 h», sin status legible es el rojo, tope más página
  caída) y que los dos workflows traen, pasan y guardan el estado.
- `tests/test_avisos_hilos.py`: el ✅ de un 🟡 queda en el hilo.
- Diecisiete mutaciones —sin agrupar, firma que no borra el nombre, grupo
  abierto que no sigue agrupado, cotejo callado apagado, callar sin mirar el
  motivo, callar también en el issue, umbral de fuentes en 1, aviso de un
  pendiente que se fue, broadcast siempre, broadcast nunca, cambio sin
  comparar contra main, hilo que no cuenta cambios, `verde` que no cierra, tope
  no detectado, un aviso por cambio en el tope, workflow sin estado, nocturna
  sin `verde`— hacen fallar al menos una prueba cada una.

## Pros y contras de las opciones

- **1. Reglas por clase.** Bueno: cada regla ataca un caso medido y deja
  intacto lo accionable. Malo: suma estado (un artifact) y una lista que hay
  que mantener con criterio.
- **2. Resumen diario.** Bueno: un solo mensaje por noche. Malo: es el ruido
  que ADR-0270 sacó del canal, y un 🔴 urgente esperaría al resumen.
- **3. Silenciar a mano.** Bueno: nada que programar. Malo: se pierde también
  lo accionable, que es la razón de que exista el canal.

## Más información

- ADR-0270: el aviso dice qué falló; reglas de fixtures y `failure() ||
  cancelled()`.
- ADR-0309: un hilo por problema; el estado en la cache de Actions.
- ADR-0175: por qué un error que no es de red avisa siempre.
- ADR-0334: AEA fuera del perímetro, y por qué su silencio es señal y no tarea.
- `CLAUDE.md`, sección «Avisos del pipeline».
