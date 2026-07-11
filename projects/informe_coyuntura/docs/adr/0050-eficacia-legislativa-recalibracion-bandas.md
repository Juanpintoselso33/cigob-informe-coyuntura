# ADR-0050 — `eficacia_legislativa`: recalibración de bandas contra la serie real (truncamiento estructural de la ventana única)

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-11 |
| **Ámbito** | `scripts/itcp.py` · `scripts/politica.py` (docstring) · `web/src/lib/fichas.ts` |
| **Precedente directo** | ADR-0045 (`comisiones_caidas`, misma patología), ADR-0038/0039/0042 (recalibraciones con backfill real), ADR-0021 (interpolación, tramos extremos abiertos) |

## Contexto

`eficacia_legislativa` (% de proyectos del PE aprobados, ventana móvil 365
días, datos abiertos HCDN) puntuaba con anclas 5/15/35/55 heredadas de la
fórmula ad hoc pre-paramétrica (`(70 − valor) / 7`), nunca validadas contra
la serie real del indicador. Era el único indicador del cinturón que quedaba
sin el tratamiento de recalibración que ya recibieron `comisiones_caidas`
(ADR-0045), `alineamiento_senadores_prov` (ADR-0038) y las dos cohesiones
(ADR-0039/0042).

Contra los **32 puntos mensuales reales** de `output/series/politica.csv`
(dic-2023→jul-2026): rango observado **0–8,7%** (media 2,4, mediana 0). Los
32 meses caían en las dos bandas más bajas (puntaje 10–40) — cero
discriminación en un indicador que pesa el 7,5% del ITCP y que el informe
venía mostrando como "el frente que concentra la tensión del cinturón".

**El hallazgo que motiva la recalibración no es solo la distribución: la
métrica tiene truncamiento estructural.** El numerador exige que la SANCIÓN
caiga dentro de la MISMA ventana de 365 días en que se publicó el proyecto
(`fetch_eficacia_legislativa`: `PUBLICACION_FECHA >= cutoff` ∧
`FECHA_movimiento >= cutoff`). Un proyecto enviado hace pocos meses casi
nunca llegó a sancionarse todavía, así que buena parte del denominador es
estructuralmente "demasiado joven" para contar en el numerador: ni un
Ejecutivo con mayoría sólida podría acercarse al 35–55% de las anclas
viejas. Es la misma patología, en espejo, que ADR-0045 documentó para
`comisiones_caidas` (un dictamen reciente casi nunca se sanciona dentro de
su propia ventana). Las anclas viejas describían la tasa de aprobación de
un congreso de manual, no esta métrica.

## Decisión

Anclas nuevas **1/3/5/7** (números redondos, mayor = mejor, tramos extremos
abiertos según ADR-0021):

`(7,∞)→100 · (5,7]→85 · (3,5]→65 · (1,3]→40 · (−∞,1]→10`

Chequeadas contra los 32 puntos reales: distribución **4/2/8/0/18** por
banda.

- Los cortes caen en los huecos reales de los datos: la serie tiene tres
  regímenes — 18 meses en 0,0 exacto (cero sanciones en la ventana), un
  clúster en ~3,7–4,3 (un aprobado sobre ~23-25 enviados) y un clúster en
  ~6,5–8,7 (la era Ley Bases, jun-2024→mar-2025).
- **El hueco de la banda 40 (1–3%) es estructural y queda como margen**:
  con ~23-25 proyectos/año de denominador, un solo aprobado ya da ~4% —
  valores de 1-3% solo aparecen si el PE duplicara el envío de proyectos.
  Mismo criterio que el hueco documentado de `cohesion_bloque_senado`
  (ADR-0039) y las bandas inferiores vacías de `derrotas_legislativas`
  (ADR-0046).
- **Los 18 ceros van todos al piso y son indistinguibles entre sí por
  diseño** (caveat ADR-0042): cero aprobaciones en un año es la señal real
  de mínima capacidad, no un artefacto a repartir entre bandas.
- La alternativa 2/4/6/8 se descartó: reparte 1/5/3/5/18 pero pone un corte
  (4,0) adentro del clúster de "un aprobado" — 4,0 (1/25) y 4,3 (1/23) son
  la misma realidad política con distinto denominador; un borde ahí
  convierte ruido de denominador en cambios de banda.

## Opciones descartadas

- **Dejar las anclas viejas como señal editorial** ("el piso ES la
  noticia: el gobierno no aprueba leyes"): descartado — el nivel absoluto
  lo comunica el `valor` de la card (4,3%, 1 de 23); el puntaje del índice
  necesita discriminar entre los regímenes reales del período (0% ≠ 4% ≠
  8%), que es exactamente el argumento que ganó en ADR-0045. Además el
  techo 35-55% es inalcanzable por construcción de la métrica, no por
  debilidad política: mantenerlo no es exigencia editorial, es un error de
  escala.
- **Rediseñar la métrica para eliminar el truncamiento** (p. ej. cohortes:
  % de proyectos enviados hace 12-24 meses ya sancionados): fuera de
  alcance — cambia la definición del indicador publicado y la serie
  entera; la recalibración resuelve el problema de scoring sin tocar la
  semántica de la card. Queda como candidato si una revisión editorial
  futura pide medir "tasa de éxito final" en vez de "eficacia en ventana".

## Consecuencias

- Con el valor vigente (4,3%): puntaje 10,0 → ~65 interpolado; la dimensión
  poder legislativo 48,8 → **63,3**; **ITCP 72,9 → 77,2** (tensión 2,7 →
  **2,3**), banda sigue "moderadamente aflojado". Salto esperable de la
  recalibración, no un error — misma clase que documentaron ADR-0045 y
  ADR-0048.
- La reconstrucción histórica de `validacion_externa.py` gana varianza en
  el componente: los meses de la era Ley Bases (7-9%) pasan de puntaje ~40
  a 85-100 mientras los 18 meses en cero siguen en el piso. El r ITCP↔EPU
  se recalcula en la misma corrida (regla de 2026-07-09: la validación va
  DENTRO del camino scoped al tocar `BANDAS_*`) y se reporta el valor que
  dé — las anclas se eligieron contra la distribución del propio
  indicador, no optimizando r.
- Ficha metodológica web actualizada (anclas nuevas + limitación nueva que
  declara el truncamiento estructural + entrada en `cambios`); de paso se
  corrigen los pesos internos stale de las 4 fichas de poder legislativo
  (decían 25/30/20/25, los previos a ADR-0046; son 20/25/15/20 y las
  listas de indicadores compañeros ahora incluyen a `derrotas_legislativas`).
- El docstring de `fetch_eficacia_legislativa` pierde la fórmula ad hoc
  pre-paramétrica que todavía citaba (`Score: 70%→0...`) y documenta el
  truncamiento de la ventana única.
- Sin cambios de serie ni cachés nuevos: solo bandas + textos. Los tests de
  `test_itcp.py` no pineaban las anclas viejas de este indicador (el caso
  de 60,0 → 100 sigue válido con tramos abiertos).
