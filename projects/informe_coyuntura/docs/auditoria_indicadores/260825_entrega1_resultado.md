# Entrega 1 — resultado

**Fecha:** 25 de agosto de 2026 · **Estado:** código, tests y ADR completos.
**No se corrió el pipeline ni se publicó nada**: los valores de abajo son el
impacto calculado sobre el snapshot auditado, sustituyendo únicamente los
puntajes de los indicadores corregidos.

Línea de base congelada en [`linea_base_260825.json`](linea_base_260825.json)
(69 indicadores, `sha256` del snapshot `83543334655b…`, score global 3,9).
Comparador: `scripts/manifiesto_remediacion.py`.

## Los siete casos

| # | Indicador | Antes | Después | Causa raíz | ADR |
|---|---|---:|---:|---|---|
| 1 | `costo_financiamiento_tesoro` | 8,07% real | **4,92% real** | La TIREA se reconstruía desde precio y fechas capitalizando por meses de calendario enteros en vez del plazo real. Es un dato publicado: `(1+TEM)^12−1`. | 0238 |
| 2 | `iaf_transferencias` | +0,8% real | **+1,6% real** | Un solo IPC promedio anual para doce flujos con estacionalidad propia. Se deflacta mes a mes desde la planilla mensual de Hacienda. | 0239 |
| 3 | `cobertura_judicial` | 69,63% | **69,63%** | El valor era correcto; el texto lo explicaba con otra definición y otro corte («604 de 955» = 63,25%). Ahora publica numerador, denominador y fecha de cada uno. | 0240 |
| 4 | `ratio_dnu` | 1,92 | **1,48** | Contaba coincidencias textuales de «necesidad y urgencia» (48) en vez de decretos tipificados como DNU (37). | 0241 |
| 5 | `icc_utdt` | 39,9 | **40,2** | Leía la columna 1 por posición, que es `ICC Capital`. Se publicaba CABA rotulado como total nacional. | 0242 |
| 6 | `consumo_supermercados` | 83,2 · «2004=100» | **83,2 · 2017=100** | Base rotulada a mano y equivocada. Ahora se lee de los metadatos de la fuente. **El período sigue en mayo: ver abajo.** | 0243 |
| 7 | `concesiones_infraestructura` | 28,7% | **100%** | Decidía por el estado de CONTRAT.AR, que se queda viejo. Dos etapas ya estaban adjudicadas por resolución publicada. | 0244 |

## Lo que la auditoría no había visto

En el caso 7, la auditoría detectó la **Etapa III** (Res. 1379/2026, 24-ago) y
estimó ≈71,65%. La **Etapa II-B** también estaba adjudicada, por **Resolución
1149/2026 del 28 de julio** — casi un mes antes del corte, y CONTRAT.AR seguía
mostrándola como disponible. Con las cuatro etapas, el plan está entero
adjudicado: **100%**, no 71,65%.

Confirmado en el texto del Boletín Oficial de la 1379/2026 (ocho tramos con sus
adjudicatarios) y en la cobertura de prensa de la 1149/2026 (cuatro tramos,
adjudicatarios nombrados).

## Impacto sobre los índices

Sustituyendo sólo los puntajes de banda corregidos sobre los pesos publicados.
El control reproduce el snapshot dentro del redondeo.

| Cinturón | Índice antes | Índice después | Δ | Tensión antes | Tensión después |
|---|---:|---:|---:|---:|---:|
| Macro (ITCM) | 64,0 | 64,6 | +0,52 | 3,6 | **3,5** |
| Política (ITCP) | 67,0 | 68,3 | +1,32 | 3,3 | **3,2** |
| Vida cotidiana (ITVC) | 94,57 | 94,62 | +0,05 | 6,1 | 6,1 |
| Gestión (ITCG) | 73,0 | 74,7 | +1,66 | 2,7 | **2,5** |
| **Score global** | | | | **3,9** | **3,8** |

Puntajes de banda que se movieron:

| Indicador | Banda antes | Banda después |
|---|---:|---:|
| `costo_financiamiento_tesoro` | 78,9 | 92,0 |
| `iaf_transferencias` | 76,6 | 78,2 |
| `ratio_dnu` | 16,0 | 44,6 |
| `concesiones_infraestructura` | 44,6 | 100,0 |
| `cobertura_judicial` | 51,6 | 51,6 (sin cambio) |
| `icc_utdt` (rebase, no banda) | 91,2 | 91,9 |

**Todos los movimientos son en la misma dirección: los cuatro cinturones bajan
su tensión.** No es casualidad ni sesgo del método: de los siete errores, cinco
subestimaban el desempeño y ninguno lo sobreestimaba. Vale la pena tenerlo
presente al leer el resultado.

## Lo que queda abierto

**`consumo_supermercados` sigue publicando mayo de 2026.** La auditoría pide
junio = 82,1. El INDEC lo publicó el 21-ago; la API de series de datos.gob.ar
todavía termina en mayo, con el valor sin revisar. El PDF del informe no es
direccionable —su nombre lleva un hash y el sitio devuelve 200 con el shell de
la SPA para cualquier ruta, así que ni el sitemap, ni `/rss`, ni `/feed`, ni el
directorio de informes permiten derivarlo—. Cerrarlo requiere incorporar una
fuente nueva, que es una decisión de alcance.

Lo que sí queda cubierto: el día que la API espeje junio, la card pasa a 82,1 y
mayo se corrige a 83,0 sin intervención, y hay un test que lo prueba con esos
números exactos.

## Riesgos y decisiones anotadas

- **Reaperturas de deuda (caso 1).** El indicador informa la tasa contractual
  del instrumento, no el rendimiento marginal del precio de corte. Es una
  limitación declarada en el ADR-0238: la variante marginal mide mejor el costo
  pero depende de una reconstrucción del payoff que no se pudo verificar contra
  ninguna gacetilla de reapertura.
- **Adjudicaciones parciales (caso 7).** Las etapas se cuentan enteras. Hoy no
  cambia nada porque las cuatro están adjudicadas por completo; una etapa a
  medias contaría como total.
- **Dependencia de rótulos ajenos (casos 4, 5 y 7).** El filtro de DNU depende
  del rótulo de InfoLeg, la columna del ICC de los encabezados de la UTDT y la
  detección de adjudicaciones de una frase propia de esta licitación. Los tres
  fallan **ruidosamente** si la fuente cambia, que es el modo de falla que se
  prefiere sobre el anterior.

## Verificación

- `pytest tests -q`: **2878 pasan**, 3 se saltean.
- `npx tsc --noEmit`: limpio.
- Cada corrección tiene fixture congelado con su fuente y fecha, y **todas las
  guardas se probaron rompiéndolas**: revertida la lógica al comportamiento
  anterior, fallan (5 · 2 · 4 · 8 · 2 · 5 · 4 tests respectivamente).
- No se tocó ninguna salida versionada ni el trabajo local ajeno
  (`scripts/aviso_informe.py` sigue intacto y sin versionar).
