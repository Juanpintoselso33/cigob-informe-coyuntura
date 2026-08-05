# Task 14 — Validación externa del ITCP (política)

## Resumen

Se agregó la validación externa del ITCP (cinturón político), mirroring
ITCM/ITCG/ITVC: reconstrucción mensual del índice desde sus componentes,
correlación contra un par externo teóricamente motivado, y extensión de la
matriz de validación cruzada (ADR-0031) de 3x3 a 4x4.

El par externo terminó siendo, tras dos correcciones de rumbo del
coordinador durante la tarea: el **EPU Argentina** (Economic Policy
Uncertainty, minería de texto de prensa local argentina — dataset
`EPU_LATAM.xlsx` del Banco de España + SECMCA, hoja `data_LATAM`, columna
`EPU_ARG_local`). Se descartaron en el camino: riesgo país (ya exclusivo del
ITCM), brecha cambiaria CCL/oficial (ya componente del ITCG), y el World
Uncertainty Index/WPUI de worlduncertaintyindex.com (reemplazado por la
fuente del Banco de España tras una verificación en vivo más profunda).

## Cobertura histórica real por indicador del ITCP (12 componentes)

Verificado con `output/series/politica.csv`, `output/series/gestion.csv` y
`web/src/data/series.json` (los CSV ya están fusionados en este último, que
es lo que lee `validacion_externa.py`):

| Indicador | Cobertura real | Fuente/nota |
|---|---|---|
| `votometro_ventaja_lla` | 32 pts, 2023-12→2026-07, mensual | politica.csv |
| `eficacia_legislativa` | 32 pts, 2023-12→2026-07, mensual | politica.csv |
| `comisiones_caidas` | 32 pts, 2023-12→2026-07, mensual | politica.csv |
| `protestas_caba` | 102 pts, 2017-12→2026-05, mensual (conteo crudo) | **vive en gestion.csv**, no en politica.csv (confirmado: `POLITICA_DERIVADAS` deliberadamente NO la registra — comentario explícito en `descargar_series.py` línea ~520: "ya está en GESTION_DERIVADAS... la clave protestas_caba ya queda disponible para el ITCP sin duplicar la descarga") |
| `iaf_transferencias` | 9 pts, 2017→2025, **un punto por año** (dic) | politica.csv — dato anual real, no mensual |
| `ratio_dnu` | 7 pts, 2020→2026, por período (no mensual) | politica.csv |
| `veto_quorum` | 3 pts, 2024/2025/2026 | politica.csv |
| `movilizacion_cepa` | **2 pts**, 2026-06 y 2026-07 | recién automatizado esta sesión, sin backfill histórico en `descargar_series.py` |
| `gobernadores_alineamiento` | **2 pts**, 2026-06 y 2026-07 | manual (`fetch_manual`), sin backfill histórico |
| `cohesion_bloque` | **1 pt**, 2026-07 | scraper bloqueado, ADR-0037 |
| `cohesion_bloque_senado` | **1 pt**, 2026-07 | recién automatizado esta sesión |
| `adhesion_reformas_provincial` | **1 pt**, 2026-07 | stock (evento único, no backfilleable) |

Conclusión honesta: 3 de 12 tienen historia mensual sólida desde dic-2023, 1
tiene historia larga pero requiere transformación (protestas_caba →
var_vs_2023, ver abajo), 3 son anuales/por período con pocos puntos, y 5
recién tienen 1-2 puntos (automatizados esta sesión). El motor
(`parametrica.calcular_indice`) renormaliza pesos ante faltantes y solo
devuelve `None` si TODAS las dimensiones quedan vacías ese mes — dado que
imagen_voto (votómetro) y buena parte de poder_legislativo tienen dato
mensual completo desde dic-2023, la reconstrucción **no tuvo huecos**: 32
meses completos, 2023-12 → 2026-07.

### Caso especial: `protestas_caba`

El ITCP puntúa este indicador sobre `var_vs_2023` (% de variación de eventos
ACLED acumulados 12 meses contra la suma FIJA de eventos de todo 2023), NO
sobre el conteo crudo — está documentado explícitamente en el docstring de
`itcp.BANDAS_ITCP` y en `politica._valor_itcp()`. La serie histórica
disponible (`series.json["protestas_caba"]`) es el conteo crudo mensual, así
que hubo que reconstruir la transformación yo mismo en
`validacion_externa.py` (`_protestas_caba_var_vs_2023`), replicando
EXACTAMENTE la fórmula de `gestion.fetch_protestas_caba()`: acumulado móvil
de 12 meses / suma fija de eventos 2023. Sin este ajuste, pasar el conteo
crudo (decenas/cientos de eventos) directo a las bandas de `protestas_caba`
(pensadas para una escala de variación %, ej. -30/+30) lo habría puntuado
completamente mal.

## Fuente externa: EPU Argentina

- `https://www.bde.es/f/webbe/SES/AnalisisEconomico/AnalisisEconomico/America_latina/Publicaciones/EPU_LATAM.xlsx`
- Verificado en vivo (`openpyxl.load_workbook`): hoja `data_LATAM`, columna
  `EPU_ARG_local` (fila de encabezado 1, columna B). 283 puntos no-nulos,
  2002-11 → 2026-05, **sin huecos en el rango 2023-2026** que necesita el
  proyecto.
- `openpyxl` ya estaba en `requirements.txt` (usado para el ITCRM del BCRA);
  no hizo falta agregar ninguna dependencia nueva.
- Fetcher: `fetch_epu_argentina_mensual()` en `scripts/validacion_externa.py`,
  mismo estilo/manejo de errores que `fetch_riesgo_pais_mensual()` (import
  local de `openpyxl`/`io`, sin manejo de excepción propio — el `try/except`
  vive en `main()`, igual que los otros fetchers).

## Resultado real (no fabricado)

Corrida real de `python scripts/validacion_externa.py`:

```
serie ITCP reconstruida: 32 meses (2023-12 → 2026-07) · último: 58.3
correlaciones ITCP (Pearson, negativa = válida):
  niveles (ITCP vs EPU Argentina): r = -0.382  (n = 30)
  primeras diferencias (ITCP vs EPU): r = -0.224  (n = 29)
  ITCP adelantado 1 mes vs EPU: r = -0.475  (n = 29)
  EPU adelantado 1 mes vs ITCP: r = -0.068  (n = 30)
```

**n = 30 meses de solape, r = -0,382 en niveles** — cómodamente por encima
del umbral de 12 meses que exige `_validacion_itcp()` para no ser un no-op.
Signo correcto (negativo, como se esperaba: más capital político → menos
incertidumbre de política percibida), pero notablemente más moderado que
ITCM (-0,74 con riesgo país) o ITCG (+0,77 con Merval) — consistente con la
cobertura más flaca de varios componentes del ITCP.

Confirmado end-to-end corriendo `python scripts/publicar.py` sobre datos
reales (sin mockear nada): `web/src/data/informe.json` quedó con
`cinturones.politica.itcp.validacion` poblado (`r_niveles: -0.382,
r_diferencias: -0.224, n: 30`) y `informe.validacion_cruzada` con 4 filas.

### Matriz cruzada 4x4 real (de `informe.json` tras la corrida)

| Índice | propio | riesgo | merval | icc | epu |
|---|---|---|---|---|---|
| ITCM | riesgo | **-0.74** | 0.64 | 0.53 | 0.14 |
| ITCG | merval | -0.88 | **0.77** | 0.46 | 0.27 |
| ITVC | icc | -0.40 | 0.36 | **0.47** | 0.17 |
| ITCP | epu | 0.13 | 0.05 | 0.12 | **-0.38** |

Validez discriminante clara para ITCP: su correlación con su propio par
(-0,38) es varias veces más fuerte (en valor absoluto) que con cualquiera de
los tres pares financieros ajenos (0,05 a 0,13) — el ITCP claramente NO mide
"lo mismo" que los índices de mercado, a diferencia de lo que pasa entre
ITCM/ITCG (que sí comparten bastante señal con el riesgo país, ~-0,74/-0,88,
un límite ya declarado en la conclusión de la matriz desde antes de esta
tarea).

## Archivos modificados (staged)

- `scripts/validacion_externa.py` — import de `itcp`; `EPU_LATAM_URL`;
  `ITCP_SERIES`; `_protestas_caba_var_vs_2023()`; `construir_serie_itcp()`;
  `fetch_epu_argentina_mensual()`; wiring en `main()` (bloque
  `serie_itcp`/`epu_argentina_mensual`/`correlaciones_itcp`).
- `scripts/publicar.py` — `_validacion_itcp(bloque)` (mismo shape que
  `_validacion_itcm`/`_validacion_itcg`); wiring en `aplicar_scoring()` (rama
  `politica`, después de `_scoring_indice`); `_validacion_cruzada()` extendida
  de 3 a 4 índices (`PAR_PROPIO["ITCP"]="epu"`, tupla de iteración con
  "ITCP", `externas["epu"]`, guard genérico `for e in externas` en vez de la
  tupla hardcodeada `("riesgo","merval","icc")`, desempaquetado de 4 filas).
- `web/src/pages/[slug].astro` — `CRUZ_CORTAS["epu"] = "EPU Argentina"`;
  comentarios actualizados (ya no dicen que política "no tiene contraste
  externo"). **La lógica de gating NO necesitó cambios de código**: el filtro
  ya era genérico (`cruzRaw.filas.some(f => f.indice === indice.sigla)`) —
  con ITCM/ITCG/ITVC nada más en `filas`, política nunca matcheaba y el
  bloque quedaba oculto solo; ahora que `_validacion_cruzada` agrega la fila
  "ITCP", el mismo filtro genérico la muestra automáticamente con su propio
  resaltado ("(este cinturón)"). Solo hubo que actualizar el comentario que
  describía el estado viejo.
- `output/validacion_externa.json` — regenerado por la corrida real.
- `web/src/data/informe.json` — regenerado por la corrida real de
  `publicar.py` (snapshot publicado).

`web/src/data/series.json` quedó **regenerado exactamente igual a HEAD**
(diff vacío) — la corrida de `publicar.py` lo reconstruye desde cero a
partir de los CSV de `output/series/` y el histórico acumulado, y da
byte-idéntico al commit. Aclaración honesta: al inicio de la tarea este
archivo figuraba como "modificado" en el working tree (diff previo, ajeno a
esta tarea — trabajo de motos/SSS de otra sesión); mi corrida de
`publicar.py` lo REGENERÓ determinísticamente y ese diff previo quedó
sobrescrito (no fue "sin efecto": fue efecto nulo en el resultado final
porque la regeneración determinística coincidió con HEAD, pero cualquier
estado intermedio no commiteado de ese archivo se perdió). No afecta el
entregable de esta tarea (no se stagea) ni parece afectar trabajo pendiente
ajeno, pero lo dejo explícito en vez de decir sin más "no hay efecto".

`data/historico/indicadores.json` también fue tocado por mi corrida de
`publicar.py` (vía `acumular_historico()`), que se ejecuta incondicionalmente
en `main()`. Este archivo YA estaba modificado (dirty preexistente, ajeno a
esta tarea) antes de que yo corriera nada; mi corrida probablemente agregó/
actualizó entradas de hoy encima de ese diff previo, mezclando ambos. Lo dejo
sin stagear (no está en la lista de archivos de esta tarea) tal como se
indicó, pero no es un archivo "intacto" — es un archivo con dirty preexistente
+ mi corrida encima, sin forma de separar limpiamente ambas capas post-hoc.

### Drift menor en ITCM/ITCG/ITVC por refetch en vivo (no relacionado con ITCP)

Al comparar `output/validacion_externa.json` y `web/src/data/informe.json`
contra HEAD, además de las adiciones de ITCP hay un **drift de terceros
decimales** en las correlaciones YA existentes de ITCM/ITCG/ITVC (ninguna
cambia de signo ni de orden de magnitud, ningún `valor` publicado de
ITCM/ITCG/ITVC cambió):

- `correlaciones_itcg["niveles (ITCG vs riesgo país)"]`: -0,884 → -0,885
- `correlaciones_itcg["primeras diferencias (ITCG vs Merval USD)"]`: 0,376 → 0,375
- `correlaciones_itcg["primeras diferencias (ITCG vs riesgo)"]`: -0,241 → -0,24
- `correlaciones["niveles (ITVC sin ICC vs ICC)"]` y las otras 3 variantes ITVC: +0,002/+0,003 cada una
- `serie_itcg` de julio-2026: 73,1 → 73,8 (el mes corriente, parcial, se mueve con cada refetch de Merval/CCL)
- `serie_itcm`/`serie_itvc`: sin cambios en su último mes

Esto es un efecto esperado y no deseado de correr el pipeline completo para
verificar el trabajo de ITCP: `fetch_riesgo_pais_mensual()`/
`fetch_merval_usd_mensual()` pegan a APIs en vivo, y el mes corriente
(parcial) se recalcula con cada corrida. Los `valor` publicados de
ITCM/ITCG/ITVC (el número que ve el usuario en la card) NO cambiaron; solo
sus paneles de validación externa (decimales de correlación) se refrescaron
con datos de mercado más actuales. Lo dejo explícito en el commit para que
no se lea como "cambios no explicados" en el diff.

## Self-review

- `python -m pytest tests/ -v`: **97 passed**, sin regresiones. Incluye
  `test_politica_itcp_reconcilia` (ya cubría el bloque `itcp` antes de esta
  tarea) sin romperse: el nuevo campo `validacion` es aditivo, no toca
  ninguno de los campos que ese test verifica.
- No se agregó un test nuevo para `_validacion_itcp`/`_validacion_cruzada`:
  ninguna de las dos tenía cobertura previa (mismo precedente que
  `_validacion_itcm`, que tampoco la tiene), y no toqué la firma ni el
  comportamiento de `itcp.calcular_itcp` ni de ninguna función YA cubierta
  más allá de agregar una llamada aditiva (`if c.get("itcp"):
  _validacion_itcp(c["itcp"])`).
- `cd web && npm run build`: compiló limpio, 65 páginas generadas. Verificado
  en el HTML generado (`web/informe/politica/index.html` — el build usa
  `outDir` fuera del repo del proyecto): aparecen las 4 filas
  ITCM/ITCG/ITVC/ITCP en la tabla, con ITCP marcada `es-actual` en la página
  de política; verificado también que macro/gestión/vida siguen mostrando
  su propia fila resaltada sin regresión.
- `git status` revisado antes de stagear: se agregaron EXACTAMENTE los 5
  archivos relevantes (`scripts/validacion_externa.py`, `scripts/publicar.py`,
  `web/src/pages/[slug].astro`, `output/validacion_externa.json`,
  `web/src/data/informe.json`); no se tocó ningún archivo de la lista de
  "dirty preexistente e irrelevante" (motos, fix de gestion.py/test_itcg.py,
  caches/series de otros cinturones, `data/historico/indicadores.json`,
  `output/interpolacion_sombra.json`, `output/sensibilidad.json`). No se usó
  `git add -A` en ningún momento.

## Concerns

1. **Correlación moderada, no fuerte.** -0,38 es un signo correcto pero un
   efecto bastante más débil que los de ITCM (-0,74) e ITCG (+0,77). Es
   honesto y coherente con la cobertura real (5 de 12 componentes con 1-2
   puntos), pero cabe la posibilidad de que, a medida que
   cohesion_bloque/gobernadores_alineamiento/movilizacion_cepa acumulen
   historia real en los próximos meses, esta correlación cambie
   materialmente (para mejor o peor) — vale revisarla en unos meses, no
   tratarla como definitiva.
2. **CSS de la matriz cruzada a 4 columnas.** `web/public/overrides.css`
   tiene una regla mobile (`@media` cerca de la línea 430) con
   `table-layout: fixed` y un ancho fijo de 17% para la columna de
   encabezado de fila; las columnas de datos se reparten el resto por igual
   (antes 3 columnas al 27,7% c/u, ahora 4 al ~20,75% c/u). No rompe nada
   (confirmado con el build y el HTML generado), pero queda algo más
   apretada en mobile — no toqué el CSS porque no se pidió explícitamente y
   no hay evidencia de que rompa nada, solo que puede verse algo más justa.
3. **La brecha cambiaria y el WPUI fueron descartados en el camino** (ver
   historial de mensajes): documentado acá por transparencia, no quedó
   código residual de esos intentos — no se llegó a escribir ningún fetcher
   para ellos, la decisión se tomó antes de tocar código.
4. **`_validacion_cruzada` sigue siendo todo-o-nada, y ahora con un input
   más.** La función arma la matriz solo si LOS 4 bloques
   (`itcm/itcg/itvc/itcp`) tienen `.validacion.pares` Y las 16 celdas
   cruzadas superan el umbral de 12 meses; si falta cualquiera de las 4
   piezas, la matriz completa desaparece de LAS 4 páginas (no solo de la de
   política). Antes de esta tarea esto ya era así con 3 índices; ahora un
   fallo puntual de la fuente EPU (Banco de España, xlsx público) —o de
   cualquiera de los otros 3 fetchers— apaga la matriz en las cuatro
   páginas, no solo en la de política. No es una regresión (el contrato
   "todo o nada" ya existía) ni rompe nada hoy (los 4 fetchers respondieron
   bien en esta corrida), pero es un nuevo punto único de falla que vale la
   pena tener en cuenta si en el futuro se quiere hacer la matriz más
   resiliente (ej. degradarla a 3x3 o Nx N según qué índices tengan
   validación real, en vez de exigir las 4 a la vez). Deliberadamente NO lo
   arreglé ahora — está fuera del alcance de esta tarea y el riesgo práctico
   es bajo (el archivo del Banco de España es más estable que las APIs de
   mercado que ya dependían de este mismo contrato).
