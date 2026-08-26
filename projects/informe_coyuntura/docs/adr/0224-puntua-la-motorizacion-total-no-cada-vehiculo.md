---
madr: 4
id: '0224'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [motorizacion_total, patentamiento_autos, patentamiento_motos]
archivos: ['scripts/vida_cotidiana/collectors/motorizacion.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/publicar.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'scripts/gate_calidad.py', 'tests/test_motorizacion_total.py']
supersede_parcialmente: ['0223']
relacionado: ['0018', '0024', '0033', '0108', '0153', '0216', '0217', '0231', '0233', '0267']
modificado_por: ['0225']
ambito: 'ITCIS · dimensión de ingresos y consumo · qué puntúa del patentamiento de vehículos'
origen: 'Desacuerdo editorial: un editor sostiene que el pasaje del auto a la moto es empobrecimiento y debe puntuar negativo; el otro, que es acceso y es una mejora'
---

# ADR-0224 — Puntúa la motorización total, no cada vehículo por su lado

## Contexto y planteo del problema

Dos editores en desacuerdo sobre el signo del mismo dato, y los dos con un
argumento serio.

**El editor A** sostiene que el pasaje del auto a la moto es **empobrecimiento**.
La moto es un medio de transporte más precario —menos seguro, sin protección
climática, menor capacidad—, y un hogar que no sostiene el auto y compra una
moto está peor aunque el patentamiento suba. El índice debería registrarlo como
deterioro. El propio editor A nombró los confusores: economías de plataforma,
cambio de patrones de movilidad, bicicletas.

**El editor B** sostiene que es **acceso**. Gente que antes no podía comprar
ningún vehículo ahora compra una moto. Es aspiracional y es una mejora.

El problema es real y el índice no podía dirimirlo, porque **las dos lecturas
mueven la misma serie en la misma dirección**. [[0223-el-espejo-de-las-motos-el-patentamiento-de-autos]]
—de un día antes— incorporó el patentamiento de autos para poder verlo, y
efectivamente lo hizo visible: desde diciembre de 2025 las dos series se
separan. Pero verlo no es puntuarlo. Con autos y motos como componentes
independientes, el índice sigue sin decidir el signo: suma una serie que sube y
otra que baja, y el resultado no distingue acceso de descenso de categoría.

A eso se sumaba un problema de medición: `patentamiento_motos` estaba **clavado
en el techo de winsorización de 140 desde enero de 2026**, con índice crudo
170,0. Un componente saturado durante siete meses es una constante, y el propio
ADR-0223 dejó anotado que ése era «lo primero a revisar».

### Las cuatro pruebas que discriminan

Antes de decidir se midió. La hipótesis del editor A —sustitución descendente—
hace predicciones contrastables, y **las cuatro fallan**.

**1. El total sube.** Autos + motos per cápita, acumulado móvil de 12 meses,
rebaseado al 4T-2023: en la ventana exacta de la divergencia (dic-2025 →
jul-2026) el total **sube 7,5%**, de 134,6 a 144,7. Si los hogares bajaran de
categoría, cada moto que entra tendría un auto que sale y el total estaría
plano. En unidades: se dejaron de patentar 47.769 autos y entraron 151.587
motos, un neto de **+103.818 vehículos** — **3,17 motos por cada auto perdido**.

**2. La geografía no arma el patrón.** Cruzando las dos series por jurisdicción
contra el salario mediano privado provincial de 2023 (CEP-XXI) y la población
del censo 2022, el test directo de sustitución —¿suben las motos donde caen los
autos?— da **r = +0,02** (−0,01 sin Tierra del Fuego, −0,13 sacando también
Santa Cruz y CABA). No hay relación de ningún signo. Lo que sí hay es un
gradiente de ingreso: el total crece más rápido cuanto **más pobre** la
provincia (r = −0,70 con el salario; Tucumán +32,0%, Formosa +31,2%, Santiago
del Estero +25,5%, Chaco +23,9%), y **cae** en las ricas (Santa Cruz −21,7%,
Chubut −8,3%, Río Negro −1,8%, CABA −0,9%). Sube en 17 de 24 jurisdicciones.

**3. Nadie se está desprendiendo del auto.** Las transferencias de automotores
—el mercado de usados, misma fuente— hacen pico a mediados de 2025 y **caen**
desde entonces: 1.890.403 unidades en los 12 meses a dic-2025 contra 1.840.642 a
jul-2026. Un descenso masivo de categoría tendría que verse como una ola de
autos usados saliendo al mercado. No está.

**4. La caída de autos ya tiene dueño, y es el crédito.** El stock real de
préstamos prendarios a personas humanas (BCRA, variable 949, deflactado por IPC)
hace pico en **octubre de 2025** y cae **12,0% real** hasta junio de 2026, con
la variación interanual desplomándose de +197,0% a −1,9%. Correlaciona con el
índice de autos en **r = +0,986 con cuatro meses de rezago**. Los autos no
cayeron porque la gente los cambió por motos: cayeron porque se les cortó el
financiamiento.

#### El reencuadre, que es el hallazgo que ninguno de los dos editores tenía

Deflactando por IPC nivel general, base dic-2023 = 100 (INDEC, aperturas del
IPC-GBA): **«adquisición de vehículos» cae a 84,1 en términos reales —15,9%—
mientras «transporte público» sube a 200,7, más del doble.** El precio relativo
entre poner un vehículo en la puerta y tomarse el colectivo se movió por un
factor de 2,4.

**La moto no está compitiendo contra el auto: está compitiendo contra el
colectivo, y el colectivo se volvió inaccesible.** Es lo que el estudio de la
CAF sobre cinco ciudades latinoamericanas —Buenos Aires entre ellas— ya había
documentado: la gran mayoría de quienes usan la moto como vehículo privado
**vienen del transporte público** y volverían a él si no tuvieran la moto.

Lo que los datos describen, entonces, no es «acceso = mejora» ni «sustitución =
deterioro», sino **motorización forzada desde abajo**: hogares que no venían del
auto sino del colectivo, en las provincias más pobres, empujados por un cambio
de precios relativos y habilitados por un vehículo que se abarató. Es un ascenso
en la escalera de activos **y** un deterioro de la asequibilidad del transporte,
al mismo tiempo.

#### El artefacto de Tierra del Fuego

La provincia inscribió **29.005 motos en 2025** contra 816 en 2023, 762 en 2024
y 294 en los siete meses de 2026. Todo el exceso se concentra entre abril y
noviembre de 2025, con un pico de 7.428 en octubre sobre una línea de base de
unas 60 por mes: **35 veces lo normal, en la provincia menos poblada del país**.
Es un movimiento registral de su régimen de promoción industrial, no compras de
hogares fueguinos, y estaba entrando al índice como si 29.000 familias hubieran
comprado una moto.

Efecto medido: el componente de motos marcaba 170,0 con el artefacto y 166,0 sin
él. Y como el pico cae más adentro de la ventana que termina en dic-2025 que de
la que termina en jul-2026, **achicaba** la divergencia real.

## Factores de decisión

- **El componente tiene que medir lo que decide el signo.** Si la pregunta es si
  el hogar accedió a un vehículo, el componente tiene que mirar el acceso, no la
  marca de carrocería.
- **El signo se deduce del objetivo del índice, no del indicador.** Es lo único
  que el *Handbook* OCDE/JRC dice al respecto —no usa siquiera la palabra
  «polaridad»—, y su ejemplo es estructuralmente idéntico a éste: la movilidad
  internacional de investigadores, que puede leerse como fuga de cerebros o como
  aprendizaje entre pares.
- **Un componente saturado no aporta.** Mientras el techo lo aplane, da igual lo
  que haga la fuente.
- **O integra el índice, o no es card** ([[0216-o-integra-el-indice-o-no-es-card]]).
- **La composición tiene que seguir siendo legible**: el corrimiento hacia la
  moto es un hecho y no puede desaparecer del informe.
- **El peso del bloque de vehículos no se mueve de contrabando.**
- **Y el precedente propio manda**: [[0217-puntua-el-acceso-total-a-proteina-no-la-vacuna]]
  resolvió el mismo dilema con la carne hace un día. Leer la caída de la vacuna
  como pérdida de poder adquisitivo era un falso positivo, porque buena parte
  era sustitución hacia pollo y cerdo. La salida no fue elegirle un signo: fue
  **puntuar el acceso total y usar la composición para explicar el color**.

## Opciones consideradas

1. **Puntuar la motorización total** —autos + motos per cápita— y explicar el
   color con la composición, como la matriz A×B de la carne.
2. **Dejar los dos componentes separados**, eximir motos del techo y sacar el
   artefacto de Tierra del Fuego.
3. **Un indicador de sustitución con signo explícito**: el ratio motos/total,
   invertido, puntuando como deterioro.
4. **No tocar nada.**

## Decisión

**Opción 1.** Entra **`motorizacion_total`**: cuántos vehículos 0 kilómetro
—autos y motos— se inscriben por año cada mil habitantes. Autos y motos **dejan
de puntuar y dejan de ser cards**, y pasan a ser los Componentes A y B de la
matriz A×B que explica el color, exactamente como la vacuna dentro del total de
carnes.

Toma el **peso combinado de los dos que reemplaza** —0,0196 de motos más 0,0200
de autos = 0,0396 de la dimensión de ingresos, 1,11% del índice— y **los otros
tres componentes de la dimensión no se tocan**. Es el único reparto que no
afirma nada que no se haya medido.

Esos porcentajes describen el reparto al tomar esta decisión. ADR-0225, dictado
después, incorporó consumo de supermercados y redujo proporcionalmente el peso
vigente de motorización a 3,17% de la dimensión y 0,89% del ITCIS; con ese peso,
el máximo del ejemplo de 170 es 0,27 puntos por encima del techo.

Fuente: los dos registros de la **DNRPA**, sumados y divididos por la población
urbana total proyectada del INDEC, con acumulado móvil de 12 meses
([[0024-motos-movil-12m-estacionalidad]], aplicado a la SUMA y no a cada
vehículo) y rebase al 4T-2023 ([[0018-itvc-parametrica-vida-cotidiana]]).

**Motos cambia de fuente**: de CAFAM a la DNRPA. No es una preferencia — CAFAM
publica sólo el total país, y **excluir Tierra del Fuego exige apertura por
jurisdicción**. De paso desaparece el store local que acumulaba la serie mes a
mes: la DNRPA publica el histórico entero en cada corrida.

**Tierra del Fuego se excluye entera y en toda la serie**, no sólo en los meses
del pico. Recortar los meses anómalos exigiría un umbral, y cualquier umbral que
atrape una carga fiscal también atrapa un mes real: abril de 2020 fue el 12% de
la mediana de los doce meses previos y era una cuarentena. La exclusión cuesta
0,6% del total y no depende de calibrar nada. Va escrita en la línea de fuente
de las tres series, que es donde el lector la ve.

### La excepción al techo de winsorización, acotada y argumentada

`motorizacion_total` queda **exento del techo de 140** de
[[0033-itvc-doble-conteo-y-winsorizacion]]. **Esto no levanta el techo: exime a
un componente**, y hace falta porque sin la exención el cambio no sirve para
nada — el total da 144,7 y **también** quedaría recortado, cambiando dos
constantes por una constante. Empezó a saturar en marzo de 2026, dos meses
después que motos.

Los dos argumentos, medidos:

1. **A este peso, el techo protege contra algo que no puede pasar.** Con 1,11%
   del índice, lo máximo que el componente puede comprar por encima del techo
   son **0,33 puntos de ITCIS**, y eso exigiría que llegara a 170. El techo
   existe para que un boom no compre compensación *ilimitada* en una agregación
   lineal; acá la compensación ya está acotada por el peso, que es el mecanismo
   del que el techo es un sustituto grueso.
2. **Contra esta base, 140 no marca un outlier: marca un año normal.** El
   4T-2023 fue el fondo del congelamiento previo a la devaluación, o sea una
   base **deprimida**. Medido sobre 2011-2019 y rebaseado a esa misma base, el
   **64%** de los meses del total de motorización habrían superado 140 —y el 84%
   de los de autos solos—, con máximos de 206,7 para el total y 213,4 para
   autos. El criterio del JRC que ADR-0033 cita recorta un puñado de valores
   extremos, del orden del percentil 95; no dos tercios de la distribución.
   Winsorizar acá no controla outliers: **censura el rango normal**.

**Lo que esta excepción NO decide**: si 140 sigue siendo el número correcto para
el resto de los componentes, dado que **todos** comparten la misma base
deprimida. El problema es más grande que este componente y **merece su propio
ADR**; acá no se resuelve. `sentimiento_digital` y todos los demás siguen con
techo, y `tests/test_motorizacion_total.py` falla si la lista de exentos crece.

### Consecuencias

- **El componente entra en 142,9** (era 140,0 recortado desde 170,0) con 1,11%
  del índice. **El ITCIS pasa de 90,7 a 90,8** y la tensión de 6,9 a 6,8; la
  dimensión de ingresos y consumo, de **117,3 a 117,7**.
- **El cinturón queda con diecisiete componentes y los diecisiete puntúan.**
- La card publica el **nivel**: 30,9 vehículos 0km por cada mil habitantes. El
  par card/serie queda en unidades distintas y entra a `G3_EXCEPCIONES` — pero,
  a diferencia de la carne, **no hay dos fuentes**: las dos salen de la misma
  descarga, así que no pueden separarse.
- **Desaparece de la matriz de redundancia el par autos↔motos**, que ADR-0223
  tuvo que declarar como el único del cinturón por encima de 0,7 al destendenciar
  (+0,801) y con un motivo incómodo: daba tan alto porque el techo aplanaba a
  motos y comparaba a autos contra una recta.
- El histórico del ITCIS en `validacion_externa.py` aplica la misma exención, y
  un test verifica que las dos listas no diverjan.

### Lo que hay que declarar en la ficha, porque le da la razón al editor A

El componente puntúa una mejora de acceso **y** convive con un deterioro que no
puntúa. Las dos cosas van escritas en las limitaciones de la ficha:

- **La escalera de activos es real y está cuantificada.** El Índice de Pobreza
  Multidimensional global de OPHI/PNUD define la privación de activos como *«no
  poseer más de uno de estos bienes: radio, TV, teléfono, computadora, carro de
  tracción animal, bicicleta, **motocicleta** o heladera, **y no poseer un auto
  o camión**»*: la moto es un activo menor y el auto tiene **rol de veto** —
  tenerlo, solo, saca al hogar de la privación. No es normativo: el DHS Wealth
  Index, que **estima** el peso de cada bien con componentes principales en vez
  de suponerlo, le da a la moto alrededor de **0,23 veces** el peso del auto. Y
  el corrimiento es real y es récord: las motos son el **60,1%** de lo que se
  patenta, contra un rango de 37,9%-54,3% en los veinte años previos de la
  serie. Que el total suba mientras la mezcla se corre a la moto es acceso y
  descenso de peldaño a la vez, y el color sólo refleja lo primero.
- **Parte de la suba es precio relativo y no ingreso**, por lo del transporte
  público. El componente no separa esos dos motores.

Lo que **no** entra al signo es la siniestralidad. Que la moto sea un transporte
mucho más riesgoso es cierto y es grave, pero es un fenómeno distinto del
acceso: meterlo adentro del signo del patentamiento sería exactamente el error
que [[0218-el-cierre-de-pymes-se-mide-con-la-srt]] tardó trece meses en
corregir. Si importa, va como indicador propio de siniestralidad vial.

### La objeción que no quedó desactivada

Nishitateno y Burke (2014), *«The motorcycle Kuznets curve»*, sobre 153 países y
1963-2010, encuentran que la motorización en dos ruedas **sube y después baja**
con el ingreso, con un pico entre 7.000 y unos 15.000 dólares per cápita según
especificación — y que **sólo las motos** tienen ese pico: autos y camiones
crecen monótonamente. Argentina está por encima de ese umbral.

Un lector adversarial puede decir, con la literatura del lado: ya pasamos el
pico, así que motos en alza es rama descendente, o sea empobrecimiento. **La
evidencia reunida acá no desactiva del todo esa objeción.** Lo que la debilita
es que la curva es un promedio de sección cruzada que el propio paper describe
como *shallow*, y que el patrón argentino —crecimiento concentrado en Chaco,
Tucumán, Salta y Santiago del Estero, baja cilindrada, total en alza— describe
entrada y no salida. Queda anotada para que el próximo que la traiga encuentre
que ya se consideró.

### El costo político, dicho de frente

**Esto retira la card de autos un día después de publicarla.** ADR-0223 la creó
el 21 de agosto de 2026 y éste la baja a Componente B con la misma fecha. La
lectura de la divergencia que aquel ADR habilitó no se pierde —es literalmente
lo que dice la matriz A×B—, pero deja de estar en una tarjeta propia. Es el
costo más caro del cambio y es real.

Se paga igual porque el diagnóstico de ADR-0223 era correcto y su remedio,
incompleto: identificó que con motos solas el índice no podía distinguir más
consumo de bajar de categoría, y agregó el dato que faltaba para **verlo**. Lo
que no hizo fue cambiar **qué puntúa**, y el problema estaba ahí.

### Confirmación

`tests/test_motorizacion_total.py` (30 tests) cuida lo que puede volver a
romperse: que la fuente siga siendo el registro y no una cámara, que el colector
reviente en vez de publicar una serie recortada, que puntúe el total y que autos
y motos no vuelvan como cards, que la matriz explique el color y **reconcilie
con las series publicadas**, que Tierra del Fuego siga excluida y que la
exclusión se **note** en la serie, y que la exención del techo siga acotada a un
componente en los dos lugares que la aplican.

El cambio de fuente se **verifica, no se declara**: `data/vida/puente_cafam_dnrpa.json`
congela la serie de CAFAM y un test la compara mes a mes contra la nueva. Fuera
del período del artefacto el cociente queda **entre 0,9995 y 1,0080 en 37
meses** —las dos fuentes miden lo mismo, la diferencia es el día de corte de la
cámara—; dentro, cae hasta **0,8879**, que es la exclusión haciendo exactamente
lo que dice que hace.

## Pros y contras de las opciones

**1. Puntuar el total, explicar con el ratio.** A favor: es lo único que
distingue acceso de descenso de categoría, tiene precedente propio de un día
antes (ADR-0217), disuelve el par redundante y saca al bloque de vehículos del
techo. En contra: retira la card de autos un día después de crearla, exige una
excepción al techo que sienta precedente, y colapsa en un solo número una
divergencia que hoy se ve en dos gráficos.

**2. Dos componentes separados, sin techo y sin Tierra del Fuego.** A favor:
cuesta muy poco, arregla la saturación y el dato sucio, y conserva las dos
cards. En contra: **no contesta la pregunta editorial**. El índice sigue sin
ningún lugar donde diga que el acceso total a un vehículo subió, que es el hecho
central, y sigue sumando dos series de signo ambiguo esperando que se compensen.

**3. Indicador de sustitución con signo explícito.** A favor: sería la respuesta
directa a la tesis del editor A. En contra: publicaría hoy 87,5, o sea puntuaría
como deterioro un movimiento cuyo mecanismo **no aparece en ninguna de las
cuatro pruebas**. Y no existe precedente: ningún observatorio publica un
indicador de sustitución de movilidad, y el «cambio modal» que sí se publica
tiene el signo **invertido** por criterio ambiental. Habría que justificarlo
íntegramente solos, para mover el ITCIS medio punto.

**4. No tocar nada.** A favor: ninguno. En contra: deja un componente clavado en
el techo hace siete meses y una pregunta editorial abierta sin respuesta.

## Más información

- **Todo el rango de la discusión cabe en seis décimas de ITCIS**: medidas las
  once variantes, el índice va de 90,2 (sólo sustitución, la tesis del editor A
  en estado puro) a 90,8. La dimensión se mueve más: de 115,5 a 117,9. Vale la
  pena resolverlo bien porque es una decisión de método que se va a citar, no
  porque el número se vaya a mover.
- **El delivery quedó descartado como causa de la aceleración, con una salvedad
  grande.** `trabajo_independiente` (SIPA) sube suave y sin quiebres —19,21% en
  oct-2023, 20,65% en ene-2026— y en la ventana de la divergencia se mueve 0,05
  pp mientras las motos ganan 33,7 puntos de índice. Pero el trabajo de
  plataformas es mayormente informal y no aparece en SIPA: se puede afirmar que
  no hubo salto en el trabajo independiente **registrado**, no que no lo hubo en
  el informal.
- **La composición por cilindrada no se pudo medir.** El CSV de la DNRPA trae
  tipo de vehículo, mes y jurisdicción, y no cilindrada ni precio. Lo único
  disponible es el ranking de modelos de ACARA —todos de baja cilindrada
  utilitaria—, que es fuente secundaria y no se usó.
- **El desagregado de precios moto contra auto tampoco existe.** El IPC del
  INDEC publica «adquisición de vehículos» como una sola apertura, sin separar
  dos ruedas; la serie del IPC-GBA base 1988 que sí lo separaba está
  discontinuada desde 2000. La pregunta literal —¿se abarató la moto contra el
  auto?— **no se puede contestar** con fuente primaria argentina.
- [[0223-el-espejo-de-las-motos-el-patentamiento-de-autos]] queda superado
  parcialmente: su diagnóstico y su elección de fuente siguen en pie —la DNRPA
  contra ACARA y ADEFA, y el rezago de 90 días medido sobre el catálogo—, y lo
  que cambia es que el patentamiento de autos deja de ser un componente propio.
