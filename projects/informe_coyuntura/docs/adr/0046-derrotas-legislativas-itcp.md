---
madr: 4
id: '0046'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_derrotas_legislativas, fetch_derrotas_legislativas_mensual]
archivos: ['scripts/politica.py', 'data/politica/derrotas_legislativas_eventos.json', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/gate_calidad.py', '.github/workflows/data-pipeline.yml', 'datos.ts', 'descripciones.ts', 'formulas.ts', 'fichas.ts', 'tests/test_itcp.py', 'tests/test_politica_derrotas.py']
relacionado: ['0069']
ambito: '`scripts/politica.py` (`fetch_derrotas_legislativas` y helpers) · `data/politica/derrotas_legislativas_eventos.json` (registro versionado, semilla verificada a mano) · `scripts/itcp.py` (banda nueva + pesos internos de poder_legislativo) · `scripts/descargar_series.py` (`fetch_derrotas_legislativas_mensual`) · `scripts/validacion_externa.py` (ITCP_SERIES) · `scripts/gate_calidad.py` (excepción G3) · `.github/workflows/data-pipeline.yml` (git add del registro) · web (`datos.ts`/`descripciones.ts`/`formulas.ts`/`fichas.ts`) · `tests/test_itcp.py` · `tests/test_politica_derrotas.py`'
---

# ADR-0046 — `derrotas_legislativas`: nuevo indicador del ITCP (vetos insistidos + decretos rechazados, fusionados)

## Contexto y planteo del problema

Las insistencias de septiembre-octubre de 2025 (leyes 27.793, 27.795 y
27.796) fueron las **primeras que revirtieron vetos presidenciales desde
2003**, y el mismo trimestre cerró la ola de decretos derogados por el
Congreso (DNU 656/24 en 2024 —primer DNU derogado desde la reforma de
1994— y los cinco decretos de agosto de 2025). Ningún indicador del ITCP
capturaba ese pulso: `veto_quorum` mide sesiones fracasadas (amagues, no
derrotas), `eficacia_legislativa` mide la agenda propia aprobada, y
`ratio_dnu` mide cuánto USA el decreto el Ejecutivo, no cuánto se lo
devuelve el Congreso.

Dos investigaciones de factibilidad independientes (2026-07-09, una por
familia de eventos) verificaron contra fuente primaria los 32 meses del
mandato y probaron en vivo la extracción automática:

- **Vetos** (InfoLeg): la unión de 3 búsquedas de frase exacta
  (`"observase en su totalidad"` + `"observa en su totalidad"` +
  `"promulgacion parcial"`, tipoNorma=2) recupera los 10 proyectos vetados
  dic-2023→jul-2026 con 0 falsos positivos y 0 falsos negativos; la
  insistencia se detecta de forma binaria porque el proyecto vetado aparece
  publicado como Ley con fecha posterior al decreto (10/10 verificados;
  una ley publicada el MISMO día es la promulgación parcial del propio
  decreto, caso 27.739).
- **Decretos** (Senado): el listado de actas por año (el mismo POST
  paginado que ya usa `cohesion_bloque_senado`) trae el título de cada
  votación, y toda votación de decreto bajo la ley 26.122 lleva la fórmula
  estable "en los términos de la ley 26.122" (8/8 casos reales; excluye
  sola a los falsos amigos: mociones de orden, el decreto simple 681/25,
  la reforma trunca de la propia 26.122). En esas actas se vota la
  **validez** del decreto: gana NEGATIVO = rechazo (verificado en los 8).

## Opciones consideradas

- **"% de vetos sostenidos" como indicador standalone** (la métrica
  candidata de la investigación de vetos) — descartada al fusionar: con
  n=1-3 vetos en ventana un solo evento movía 33-100 pp (denominador
  chico), y la ventana se vacía por completo si pasa un año sin vetos
  (valor clavado en 100 con flag). El conteo absoluto fusionado elimina
  el denominador y reparte los eventos raros entre dos familias.
- **"DNUs caídos" como indicador mensual autónomo** — NO-GO con datos
  reales: la serie "% de decretos rechazados / DNUs dictados 12m" cambia
  3 veces de numerador en 32 meses y tiene la señal invertida en 2026
  (el % *empeora* solo porque el denominador —DNUs dictados— se achica,
  justo cuando el control real del Congreso desapareció: cero
  tratamientos en recinto en 2026). Además el denominador automatizable
  (full-text InfoLeg) sobrecuenta ~50% contra los conteos académicos.
- **Contar por votación de cámara en vez de por norma** (cada rechazo o
  insistencia de cada cámara suma; serie 0→3→pico 16) — descartada: el
  rechazo de la segunda cámara es la misma derrota política que la
  primera consumó (contarlo dos veces duplica el mismo hecho), y la
  fecha del evento queda mejor definida por la consumación. La
  definición por norma también deja el registro alineado con la lectura
  editorial de la card ("N vetos insistidos + M decretos rechazados").
- **Detectar los rechazos de Diputados vía los PDFs de actas
  (ADR-0040)** además del Senado — pospuesta: exigiría extender la caché
  permanente por acta para guardar títulos y caminar ids con agujeros
  404; el costo no se justifica hoy porque el Senado terminó votando
  todos los decretos politicamente relevantes del período (la fecha se
  correría ~2 semanas en el peor caso real) y la semilla histórica ya
  tiene las fechas exactas de Diputados. Queda como refinamiento posible
  post-lanzamiento, documentado como limitación en la ficha.
- **Ventana de 24 meses** para suavizar los cliffs — descartada por
  inconsistencia con el estilo 12m del resto del cinturón; el cliff es
  una propiedad del fenómeno (eventos raros) y se declara en la ficha en
  vez de disimularse con fórmula.

## Decisión

**Un solo indicador fusionado**: `derrotas_legislativas` = conteo
absoluto, en ventana móvil de 12 meses, de las derrotas legislativas
consumadas del Ejecutivo — vetos insistidos por ambas cámaras (2/3,
art. 83 CN) **+** decretos (DNU/delegados) rechazados por al menos una
cámara bajo la ley 26.122. Cada norma cuenta **una vez**, fechada en el
mes de la derrota consumada (insistencia de la segunda cámara / primer
rechazo en recinto). Menor = mejor.

- **Registro de eventos versionado** en
  `data/politica/derrotas_legislativas_eventos.json`: semilla con los 10
  eventos históricos verificados (3 vetos insistidos + 7 decretos
  rechazados) + detección incremental en cada corrida (vetos e
  insistencias vía InfoLeg; decretos vía actas del Senado con memoria de
  actas ya procesadas). Los eventos consumados son inmutables; los vetos
  con media insistencia pendiente (27.790, 27.794 — sin plazo de
  caducidad) se re-verifican en cada corrida. El archivo está en el git
  add del cron desde este mismo cambio (regla del proyecto).
- **Serie mensual determinística** dic-2023→hoy derivada del registro
  (`descargar_series.fetch_derrotas_legislativas_mensual`), misma ventana
  y conteo que la card. Entra a la reconstrucción del ITCP de
  `validacion_externa.py` como el resto.
- **Anclas** (BANDAS_ITCP, menor = mejor, tramos extremos abiertos):

  ```python
  (-INF, 1.0, 100), (1.0, 3.0, 85), (3.0, 8.0, 65), (8.0, 14.0, 40), (14.0, INF, 10)
  ```

  Calibradas contra la serie mensual reconstruida real (32 meses):
  valores observados {0×3, 1×10, 2×7, 5×1, 6×1, 8×10} → 13/7/12/0/0 por
  banda. Las dos bandas inferiores quedan vacías **a propósito** como
  margen para confrontaciones más intensas que el pico real (8 derrotas
  en ventana desde oct-2025), mismo criterio que el hueco documentado de
  `cohesion_bloque_senado` (ADR-0039). El indicador nace **sin** estado
  provisional. A valores de jul-2026 (8 derrotas: 3 vetos insistidos + 5
  decretos) el puntaje interpolado es 53,6.
- **Pesos internos de poder_legislativo** (30% del ITCP) redistribuidos:
  ratio_dnu 25→20 · eficacia_legislativa 30→25 · veto_quorum 20→15 ·
  comisiones_caidas 25→20 · **derrotas_legislativas 20**. Racional:
  eficacia sigue primera (la medida más abarcativa); las derrotas entran
  al nivel de ratio_dnu/comisiones porque son la expresión más directa
  del balance Ejecutivo-Congreso (con ratio_dnu forman el par "gobernar
  por decreto / sostener la norma propia"); veto_quorum cede más por ser
  la medida más estrecha.
- **Excepción G3 declarada**: la card cuenta los 12 meses calendario
  anclados al mes en curso (parcial); la serie, a cada fin de mes cerrado
  — con eventos discretos difieren de a enteros cada vez que un evento
  entra o sale de la ventana durante el mes corriente (misma familia de
  anclaje que votometro/cohesión, pero con saltos enteros en vez de
  décimas).

### Consecuencias

- El ITCP gana su 13.ª banda activa y "poder legislativo" pasa de 4 a 5
  indicadores. Efecto material HOY (simulado contra el caché vigente del
  2026-07-09): casi nulo — el puntaje del indicador (8 derrotas → 53,6
  interpolado) cae muy cerca del promedio actual de su dimensión (la
  dimensión pasa de 47,5 a 48,8 con los pesos nuevos; ITCP 70,9 → 70,9,
  tensión 2,9 sin cambio). El indicador no entra para mover el índice de
  hoy sino para que el índice VEA este frente: cuando la tanda de
  ago-oct 2025 salga de la ventana (ago-nov 2026), la serie caerá
  mecánicamente 8→3→0 y el puntaje subirá hacia 85-100 — un
  "aflojamiento" de aritmética de ventana, declarado como limitación en
  la ficha; y una tanda nueva de derrotas lo hundiría de inmediato, que
  es exactamente la señal que hoy falta.
- Riesgos declarados y monitoreables: (i) cliffs mecánicos de ventana
  móvil cuando la tanda de ago-oct 2025 salga de la ventana (ago-oct
  2026) — la serie caerá 8→0 por aritmética; (ii) si una futura reforma
  de la ley 26.122 reintrodujera caducidad automática o derogación por
  rechazo de una sola cámara, cambia el régimen del indicador →
  recalibrar y nuevo ADR; (iii) una cuarta variante de sumario de veto
  en InfoLeg escaparía a las tres frases — mitigable con una consulta de
  contraste (palabra `veto` + tema del listado) si alguna vez se observa.
- El evento "decreto 681/25" (suspensión de la ley insistida 27.793,
  rechazado por el Senado fuera del carril 26.122) queda fuera del
  conteo por diseño: el filtro por la fórmula legal lo excluye solo, y
  el indicador mide derrotas terminales del régimen de control, no todo
  revés parlamentario.
