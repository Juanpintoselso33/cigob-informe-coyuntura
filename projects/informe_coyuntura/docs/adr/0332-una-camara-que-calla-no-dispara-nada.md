---
madr: 4
id: '0332'
estado: 'aceptado'
fecha: 2026-09-20
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_empresario]
archivos: ['scripts/politica.py', 'tests/test_camara_muda.py']
relacionado: ['0149', '0310']
ambito: 'Cinturón política · ITCP · `apoyo_empresario` · detectar que una cámara dejó de publicar; no cambia el cálculo del saldo'
origen: 'Al desbloquear la card el 20-sep-2026 (tanda de 4 comunicados UIA) se midió de dónde venían los computables y AEA no aparecía desde marzo. Juan lo empujó preguntando «pero no hay más datos?».'
---

# ADR-0332 — Una cámara que calla no dispara nada, y el saldo sigue saliendo

## Contexto y planteo del problema

`apoyo_empresario` publica el saldo de postura de **dos** cámaras —AEA y UIA—
hacia el Ejecutivo nacional, y su card se rotula «Postura pública de las cámaras
empresarias». Al 20-sep-2026 **una de las dos lleva 173 días sin publicar**.

AEA no emite un comunicado desde el **2026-03-31**. Verificado contra su propia
página (`aeanet.net/prensa.html`): la fecha más nueva que existe ahí es ésa, así
que no es el extractor, es la fuente. Y no es su cadencia normal: sobre los 42
huecos observados en el corpus, AEA tiene **mediana 43 días, p90 116, p95 151 y
máximo 154**. Los 173 días actuales **no tienen precedente**. UIA, en cambio,
está en 3 días contra un máximo de 112.

El efecto sobre el número publicado, medido en la ventana móvil de 12 meses que
produce el punto de 2026-09 (valor −0,2):

| | computables en la ventana |
|---|---|
| UIA | **9** |
| AEA | **1** (un apoyo del 2026-03-03) |

O sea: el indicador que se llama «las cámaras empresarias» es hoy **90% UIA**, y
cuando marzo salga de la ventana móvil será 100% UIA sin que nada cambie en la
card.

**Lo que falla no es el cálculo: es que nadie lo mira.** ADR-0310 puso dos
guardas sobre este indicador y AEA pasa las dos:

- los **pendientes** cortan la serie cuando hay un comunicado sin codificar —
  pero AEA no tiene comunicados nuevos, así que no genera ninguno;
- **`inventario_verificado`** exige que las dos cámaras **respondan** en la misma
  corrida — y la página de AEA responde perfectamente, con sus 46 comunicados de
  siempre.

Una fuente que contesta y no publica es indistinguible, para el pipeline, de una
fuente que no tiene novedades. El manual del indicador ya lo tenía anticipado en
una línea de `lo_que_este_indicador_NO_dice`: *«Una cámara puede callar por
conveniencia y eso no aparece»*. Está pasando, y no aparece.

## Factores de decisión

- El umbral en DÍAS no puede ser un número elegido a mano: es lo que este repo
  llama copiar el rezago del documento en vez de medirlo. (Sí queda un número
  elegido: cuántos huecos hacen falta para estimar una cadencia. No fija cuándo
  avisar, fija cuándo hay evidencia para opinar.)
- Tiene que ser **por cámara**. AEA publica cada 43 días de mediana y UIA cada 7:
  un tope único daría falsos positivos en una y taparía a la otra.
- **Sólo lo accionable.** Un aviso que salte en cada hueco normal de AEA entrena
  a ignorar el canal, que es la regla que mantiene vivo `#monitor-alertas`.
- No se toca el cálculo del saldo. Que una cámara calle es un hecho del mundo,
  no un error de cómputo.

## Opciones consideradas

1. **Renombrar la card a «Postura pública de la UIA»** mientras AEA calle.
2. **Un tope fijo de días** igual para las dos cámaras.
3. **Avisar cuando el silencio de una cámara supera su propio máximo
   histórico**, medido sobre el corpus — elegida.
4. No hacer nada y anotar el hallazgo.

## Decisión

**Opción 3.** `politica.silencio_por_camara()` calcula, por cámara vigilada, los
días sin publicar y el umbral a partir de su propia cadencia.
`_avisar_camara_muda()` registra una incidencia `[COTEJO_MANUAL]` —el mismo
mecanismo que el vencimiento de la conciliación judicial— cuando el silencio
supera ese umbral.

Tres definiciones hacen el trabajo, y las tres salieron de la revisión
adversarial previa al merge:

**1. El umbral es el percentil 95 de los huecos, no el máximo.** Con el máximo la
guarda ratcheteaba: un silencio extraordinario, una vez cerrado, se convertía en
el nuevo umbral y la guarda quedaba sorda hasta superarlo. Una ausencia de 400
días ignorada dejaba el umbral en 401 para siempre — la guarda aprendía justo de
los incidentes que tenía que detectar. El p95 es insensible a un caso aislado y
sí recoge los huecos largos cuando son parte de la cadencia real: al 20-sep-2026
AEA queda con **umbral 134** (máximo 154, mediana 43) y UIA con **38** (máximo
112, mediana 7).

**2. La fecha sale del INVENTARIO, no del corpus codificado.** Un comunicado
recién detectado entra a `pendientes`, no a la codificación. Leyendo sólo lo
codificado, la guarda habría seguido diciendo «muda» después de que la cámara
volvió a publicar, hasta que alguien la clasificara: eso mide nuestro atraso, no
el silencio de la fuente.

**3. «No pude evaluar» se avisa, y no se parece a «no está muda».** La función
devuelve SIEMPRE una entrada por cada cámara de `CAMARAS_VIGILADAS`, con
`evaluable: False` y un `motivo` cuando no puede juzgar —inventario ilegible,
cámara ausente, fecha futura, o menos de `CAMARA_MUDA_PISO_HUECOS = 10` huecos
observados—, y cada uno de esos casos registra su propia incidencia. La primera
versión devolvía `{}` y la lista de avisos salía vacía: indistinguible de «las
dos cámaras están publicando», o sea la misma omisión silenciosa que este ADR
vino a eliminar.

La llamada va **aislada en un `try`** después de escribir el store: si la guarda
se cae no puede llevarse el aviso de pendientes que el llamador manda después, y
su propia caída se registra como incidencia en vez de pasar por «no hay cámaras
mudas».

**No se renombra la card (opción 1 descartada).** El universo de diseño sigue
siendo las dos cámaras y el manual ya declara que una puede callar; renombrar
haría que el rótulo oscile cada vez que AEA publique o deje de publicar, y
perdería la información de que una se calló. Si el silencio resulta permanente,
cambiar el perímetro del indicador es **otra** decisión y pide su propio ADR —
es lo que el texto del aviso le pide explícitamente a quien lo lea.

La opción 2 se descartó porque con un tope único AEA quedaba en falso positivo
permanente o UIA sin vigilancia; la 4, porque un hallazgo sin guarda se
redescubre a los golpes, que es la lección de ADR-0220.

### Consecuencias

- La corrida nocturna va a avisar por AEA **desde la próxima**, y va a seguir
  avisando hasta que publique o hasta que se decida el perímetro. Es el
  comportamiento buscado: hoy el hallazgo vive en este ADR y en nada más.
- El saldo, el peso y la banda **no cambian**. La card sigue publicando −0,2 con
  fecha 2026-09.
- La guarda sirve para las dos cámaras: si mañana UIA se calla —que es la que
  sostiene 9 de los 10 computables— también avisa.
- **El canal puede recibir avisos de «vigilancia sin evaluar»** que antes no
  existían. Es deliberado y es el punto: preferimos un aviso de que no estamos
  mirando antes que un silencio que se lee como que todo está bien.
- Queda sin resolver, a propósito, que la ficha no publique la composición por
  cámara de la ventana. Se decide cuando se decida el perímetro.

### Confirmación

`tests/test_camara_muda.py`, doce casos. Lo que prueba de verdad es lo que la
guarda **no** tiene que hacer:

- **no** avisa con un silencio que la cámara ya se tomó varias veces;
- **no** deja que un hueco extraordinario aislado le levante el umbral (el
  anti-ratchet, con un caso de 400 días ya cerrado);
- **no** se calla cuando no puede evaluar: hay un caso por inventario vacío, por
  cámara ausente, por inventario ilegible, por fecha futura y por corpus bajo el
  piso, y cada uno exige que salga la incidencia;
- **no** sigue avisando cuando la cámara volvió a publicar aunque el comunicado
  esté sin codificar;
- el umbral es por cámara: dos cámaras con el mismo silencio y cadencias
  distintas no se juzgan igual;
- el borde exacto no avisa y el día siguiente sí;
- y un caso contra el corpus versionado, no un fixture, que falla si AEA vuelve a
  publicar — o sea, avisa que este ADR dejó de estar vigente.

Los casos no comparan sólo el retorno de la función: leen stderr y exigen el
marcador `[COTEJO_MANUAL]`, porque si `registrar()` se volviera un no-op un test
que sólo mira la lista pasaría igual.

Probada rompiéndola, con el bytecode borrado antes de cada corrida:

| Mutación | Resultado |
|---|---|
| `silencio_por_camara` devuelve `{}` (fail-open) | **12 de 12 fallan** |
| umbral vuelve al máximo en vez del p95 | 1 falla (el anti-ratchet) |
| se deja de leer `pendientes` | 1 falla (mide el atraso, no la fuente) |

## Pros y contras de las opciones

**Opción 3 (elegida).** Bueno: sin un umbral de días elegido a mano, por cámara,
y se calibra sola a medida que el corpus crece. Malo: una cámara con huecos
largos habituales tiene un umbral alto y tarda en avisar; y sigue habiendo un
número puesto a mano —el piso de huecos— que decide si hay vigilancia, aunque
ahora su ausencia se avisa en vez de silenciarse.

**Opción 1.** Bueno: el rótulo diría la verdad hoy mismo. Malo: oscila con cada
publicación, y tapa el hallazgo en vez de mostrarlo.

**Opción 2.** Bueno: trivial de implementar y de explicar. Malo: no existe un
número que sirva para una cámara que publica cada 7 días y otra cada 43.

## Más información

- ADR-0149 — el detector de novedades empresarias, que no clasifica.
- ADR-0310 — el corpus cerrado y `inventario_verificado`, las dos guardas que
  AEA pasa sin activar.
- El hallazgo salió de una pregunta, no de un gate: al desbloquear la card se
  midió de dónde venían los 10 computables de 2026 y AEA no aparecía desde
  marzo. Agosto de 2026 es el caso que lo resume: **11 comunicados codificados y
  cero computables**.

### Qué corrigió la revisión adversarial de este ADR

La primera versión de la guarda tenía tres fallas que una revisión con Codex
—modelo distinto, contexto fresco— encontró antes del merge, y las tres eran de
la misma familia que el problema que el ADR denuncia:

1. **Fallaba abierta.** Con el inventario vacío, una ruta equivocada o una clave
   renombrada devolvía `{}`, la lista de avisos salía vacía y el pipeline seguía
   en verde: exactamente igual que con las dos cámaras publicando. Peor, el test
   de «corpus corto» consagraba ese silencio como conducta correcta.
2. **Medía nuestro atraso, no el silencio de la fuente.** Leía sólo el corpus
   codificado, así que si AEA volvía a publicar la guarda seguía gritando «muda»
   hasta que alguien clasificara el comunicado. El ADR prometía que avisaba
   «hasta que publique» y eso era falso.
3. **El umbral ratcheteaba.** Al usar el máximo, cada silencio extraordinario ya
   cerrado subía el umbral para siempre: la guarda se volvía menos sensible
   gracias a los incidentes que tenía que detectar.

Las tres están corregidas arriba, con un caso de test por cada una. La revisión
marcó además que la mediana con cantidad par se publicaba redondeada hacia abajo
(7 y 8 daban 7, no 7,5) y que faltaba el test del borde exacto: los dos
arreglados. El veredicto de la revisión fue «pediría cambios antes de mergear»,
y tenía razón en las tres.
