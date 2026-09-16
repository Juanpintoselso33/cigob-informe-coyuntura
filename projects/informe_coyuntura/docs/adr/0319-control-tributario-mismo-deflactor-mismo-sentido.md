---
madr: 4
id: '0319'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'macro'
indicadores: [recaudacion]
archivos: ['scripts/macro.py', 'web/src/lib/fichas.ts', 'tests/test_macro_recaudacion_dgi.py']
relacionado: ['0078', '0152', '0239', '0318', '0321', '0329']
ambito: 'Cinturón Macro · `recaudacion` · método de cómputo del control tributario (IVA-DGI, cheque)'
origen: 'Continuación de ADR-0318: cómo se calcula el control sin inventar un deflactor propio'
---

# ADR-0319 — El control tributario usa el mismo deflactor y compara el mismo sentido

## Contexto y planteo del problema

ADR-0318 decide QUE IVA-DGI y créditos/débitos bancarios (impuesto al cheque)
entran como control de `recaudacion`. Falta decidir CÓMO se calculan para que
la comparación contra el agregado sea honesta: con qué deflactor, en qué
unidad, y qué cuenta como «mismo sentido» o «divergencia».

Dos trampas ya documentadas en este repo aplican directo acá:

- **ADR-0078** — el IPC como deflactor compartido no es un error independiente
  por indicador: si el IPC está mal medido, todo lo que se deflacte con él se
  equivoca junto y coordinado. Inventar un segundo deflactor «propio» para
  IVA o cheque no arreglaría eso — sumaría una fuente de error más sin sacar
  la que ya existe.
- **ADR-0239** — un deflactor de calendario (peso igual por mes) distorsiona
  cuando el flujo no se reparte parejo en el año. Ahí aplicaba a una SUMA
  ANUAL de flujos mensuales (`iaf_transferencias`). Acá no aplica de la misma
  forma: el control lee un mes puntual contra el mismo mes de hace un año
  (variación interanual), no una suma de doce meses — no hay ponderación de
  calendario que corregir porque no se promedia nada.

## Factores de decisión

- No inventar un deflactor propio (instrucción explícita del encargo, y
  consistente con ADR-0078).
- El agregado (`serie`, la salida de `comarb.base_imponible_real_sa`) ya está
  deflactado y desestacionalizado — no hay que tocarlo para volver a
  deflactarlo.
- La comparación tiene que quedar en una unidad común para que «mismo
  sentido» signifique algo.

## Opciones consideradas

1. Comparar el NIVEL del agregado (100 = 4T-2023) contra la variación i.a. de
   IVA/cheque — unidades distintas, la comparación de sentido no es directa.
2. Reconstruir el nominal combinado (DGI + COMARB) y deflactarlo aparte para
   sacarle una interanual, además de la que ya usa el nivel.
3. Leer la variación interanual real del propio agregado desestacionalizado
   (`serie[ym] / serie[ym-12] - 1`) y comparar esa magnitud, en la misma
   unidad, contra la interanual real de IVA-DGI y cheque calculada con
   `_real_ia_pm3` (la misma función y el mismo IPC que ya usa el resto del
   cinturón, hoy sin uso desde que `recaudacion` pasó a nivel en ADR-0152).

## Decisión

Opción 3. `_control_tributario()` en `scripts/macro.py`:

- Calcula la interanual real de IVA-DGI y de cheque con `_real_ia_mensual(nominal,
  ipc)` — mismo IPC que deflacta el agregado, misma aritmética que ya usaba
  `recaudacion` antes de ADR-0152 y que sigue usando el resto de Macro
  (`_indec_yoy`, `_desequilibrio_monetario_serie_mensual`). La función se
  llamaba `_real_ia_pm3`; el nombre sugería un promedio móvil de 3 meses que
  nunca calculó (es interanual simple, mes contra el mismo mes del año
  anterior) — se corrigió el nombre al escribir esta corrección.
- Calcula el sentido del agregado como la interanual real de su propia serie
  ya desestacionalizada (`serie[ym] / serie[ym-12] - 1`): al ser interanual,
  compara el mismo mes calendario contra el año anterior y cancela la
  estacionalidad por construcción, sin reintroducir un segundo deflactor.
- Declara divergencia cuando el signo del agregado no coincide con el signo
  de IVA-DGI **o** con el de cheque — la lectura que pidió el equipo es
  justamente esa: si el agregado sube y los dos impuestos ligados a actividad
  bajan, la suba no viene (sólo) de actividad. El signo se calcula sobre los
  valores YA redondeados a un decimal (los que se publican), con una banda
  muerta de 0,05: lo que se muestra como 0,0% no cuenta como un sentido para
  ninguna de las tres series. Sin esto, un agregado +0,04%/IVA −0,04% publicaba
  literalmente "agregado 0,0%, IVA -0,0%... van en sentidos distintos", y tres
  ceros exactos SÍ marcaban `diverge=False` — inconsistente en el propio
  entorno del cero.
- El punto común más reciente entre las tres series puede quedar varios meses
  detrás de la card si IVA-DGI o cheque no publicaron todavía; sin tope,
  `comunes[-1]` retrocedía sin límite y el resultado se mostraba sin ninguna
  marca de desfasaje. Se acota a `MAX_RETROCESO_DESCOMPOSICION_MESES = 3`: más
  allá de eso no hay descomposición ese mes; dentro del tope se publica con
  `meses_atraso` para que el texto lo declare.
- Es best-effort: si falta un mes común utilizable entre las tres series, no
  hay control ese mes y la card de `recaudacion` publica igual (ADR-0318).

### Consecuencias

- El control queda en la misma unidad (% interanual real) para las tres
  series, así que «mismo sentido» y «divergencia» se leen sin traducir nada.
- `_real_ia_mensual` (ex `_real_ia_pm3`), que había quedado sin uso desde el
  29-jul-2026 (ADR-0152 cambió `recaudacion` de variación a nivel), vuelve a
  tener un caller.
- El control no dice nada sobre magnitud relativa, sólo sobre sentido: un mes
  donde el agregado sube 10% y el IVA sube apenas 1% cuenta como «mismo
  sentido», aunque la brecha sea grande. Eso es deliberado — separar «sentido»
  de «magnitud» evita que el control emita un juicio de calibración que no le
  corresponde.
- **Ver ADR-0321**: el encuadre de este ADR y de ADR-0318 —"control
  independiente"— es incorrecto. IVA-DGI y cheque son componentes del propio
  agregado DGI, no una fuente aparte. El método de cómputo que describe este
  ADR (deflactor, unidad, banda muerta, tope de retroceso) sigue vigente; lo
  que cambia es cómo se nombra y qué se afirma con el resultado.

### Confirmación

`tests/test_macro_recaudacion_dgi.py::test_control_tributario_*`: con datos
sintéticos, un agregado que sube 10% real i.a. mientras IVA y cheque caen 10%
cada uno marca `diverge=True`; el mismo agregado con IVA y cheque subiendo
también 10% marca `diverge=False` (control negativo: descarta un guard que
devolviera `diverge=True` siempre); sin mes común, `_control_tributario`
devuelve `None` en lugar de fallar; más de tres meses de atraso entre IVA/cheque
y la card también devuelve `None`; un mes de atraso (dentro del tope) publica
con `meses_atraso=1`; el entorno del cero (valores que redondean a 0,0%) no
marca divergencia, y un caso apenas fuera de la banda muerta (0,1%) sigue
detectándose.

**Verificación de campo (2026-09-15, series de datos.gob.ar hasta 2026-08):**
el agregado desestacionalizado divergió del sentido conjunto de IVA-DGI y
cheque en **enero, marzo, abril, mayo y julio** de 2026 (cinco de los ocho
meses del año, no cuatro — julio se omitió en la primera verificación de
campo). El caso más marcado es mayo: agregado +10,1% i.a. real mientras
IVA-DGI cae 2,9% y cheque cae 3,5%. Julio es igual de marcado en la dirección
contraria: agregado +10,0%, IVA-DGI +5,6% pero cheque −11,3%. En agosto
(último mes publicado) los tres coinciden en signo negativo (agregado −0,8%,
IVA −3,0%, cheque −9,1%), aunque con magnitudes muy distintas. Esto es un
hallazgo para reportar, no una recalibración de bandas: el puntaje de
`recaudacion` no cambia por esta verificación. Ver ADR-0321 sobre cómo leer
esta divergencia (no es una verificación independiente: IVA y cheque son
parte del propio agregado).

## Pros y contras de las opciones

- **1. Comparar nivel contra interanual:** unidades no comparables, el
  «sentido» no se puede leer sin traducir primero.
- **2. Reconstruir un nominal combinado aparte:** duplica lógica que ya existe
  en `comarb.base_imponible_real_sa` sin ganar nada — el agregado ya tiene una
  interanual real disponible con sólo dividir su propia serie.
- **3. Interanual real de la serie ya desestacionalizada:** reutiliza lo que
  ya se calcula, no inventa un segundo deflactor, y dos funciones puras
  (`_real_ia_pm3`, la interanual de `serie`) alcanzan.

## Más información

- ADR-0078: el error del deflactor no es independiente cuando se comparte.
- ADR-0152: por qué `recaudacion` es un nivel y no una variación.
- ADR-0239: por qué un deflactor de calendario distorsiona una suma de flujos
  — y por qué no aplica a una lectura de un solo mes.
- ADR-0318: la decisión de que este control entra como control, no como card.
- ADR-0321: corrige el encuadre — es una descomposición del agregado, no un
  control independiente — y las cinco (no cuatro) fechas de divergencia.
