---
madr: 4
id: '0047'
estado: 'aceptado'
fecha: 2026-07-09
cinturon: 'politica'
indicadores: [fetch_rotacion_gabinete, cohesion_interna, fetch_rotacion_gabinete_serie]
archivos: ['data/politica/gabinete_salidas.json', 'data/politica/gabinete_decretos_cache.json', 'scripts/politica.py', _detectar_salidas_gabinete_infoleg, 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', '.github/workflows/data-pipeline.yml', 'tests/test_itcp.py', 'tests/test_descargar_series_rotacion.py']
ambito: '`data/politica/gabinete_salidas.json` (nuevo, registro curado) · `data/politica/gabinete_decretos_cache.json` (nuevo, caché del detector) · `scripts/politica.py` (`fetch_rotacion_gabinete`, `_detectar_salidas_gabinete_infoleg`) · `scripts/itcp.py` (banda nueva + reponderación de `cohesion_interna`) · `scripts/descargar_series.py` (`fetch_rotacion_gabinete_serie`) · `scripts/validacion_externa.py` (ITCP_SERIES) · `.github/workflows/data-pipeline.yml` (git add) · capa web (datos/descripciones/formulas/fichas) · `tests/test_itcp.py`, `tests/test_descargar_series_rotacion.py`'
---

# ADR-0047 — rotacion_gabinete: la rotación ministerial entra al ITCP (pata ejecutiva de cohesión interna)

## Contexto y planteo del problema

La dimensión "cohesión interna del oficialismo" (20% del ITCP, ADR-0036) era
100% legislativa: `cohesion_bloque` (Diputados, 65%) y
`cohesion_bloque_senado` (35%). La cohesión del EJECUTIVO — donde se jugaron
las crisis de Posse, Mondino, el recambio post-electoral de fines de 2025 y
el escándalo Adorni de 2026 — no ponderaba en ningún lado del índice.

La literatura de rotación ministerial (Martínez-Gallardo 2014, *Comparative
Political Studies*; Camerlo & Pérez-Liñán 2015) trata la retención de
ministros como observable del capital político presidencial: los presidentes
gastan o conservan capital en sostener a su equipo, y las salidas no
programadas señalan crisis de coalición o escándalo — exactamente la lectura
matusiana de "capacidad de gobernar" que el ITCP dice medir.

Un estudio de factibilidad previo (2026-07-09) reconstruyó el registro
completo del fenómeno para el ciclo: 11 salidas de rango ministerial entre
dic-2023 y jul-2026, cada una verificada EN VIVO contra InfoLeg con su
decreto de aceptación de renuncia del BO, más 2 movimientos laterales
(Francos Interior→JGM 2024; Santilli Interior→JGM 2026) y 6
reestructuraciones de la Ley de Ministerios (el número de carteras fue
10→9→8→9→10→9). El mismo estudio prototipó un detector automático contra el
buscador de InfoLeg con recall 11/11 sobre los 32 meses.

## Opciones consideradas

- **Detector 100% automático, sin curaduría** — descartada: contaría los
  laterales (jun-2026 daría 2 salidas en vez de 1), fecharía por publicación
  en BO (dos meses corridos de desfase en el borde) y no sabe clasificar
  política vs. estructural. El costo real de la curaduría es bajísimo
  (~4 salidas/año, cada una con semanas de cobertura mediática).
- **Tasa de rotación (salidas 12m / cargos vigentes)** — descartada como
  métrica principal: el denominador cambió 4 veces por decisiones del propio
  gobierno; una fusión de ministerios subiría la tasa sin que haya más
  salidas — mete adentro de la métrica la reestructuración que se quiso
  separar. La forma de la curva es casi idéntica a la del conteo.
- **Antigüedad promedio del gabinete** — descartada: inercial por
  construcción (sube sola un mes por mes en calma), mezcla la señal de
  crisis con el paso del tiempo y su caída depende de la antigüedad del
  saliente (la eyección de un ministro nuevo casi no la mueve: Catalán).
- **Incluir las secretarías de Presidencia con rango ministerial** —
  descartada (ver universo); quedan documentadas en el registro y sumarlas
  no cambia la forma de la curva (acentúa los mismos picos).
- **Excluir el recambio post-electoral de la serie** — descartada (ver
  polaridad): más grados de libertad del analista, menos declarabilidad.
- **API REST de InfoLeg (datos.gob.ar)** como vía del detector — descartada:
  hoy exige token (`{"error":"missing_token"}`); el buscador web funciona
  sin credenciales con la misma mecánica de sesión ya usada por `ratio_dnu`
  y `desregulacion_normativa`.

## Decisión

### Métrica

**`rotacion_gabinete` = salidas de cargos de rango ministerial acumuladas en
ventana móvil de 12 meses**, imputadas al mes del **cese efectivo** (el hecho
político), no al de la publicación del decreto (el BO puede demorar hasta
~40 días: Ferraro, eyectado a fines de enero de 2024, decreto del 05-mar).
Menor = mejor.

### Universo de cargos (corte declarable)

Se cuenta: Jefatura de Gabinete de Ministros + todos los ministerios de la
Ley de Ministerios vigente en cada momento. Se excluyen las secretarías de
Presidencia aun con "rango y jerarquía de ministro" (Secretaría General,
Legal y Técnica, SIDE, Vocería): su rango es una asimilación
salarial/protocolar por decreto (no membresía del gabinete según la Ley de
Ministerios), la literatura de referencia define rotación sobre carteras, y
la SIDE además cambió de naturaleza jurídica en el período (AFI→SIDE, DNU
614/2024). Sus eventos quedan documentados aparte en el registro
(`secretarias_excluidas`) por robustez.

**No cuentan como salida**: (a) los movimientos laterales dentro del
gabinete — la persona sigue en el gabinete, contarla duplicaría el evento
político real (el Dto. 548/2026 acepta la renuncia de Adorni a JGM Y la de
Santilli a Interior en el mismo acto, pero la salida real es una); (b) las
reestructuraciones de la Ley de Ministerios (cartera creada/disuelta/
fusionada) — una fusión no es una eyección.

### Polaridad (la limitación honesta)

Una salida puede ser pérdida de capital (eyección por escándalo: Adorni) o
ejercicio de poder (reshuffle estratégico; Bullrich/Petri son ceses
programados por victoria electoral). Se cuentan **todas** las salidas, sin
distinguir, por tres razones: (1) objetividad del registro — excluir las
post-electorales exigiría una ventana de gracia arbitraria, más grados de
libertad del analista; (2) semántica matusiana defendible — incluso el
reshuffle "de poder" consume capital político real (curva de aprendizaje del
entrante, renegociación de equilibrios, señal de inestabilidad); (3)
simetría con el resto del ITCP — `movilizacion_cepa` no descuenta "protestas
legítimas" ni `ratio_dnu` "DNUs inevitables". Mitigación: el registro
clasifica cada salida (`salida_politica` / `salida_estructural_electoral`),
la card y la ficha publican la composición, y el caso extremo se administra
con el mecanismo estándar de override del analista (`ajustes_itcp.json`, con
justificación y vencimiento). La limitación queda declarada en la ficha
pública.

### Modelo de datos: registro curado + detector que avisa

Mismo patrón dos veces probado en el repo (`privatizaciones` del ITCG;
`adhesion_reformas_provincial`):

- **Fuente de verdad**: `data/politica/gabinete_salidas.json` — registro
  curado versionado; cada salida con persona, cargo, mes de cese efectivo,
  decreto BO de respaldo, clasificación, motivo y fuentes. Semilla: las 11
  salidas verificadas del estudio de factibilidad.
- **Detector de alerta InfoLeg** (`_detectar_salidas_gabinete_infoleg`), dos
  etapas, porque el buscador de InfoLeg es OR sobre palabras (imposible
  filtrar por cargo query-side) y trunca la síntesis del listado a ~150
  caracteres: E1 = listado mensual `texto="renuncia"` + `tipoNorma=2`
  (7-20 filas/mes); E2 = para las filas con tag de dependencia ministerial
  (`^JEFATURA DE GABINETE...` / `^MINISTERIO DE(L)`) y "RENUNCIA", detalle
  `verNorma.do` cacheado en disco (`gabinete_decretos_cache.json`, agregado
  al git add del cron — lección de los cachés pisados por el pipeline) y
  regex final de cargo sobre el resumen completo. Barrido: mes corriente +
  mes anterior (cubre el rezago de publicación del BO entre corridas).
  El detector **no modifica el registro**: si encuentra un decreto de
  renuncia ministerial no citado en el registro (comparación por número de
  decreto, robusta a re-salidas de la misma persona), imprime
  `[ALERTA] rotacion_gabinete` en el log de la corrida y anota la
  discrepancia en la card. Si InfoLeg falla, el indicador se publica igual
  desde el registro (que es local y no vence).
- **Serie**: `fetch_rotacion_gabinete_serie()` reconstruye la ventana 12m
  mes a mes desde dic-2023 hasta el mes corriente inclusive, determinística
  desde el registro y sin red. Con el mes corriente incluido, card y
  serie[-1] coinciden por construcción y el G3 del gate no necesita
  excepción.

Prototipo verificado en vivo (estudio de factibilidad): recall 11/11 salidas
reales en el backfill dic-2023→jul-2026; precisión léxica 100% en 31 meses
de gobierno propio (jueces, fiscales, embajadores, directorios y "ministros
plenipotenciarios" del servicio exterior quedan excluidos por el tag de
dependencia y el regex de cargo). Falsos positivos conocidos y por eso
curados, no automatizados: el mes de transición dic-2023 (renuncias del
gabinete saliente), los laterales (formalmente SON renuncias) y la fecha por
BO en vez de cese efectivo (difiere en 2 de 11 casos).

### Anclas (BANDAS_ITCP) y reponderación

```python
"rotacion_gabinete": [                # salidas 12m, menor = mejor
    (-INF, 1.0, 100),   # 0-1: recambio fisiológico   (7/32 meses)
    (1.0, 2.0, 85),     # 2: recambio bajo            (8/32)
    (2.0, 4.0, 65),     # 3-4: rotación sostenida     (9/32)
    (4.0, 6.0, 40),     # 5-6: crisis de gabinete     (6/32)
    (6.0, INF, 10),     # 7+: crisis abierta          (2/32)
]
```

Calibradas contra la serie real de 32 meses (0→4 en 2024 → mínimo 1 en
sep/oct-2025 → 5 en dic-2025 → 7 en jun-2026, máximo): distribución por
banda 7/8/9/6/2, **las cinco bandas pobladas con datos reales** (criterio
ADR-0042), números redondos, tramos extremos abiertos (ADR-0021). El
indicador nace discriminando (puntaje interpolado recorre 10-100 sin
aplanarse), a diferencia de `cohesion_bloque`, que nació saturado y hubo que
recalibrar. Alternativa considerada: cortes 1/2/4/7 (deja margen para colas
peores, pero la banda superior queda vacía, 0/32) — se prefirió la variante
con datos en las cinco bandas, aceptando que 6 y 7 salidas saturan igual en
el piso: a ese nivel la lectura es "crisis abierta" en ambos casos.

Dimensión `cohesion_interna` (20% del ITCP, pesos entre dimensiones del
ADR-0036 intactos):

```python
"indicadores": {"cohesion_bloque": 0.45, "cohesion_bloque_senado": 0.25,
                "rotacion_gabinete": 0.30}
```

El par legislativo conserva su ratio interno 65/35 ≈ 45/25; la pata
ejecutiva entra con 30%.

### Consecuencias

- La dimensión "cohesión interna" deja de ser unidimensional-legislativa:
  dos patas (Congreso 70% / Ejecutivo 30%). Los pesos entre dimensiones no
  cambian.
- Alta de un artefacto MANUAL más a mantener: ante cada salida ministerial
  hay que agregar la entrada al registro (persona, cargo, mes de cese,
  decreto, clasificación, fuentes — ver `_meta.mantenimiento`). El detector
  convierte el olvido en una alerta visible en el log del pipeline, no en un
  dato silenciosamente viejo.
- La serie se reinicia con cada presidencia: mide el gobierno en ejercicio;
  el recambio total de un fin de mandato es diseño institucional, no crisis
  (documentado como limitación en la ficha).
- Si alguna vez hay >7 salidas en 12 meses, el motor interpolado satura en
  10 sin romperse; recalibrar solo ante un desplazamiento sostenido del
  rango (doctrina ADR-0042).
- InfoLeg puede cambiar el HTML del buscador: mismo riesgo ya asumido por
  `ratio_dnu`/`desregulacion_normativa` (mecánica compartida). El indicador
  NO depende de InfoLeg para publicar (registro en disco), solo para alertar.
