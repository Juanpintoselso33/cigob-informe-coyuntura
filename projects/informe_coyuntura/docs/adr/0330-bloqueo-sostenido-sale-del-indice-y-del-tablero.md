---
madr: 4
id: '0330'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'politica'
indicadores: [bloqueo_sostenido, desafios_legislativos]
archivos: ['scripts/itcp.py', 'scripts/politica.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'scripts/validacion_externa.py', 'web/src/lib/fichas.ts', 'tests/test_itcp.py', 'tests/test_publicar.py', 'tests/test_validacion_externa.py', 'tests/test_procedencia_anclas.py']
corrige: ['0069', '0276']
relacionado: ['0021', '0046', '0062', '0070', '0089', '0153', '0216', '0230']
ambito: 'Cinturón política · ITCP · dimensión Poder legislativo · `bloqueo_sostenido` sale, `desafios_legislativos` absorbe su contenido'
origen: 'Auditoría editorial: bloqueo_sostenido es el único indicador del tablero que se publica sin puntuar (SIN UNIVERSO), y lo hace justo cuando el fenómeno que mide llega a su extremo'
---

# ADR-0330 — bloqueo_sostenido sale del índice y del tablero: enmudecer en el extremo no es una card

## Contexto y planteo del problema

`bloqueo_sostenido` (ADR-0069) mide el % de normas del Ejecutivo desafiadas en
el recinto que siguen en pie, ventana móvil de 12 meses. Desde hace trece
corridas seguidas no hay ningún desafío en la ventana: sin denominador no hay
tasa, y ADR-0276 ya había decidido bien qué hacer con eso —no inventar un
cero, no arrastrar la tasa de otra ventana— así que la card sale publicada con
`valor: None`, `en_indice: False` y el cartel «SIN UNIVERSO · Sin tasa para
esta ventana». Es, hoy, el único indicador del tablero en ese estado.

El problema no es el manejo del denominador vacío: es que ese es el ÚNICO
comportamiento que este indicador puede tener cuando el fenómeno que mide
llega a su extremo. Cero desafíos en doce meses es una señal fuerte —la
oposición dejó de intentar voltear normas del Ejecutivo—, y en vez de mostrar
esa señal, el tablero muestra una card vacía. Y el dato ya está publicado al
lado: `desafios_legislativos` (ADR-0089) vale 0 y sí puntúa. El conteo se
banca el cero como dato; la tasa derivada, no.

La regla del proyecto (ADR-0153/0216) es *o integra el índice, o no es card*:
un indicador que se publica sin puntuar vuelve a existir por omisión. Acá el
caso es más sutil que el original —no es que alguien haya olvidado marcarlo
como contexto, es que su propio diseño lo empuja a ese estado en el peor
momento posible para leerlo— pero la regla aplica igual.

## Factores de decisión

1. **El contenido no se pierde, cambia de lugar.** `bloqueo_sostenido` y
   `desafios_legislativos` comparten el mismo registro de eventos
   (`data/politica/derrotas_legislativas_eventos.json`): cuántas normas se
   desafiaron y cuántas sobrevivieron. Sacar la card no significa perder el
   dato — significa dejar de fingir que hay una tasa mensual cuando el
   denominador es cero, y en cambio contar la historia completa donde ya hay
   lugar para eso.
2. **`desafios_legislativos` sí puntúa con cero.** Su ficha ya dice, desde
   ADR-0276, que «un mes sin desafíos no es un dato faltante: es un cero, e
   indica que el Congreso no confrontó». Es la card correcta para explicar qué
   pasa cuando no hay desafíos, porque su propio valor (0) ya vive esa
   situación sin dejar de puntuar.
3. **No es objeción nueva.** El documento de indicadores del 15-sep-2026 ya
   había señalado por escrito que `bloqueo_sostenido`, `desafios_legislativos`
   y las sesiones caídas por quórum «hacen más al preciosismo del análisis
   legislativo […] que para aportar información significativa sobre el pulso
   del gobierno». Esta decisión atiende la parte de esa objeción que toca a
   `bloqueo_sostenido` (que además tiene el problema estructural del enmudecer
   en el extremo); no resuelve el resto — retirar `desafios_legislativos` o
   las sesiones caídas por quórum sigue siendo una decisión del equipo, no de
   este ADR.

## Opciones consideradas

1. **Dejarlo como está** (ADR-0276): el denominador vacío está bien resuelto,
   pero no ataca el problema de fondo — el tablero sigue mostrando una card
   vacía en el mejor escenario posible para la gobernabilidad legislativa.
2. **Inventar un piso o arrastrar la última tasa observada**: exactamente lo
   que ADR-0276 ya descartó, y por buenas razones — una tasa arrastrada de
   otra ventana no describe la ventana actual.
3. **Sacar la card del tablero (POLITICA_OCULTOS) y mover su contenido a la
   explicación de `desafios_legislativos`.**

## Decisión

Opción 3.

`bloqueo_sostenido` se agrega a `itcp.INDICADORES_CONTEXTO` (mismo mecanismo
que ya usan `rotacion_gabinete`, `protestas_caba`, `movilizacion_cepa`,
`derrotas_legislativas` y `comisiones_caidas`, ADR-0048/0052/0064/0089): sale
de `DIMENSIONES_ITCP["poder_legislativo"]["indicadores"]` y
`publicar.POLITICA_OCULTOS` (que se deriva de esa lista) lo saca del snapshot
publicado. El colector (`politica.fetch_bloqueo_sostenido`), el clasificador
de actas de Diputados/Senado y la serie mensual
(`descargar_series.fetch_bloqueo_sostenido_mensual`) **no se tocan**: siguen
corriendo como seguimiento interno, igual que los otros indicadores ocultos.

### Redistribución de peso — no debería mover el ITCP

`bloqueo_sostenido` pesaba 0,12 de 1,00 en `poder_legislativo`. Los cinco
indicadores restantes absorben ese peso proporcionalmente (÷0,88, redondeado a
dos decimales, mismo procedimiento inverso al que usó ADR-0168 para repartir
el ×0,85 cuando entró `produccion_legislativa`):

| Indicador | Peso antes | Peso después |
|---|---|---|
| `ratio_dnu` | 0,20 | 0,23 |
| `eficacia_legislativa` | 0,27 | 0,30 |
| `veto_quorum` | 0,13 | 0,15 |
| `desafios_legislativos` | 0,13 | 0,15 |
| `produccion_legislativa` | 0,15 | 0,17 |
| `bloqueo_sostenido` | 0,12 | (sale) |

Numéricamente esto **no mueve el ITCP**: `bloqueo_sostenido` llevaba trece
corridas seguidas sin dato («sin universo»), así que el motor paramétrico
(`parametrica.calcular_indice`) ya venía renormalizando el peso entre estos
cinco indicadores todos los meses, exactamente en esta proporción (peso
nominal de cada uno sobre 0,88, el peso nominal conjunto de los presentes).
Este ADR fija esa renormalización como peso de DISEÑO en vez de recalcularla
en runtime; el pequeño redondeo a dos decimales (0,20/0,88 = 0,2273 → 0,23,
etc.) es la única fuente posible de una diferencia, y es del orden de
milésimas de punto de ITCP — verificado corriendo la secuencia acotada de
política antes y después del cambio (ver Confirmación).

### `desafios_legislativos` explica el cero como señal

`politica.fetch_desafios_legislativos()` cambia su `detalle_txt` cuando el
conteo de la ventana da cero: en vez de «0 normas propias desafiadas… (0
cayeron, 0 siguen en pie)» —que lee como ausencia de dato—, ahora dice que
cero desafíos es la señal, y agrega la tasa de supervivencia del registro
**histórico completo** (no un número fijo): cuántas normas se desafiaron desde
marzo de 2024 y qué proporción sigue en pie. Ese texto llega al modal público
vía `_politica_input_txt` (`aporte_input_txt`), el mismo mecanismo por el que
ya viajaba el `detalle_txt` de `bloqueo_sostenido`.

### La ficha

`bloqueo_sostenido` pasa a ficha histórica, mismo patrón que
`derrotas_legislativas` (ADR-0089): se conserva íntegra —fuente,
transformaciones, bandas, limitaciones—, y su `incidenciaTexto` agrega que YA
NO PUNTÚA, por qué, y adónde se mudó su contenido. La ficha de
`desafios_legislativos` documenta el cambio en su propio `cambios`.

### Consecuencias

- El ITCP no debería moverse (ver medición arriba y en Confirmación).
- `tests/test_politica_sin_universo.py` deja de tener un caso real de card
  «sin universo» en el snapshot publicado — el mecanismo de ADR-0276 sigue
  existiendo en el colector (el registro interno sigue marcando
  `estado: "sin_universo"`), pero ya no llega al tablero.
- `tests/test_cierre_pymes.py` (la regla «o integra el índice, o no es card»)
  sigue en verde: es exactamente el camino que contempla.
- La ficha de `bloqueo_sostenido` sigue siendo alcanzable en
  `/metodologia/bloqueo_sostenido/` (no se borra ni se redirige — mismo
  patrón que `derrotas_legislativas`, que tampoco redirige porque nunca dejó
  de tener ficha, sólo dejó de puntuar).
- No resuelve la objeción completa del documento de indicadores del 15-sep
  sobre el "preciosismo" del cinturón legislativo: `desafios_legislativos` y
  las sesiones caídas por quórum siguen puntuando, y retirarlas —si el equipo
  lo decide— es alcance de otro ADR.

### Confirmación

`tests/test_itcp.py::test_pesos_internos_poder_legislativo_sin_bloqueo`,
`tests/test_itcp.py::test_todo_indicador_del_indice_declara_su_rezago`,
`tests/test_itcp.py::test_todo_indicador_del_indice_declara_su_familia`,
`tests/test_publicar.py::test_politica_itcp_reconcilia`,
`tests/test_procedencia_anclas.py::test_no_sobra_procedencia_de_indicadores_que_ya_no_puntuan`,
`tests/test_validacion_externa.py`, `tests/test_cierre_pymes.py`,
`tests/test_politica_sin_universo.py`. ITCP medido antes/después de la corrida
completa de política: ver el PR de esta decisión.

## Pros y contras de las opciones

- **1. Dejarlo como está:** el denominador vacío queda bien resuelto, pero el
  tablero sigue mostrando una card vacía en el mejor escenario legislativo
  posible — no ataca el problema real.
- **2. Inventar/arrastrar un valor:** ya descartado por ADR-0276 y por buenas
  razones; una tasa que no describe la ventana actual es peor que no
  publicarla.
- **3. Ocultar la card, mover el contenido a `desafios_legislativos`:** cumple
  la regla del proyecto, no pierde información (el registro y la serie siguen
  vivos), y hace que el cero se lea como lo que es. Costo: una card menos en
  el tablero público, y el peso de diseño de la dimensión cambia de forma
  visible en el código (aunque no en el resultado).

## Más información

- ADR-0069: creó el indicador («la cara ganada del pulso legislativo entra al
  ITCP»).
- ADR-0276: resolvió bien el denominador vacío; este ADR no lo contradice, va
  un paso más allá.
- ADR-0089: mismo patrón de retiro con redistribución de peso, para
  `derrotas_legislativas`.
- ADR-0168: mismo procedimiento de redistribución proporcional (en sentido
  inverso: ahí entraba un indicador y cedían peso, acá sale uno y lo ganan).
- ADR-0153/0216: la regla que esta decisión cumple («o integra el índice, o no
  es card»).
- Documento de indicadores, 15-sep-2026: objeción del equipo sobre el
  "preciosismo" del cinturón legislativo — parcialmente atendida, no cerrada.
