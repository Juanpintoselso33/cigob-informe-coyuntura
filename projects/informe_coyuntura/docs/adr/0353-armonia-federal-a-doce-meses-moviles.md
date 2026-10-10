---
madr: 4
id: '0353'
estado: 'aceptado'
fecha: 2026-10-10
cinturon: 'politica'
indicadores: [iaf_transferencias]
archivos: ['scripts/politica.py', 'scripts/descargar_series.py', 'scripts/itcp.py', 'config.py', 'tests/test_politica_iaf_12m.py', 'tests/test_politica_iaf_frescura.py', 'tests/test_politica_iaf_deflactor.py', 'tests/test_out_of_sample.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/datos.ts']
relacionado: ['0036', '0065', '0066', '0092', '0104', '0121', '0239', '0263']
ambito: 'Cinturón política · ITCP · `iaf_transferencias` · ventana de comparación: de año calendario cerrado a 12 meses móviles'
origen: 'Revisión de fuentes flojas, 10-oct-2026: el indicador estaba al 31-dic-2025, con diez meses de rezago, y la planilla de Hacienda ya traía enero a septiembre de 2026'
---

# ADR-0353 — La armonía federal se mide a doce meses móviles

## Contexto y planteo del problema

`iaf_transferencias` comparaba el último **año calendario cerrado** contra el
anterior (`year_ref = date.today().year - 1`, y `_iaf_real_por_anio` sólo
aceptaba años con los doce meses). El 10-oct-2026 la card decía «2025 vs 2024»,
con fecha del dato 2025-12-31: diez meses de rezago, aunque la planilla de
Hacienda que el colector ya baja
(`informacion_consolidada_2026_6.xlsx`) trae enero a septiembre de 2026.

Medido ese día (no copiado de un documento):

- **Planilla**: hojas mensuales hasta 2026-09.
- **IPC** (INDEC, `148.3_INIVELNAL_DICI_M_26`): último mes publicado, 2026-08.
- Por lo tanto el último mes con **ambas** cosas es agosto de 2026.

## Factores de decisión

- Que la fecha del dato sea la del último mes que se puede medir, sin esconder
  el rezago (ADR-0239 y el arreglo del 29-jul-2026 ya cerraron ese camino).
- Mantener la medida que ya está contrastada contra IARAF/Politikon (+1,6% para
  2025, ADR-0239) y las bandas del ITCP (ADR-0121).
- No comparar nunca un tramo incompleto contra uno entero (el modo de falla
  del año en curso).

## Opciones consideradas

1. **Acumulado del año en curso** contra el mismo tramo del año anterior
   (ene-ago 2026 contra ene-ago 2025: −1,18% real). Mezcla estacionalidad: los
   primeros meses no tienen el peso de mayo ni el de diciembre, y la escala
   cambia mes a mes (un enero y un agosto no son comparables entre sí).
2. **Doce meses móviles contra los doce previos**, con fecha del dato igual al
   último mes con IPC. Misma escala que la variación anual; en diciembre
   coincide exactamente con el año calendario.
3. Dejar el año cerrado y declarar el rezago.

## Decisión

Opción 2.

- `_iaf_12m_moviles()` devuelve, para cada mes `t` con 24 meses de planilla e
  IPC, la variación real de `t-11…t` contra `t-23…t-12`, deflactando cada flujo
  por el IPC de su propio mes (ADR-0239). La card toma el último `t`;
  `_iaf_real_por_anio()` queda como la ventana de diciembre.
- `fecha_dato` es el último día de `t`. `periodo` lo dice: «sep 2025–ago 2026 vs
  sep 2024–ago 2025».
- **Unidad.** El CSV anual que ancla la unidad (ADR-0239) llega a 2025. El año
  en curso hereda el factor del año anterior, con una guarda: si el nivel
  mensual medio se aleja más de cinco veces del anterior el cálculo falla
  (un cambio miles/millones es ×1000, la inflación anual no se acerca).
- **Serie**: un punto por mes (`YYYY-MM-01`, el último mes de la ventana) desde
  nov-2018, en vez de uno por año. Los puntos de diciembre son los de antes
  (2018 +6,7 · 2019 −1,4 · 2020 −4,1 · 2021 +7,3 · 2022 +6,3 · 2023 −4,4 ·
  2024 −9,8 · 2025 +1,6).
- **Valor de hoy**: a agosto de 2026, **−1,8% real** (nominal +30,5%). Contra
  los benchmarks: OPC −1% a agosto, Politikon −1,3% a julio, Fundación
  Encuentro −1,2% a agosto; son acumulados de enero, no 12 meses, así que no
  son la misma medida: la opción 1 con este mismo código da −1,18%, que sí
  coincide con ellos. La móvil mes a mes: dic-2025 +1,6 · ene-2026 0,0 · feb −2,0
  · mar −3,2 · abr −4,1 · may −0,6 · jun −1,5 · jul −1,6 · ago −1,8.
- **Bandas del ITCP: no se tocan.** Son conceptuales, ancladas en el cero con
  cortes simétricos de 10 pp (ADR-0121), y una variación real de 12 meses
  móviles está en la misma escala que la anual. Se verificó con la serie mensual
  nueva (94 puntos): rango −12,9…+11,7, con 61 puntos anteriores a dic-2023 y 33
  desde entonces; saturación 8% fuera de muestra y 0% adentro, y el test fuera
  de muestra (ADR-0104) lo marca «discrimina en ambas ventanas». Ninguna
  evidencia pide mover un corte.
- **Rezago del gate**: se borra el tope propio de 560 días de `MAX_DIAS`. El
  rezago real es el del IPC (~45 días) más el mes hasta el siguiente (~75 días
  como máximo), dentro del default de 110. Dejar 560 haría que un indicador
  mensual congelado tardara año y medio en avisar.
- **Rezago del índice** (`REZAGO_MESES_ITCP`): de 12,0 a 7,5 meses (centroide de
  la ventana, 6, más ~1,5 de IPC), el mismo criterio que `brecha_obra_publica`.
  Baja el rezago promedio que declara el ITCP.

### Consecuencias

- Buena: el dato pasa de 10 a ~1,3 meses de rezago y se actualiza todos los
  meses; la ficha, la fórmula y la descripción dicen lo mismo que el colector.
- Neutra: el valor de la card se mueve con cada planilla nueva, y como la
  ventana es móvil hereda el efecto de base del año previo durante doce meses.
- Mala: la serie mensual hace que `iaf_transferencias` entre al análisis fuera
  de muestra y a la reconstrucción histórica del ITCP todos los meses, no sólo
  cada diciembre. ADR-0092 y ADR-0104 decían, hasta hoy, que era anual y no
  evaluable: dejan de ser ciertos en esos puntos (no se reescriben, ver la
  política de este directorio). `tests/test_out_of_sample.py` deja de exigir a
  este indicador como ejemplo de ventana chica. Para no mezclar gestiones, la reconstrucción enmascara
  el indicador antes de dic-2024 (la primera ventana toda de la gestión actual,
  como ya ocurría con la serie anual). Los r de
  `validacion_externa.json` cambian en la próxima corrida; no se regeneraron en
  este cambio. Tampoco la card, la serie ni el snapshot: hasta la próxima
  corrida de datos la web muestra el valor anual anterior con la ficha nueva.

### Confirmación

`tests/test_politica_iaf_12m.py` calcula a mano ventanas sintéticas (−10%,
−13,33%, 0%) y comprueba que la ventana termina en el último mes con IPC aunque
la planilla llegue un mes más, que no da el acumulado del año, que la ventana de
diciembre coincide con el año calendario y que un salto de unidad en la planilla
corriente detiene el cálculo. Control positivo y negativo en la misma corrida.

## Pros y contras de las opciones

- Opción 1: simple de explicar, pero estacional y no comparable con la escala
  de las bandas.
- Opción 2: misma escala, fecha actual, una función para card y serie.
- Opción 3: honesta con el rezago, pero deja a la dimensión federal del ITCP
  hablando de 2025 en octubre de 2026.

## Más información

Planilla: argentina.gob.ar/economia/sechacienda/asuntosprovinciales/ron. La
fila que origina este cambio está en `docs/pendientes-datos.md`
(`iaf_transferencias`).
