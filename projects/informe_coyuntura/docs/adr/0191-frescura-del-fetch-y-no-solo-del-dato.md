---
madr: 4
id: '0191'
estado: 'aceptado'
fecha: 2026-08-12
cinturon: 'transversal'
indicadores: [judicializacion]
archivos: ['scripts/gate_calidad.py', 'scripts/publicar.py', 'scripts/macro.py', 'scripts/politica.py', 'scripts/gestion.py', 'scripts/espiritu_epoca.py', _sellar, _sellar_vida, _carry_forward, 'G2B_MAX_DIAS', 'tests/test_gate_frescura_fetch.py', 'tests/test_sello_obtenido_en.py']
relacionado: ['0037', '0133', '0135', '0168', '0170', '0174', '0210']
ambito: 'Sello `obtenido_en` en los cinco cinturones · chequeo G2b en el gate de calidad'
origen: 'Auditoría de salud del pipeline, 2026-08-11: judicializacion llevaba 12 días publicándose desde cache sin que ningún gate lo dijera.'
---

# ADR-0191 — El gate mide la frescura del dato pero no la del fetch, y por eso una fuente puede caerse en silencio

## Contexto y planteo del problema

`judicializacion` se publicó doce días seguidos desde cache —del 31-jul al
11-ago de 2026— sin que ningún gate fallara. SAIJ le devuelve **403 a todas las
corridas del pipeline** y el indicador nunca se obtuvo en vivo desde que
[ADR-0170](0170-judicializacion-y-paralisis-pasan-a-fuente-viva.md) lo declaró
fuente viva. Se encontró mirando los snapshots a mano, no por un aviso.

La causa no es que faltara un chequeo de frescura: G2 existe y mide exactamente
eso. El problema es **qué** mide. G2 compara `fecha_dato` contra un tope por
indicador, y `fecha_dato` es la fecha del DATO, no la del intento de obtenerlo.
En una serie anual las dos cosas se divorcian: el punto del año en curso se
fecha al 1-ene y no se mueve durante 365 días **ande o no ande el fetch**. Por
eso el tope de `judicializacion` es de 430 días, y el comentario que lo
justifica dice, textualmente, que "el punto del año en curso se recalcula en
cada corrida".

Ahí está la trampa: la holgura se escribió asumiendo que el número se recalcula
todas las noches, y terminó tapando que no se recalcula nunca. El único otro
control es `CARRY_FORWARD_MAX`, un presupuesto de desactualizados **por
cinturón** (40%): un solo indicador clavado entre los 18 de política da 5,6% y
no lo dispara jamás. Queda en aviso, para siempre.

El agujero no es de SAIJ ni de este indicador. Alcanza a **cualquier indicador
cuya fecha se mueva más lento que su refresco**, que en este proyecto son
todos los anuales y trimestrales — justo los que tienen los topes más
generosos, o sea los que más tardarían en delatarse.

## Factores de decisión

- El dato que hace falta —hace cuánto que la fuente contestó por última vez— no
  existe en ningún lado del snapshot.
- No puede introducir una ola de falsos positivos: un gate que grita de más se
  empieza a ignorar, y sería peor que el silencio de hoy.
- Los indicadores manuales y los derivados de series no tienen fetch propio: un
  chequeo de frescura de fetch no significa nada para ellos.
- El refresco de `judicializacion` va a ser manual y mensual por un tiempo (ver
  "Consecuencias"), así que el umbral tiene que ser configurable por indicador,
  no uno global.

## Opciones consideradas

- **Bajar el tope de G2 para los anuales**: no sirve. `fecha_dato` no se mueve
  aunque el fetch ande bien, así que bajar el tope hace fallar corridas sanas.
  El problema no es el número del tope, es la magnitud que se está midiendo.
- **Deducirlo de `desactualizado`**: descartado tras verificarlo. La bandera
  conflaciona dos cosas distintas — "esto vino del cache" y "este valor está
  degradado". Hay al menos tres fetchers que la ponen en `True` sobre una
  obtención EXITOSA (`tcrm` cuando cae a la serie INDEC discontinuada,
  `rigi_inversiones` que es un proxy, y las entradas manuales de gestión). Con
  esa deducción los tres quedarían marcados como nunca obtenidos y fallarían el
  gate para siempre: el falso positivo que hay que evitar.
- **Deducirlo comparando el snapshot con el anterior**: descartado. El
  carry-forward produce una entrada idéntica a la previa salvo la bandera, así
  que un fetch exitoso que devuelve el MISMO valor es indistinguible de uno que
  no corrió. Es precisamente el caso de este indicador.
- **Sellar en el colector, en el punto donde el resultado se acepta como
  fresco**: es el único lugar donde la distinción existe sin ambigüedad.

## Decisión

Se agrega **`obtenido_en`** a la card: el momento en que ese valor se obtuvo de
la fuente en vivo. Lo pone un helper `_sellar()` en los cuatro colectores con
patrón `frescos`/cache (macro, política, gestión, espíritu de época) y
`_sellar_vida()` en `publicar.py` para vida cotidiana, que se arma distinto.

Lo que hace que el campo mida algo es que el **carry-forward NO lo toca**: los
colectores arrastran con `{**anterior, "desactualizado": True}`, que ya preserva
el sello viejo, y en vida se preserva explícitamente. Es esa fecha que deja de
moverse la que envejece sola y delata la caída.

El gate gana **G2b**: si un indicador tiene sello y pasaron más de
`G2B_MAX_DIAS` días desde entonces, es falla. Por defecto 30 días, con override
por indicador igual que `MAX_DIAS`.

**Un indicador sin `obtenido_en` se saltea.** Eso cubre a los manuales y a los
derivados de series (`mora_familias` sale de la serie, no de un fetch: su
frescura la controla G3 contra la serie). Y da un despliegue sin ruido: el campo
aparece la primera vez que cada indicador se obtiene bien, así que el chequeo se
enciende solo, indicador por indicador, a medida que se demuestra que funciona.

Un sello ilegible es falla, no un saltear — degradarlo a "sin sello" reabriría
el agujero por la puerta de atrás.

### Consecuencias

- Un congelamiento pasa de ilimitado y mudo a **acotado**. Conviene ser
  preciso sobre qué compra esto y qué no: con el default de 14 días, una fuente
  que se cae corta la publicación a las dos semanas. NO da un aviso a las 48
  horas — este caso concreto, 12 días, no lo habría disparado. Lo que elimina
  es el "para siempre", que era el problema real: hoy `judicializacion` podría
  seguir congelada en 2027 sin que nada fallara.
- `judicializacion` arranca con tope de **45 días**, no con el default de 14.
  Es una decisión explícita, no una excepción técnica: **el acceso a SAIJ no se
  resuelve todavía** y hasta entonces el refresco es manual desde una IP
  argentina, al ritmo mensual con que se presenta el informe. Los 45 días dejan
  margen sobre ese ciclo sin volver a permitir que se congele en silencio.
- El sello no llega retroactivo. Hasta que cada indicador se obtenga bien una
  vez, G2b no lo mira — incluido `judicializacion`, que sólo lo va a conseguir
  en la próxima corrida manual desde Argentina. Es el precio de no inventar una
  fecha que no se sabe.

### El pendiente: el egreso bloqueado

Medido el 12-ago-2026 con un workflow descartable (commits `556c41f`/`fff99f4`,
run 31548730139), desde el runner del pipeline:

```
egreso  20.168.137.14 — AS8075 Microsoft, San Jose US (Azure West US)
SAIJ    403 con los tres User-Agent (colector, navegador, sin UA)
        199 bytes, Server: Apache, sin rastro de WAF
control CEPA 200 · CAFAM 200 · datos.gob.ar 200 · infoleg.gob.ar 200
```

`infoleg.gob.ar` es el control que cierra el diagnóstico: mismo ecosistema que
SAIJ/Infojus, 200 desde la misma IP en el mismo segundo. No es la red del
runner, no es el User-Agent, no es la hora (los `workflow_dispatch` de las 08:32
y 12:35 ART también dieron 403) ni rate limiting (el 403 llega en la primera
consulta). `robots.txt` de SAIJ no declara `/busqueda`, y desde una IP argentina
la misma URL devuelve 200 con las 22 requests del loop en 2,3 s.

Pedir el desbloqueo no es viable como está: GitHub publica 7.297 rangos para
Actions. Sí sería viable con un egreso propio de IP fija, que es la salida
pendiente de evaluar — y de los cinco egresos probados sólo el argentino
funcionó de forma reproducible (Azure, Jina y un proxy público dieron 403).

No se intenta ningún bypass, en línea con
[ADR-0037](0037-cohesion-bloque-scraping-bloqueado-antibot.md).

## Pros y contras de las opciones

- Bueno, porque mide la magnitud correcta en vez de ajustar el umbral de una
  magnitud que no sirve para esto.
- Bueno, porque generaliza: no es un parche para SAIJ, y el próximo indicador
  que se congele no va a ser éste.
- Bueno, porque se enciende solo y no puede producir una ola de falsos
  positivos el día que se despliega.
- Malo, porque el helper está duplicado en cuatro colectores — es el idioma que
  ya usan (`_warn`, `HTTP_HEADERS` también están duplicados), pero si divergen
  G2b miente en un cinturón. Hay un test que compara los cuatro.
- Malo, porque `mora_familias` y las cards manuales quedan fuera del chequeo.
  Es correcto —no tienen fetch— pero significa que G2b no cubre el 100% del
  snapshot y conviene no leerlo como si lo hiciera.

## Más información

- El diagnóstico completo del bloqueo está arriba; el workflow que lo midió se
  recupera con `git checkout 556c41f -- .github/workflows/diagnostico-saij.yml`.
- [ADR-0133](0133-una-fuente-demorada-no-tira-abajo-el-pipeline.md) separó "fuente caída"
  de "script roto". G2b agrega la tercera: fuente caída **que no se levanta**.
- [ADR-0174](0174-g3-verifica-cards-frescas.md) ya había reconocido que una card
  en carry-forward es un valor de otro momento; lo que faltaba era ponerle
  vencimiento a ese otro momento.
