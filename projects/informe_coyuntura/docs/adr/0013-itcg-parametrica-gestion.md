# ADR-0013 — ITCG: el cinturón de gestión se puntúa con la paramétrica de 5 dimensiones (doc 260702)

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-02 |
| **Ámbito** | `scripts/itcg.py` · `scripts/gestion.py` · `scripts/parametrica.py` · `scripts/publicar.py` · `scripts/descargar_series.py` · `data/gestion/*` · web |

## Contexto

El cinturón de gestión se puntuaba con un **promedio simple** de las tensiones de
12 indicadores heterogéneos (6 auto, 6 manuales), sin ponderación entre reformas
ni bandas explícitas. El documento CIGOB **"260702 AJUSTE PARAMETRICA GESTIÓN"**
define una fórmula paramétrica análoga al ITCM de macro: **cinco dimensiones**
con pesos 35/25/15/15/10 (reformas económicas, reforma del Estado, reforma
laboral, privatizaciones e inversión, reforma social y orden).

## Decisión

Implementar el **ITCG** (0-100, mayor = agenda ejecutándose; tensión =
(100−ITCG)/10) con el mismo motor que el ITCM — extraído a
`scripts/parametrica.py` (bandas low-exclusivo/high-inclusivo, renormalización
ante faltantes, overrides con vencimiento en `data/gestion/ajustes_itcg.json`).
Las claves históricas de los indicadores se **conservan** (cepo_mulc,
reduccion_estado, …) para no romper las series acumuladas.

### Operacionalizaciones donde el doc es ambiguo o la fuente no existe

Todas las fuentes citadas fueron **verificadas con llamadas HTTP reales**
(2026-07-02) antes de decidir qué es AUTO y qué manual.

1. **Pesos internos de D2-D5**: el doc solo fija los internos de D1 (40/40/20).
   Se definen: D2 dotación 35 / gasto funcionamiento 25 / masa salarial 20 /
   organismos 20 · D4 privatizaciones 40 / RIGI 40 / concesiones 20 ·
   D5 asistencia 40 / piquetes 40 / salud 20 (el doc describe D5 como
   "desintermediación, liberalización salud y orden público").
2. **El ejemplo de D1 del doc no se pinea**: "(0,40×20 + 0,40×95 + 0,20×85) =
   63/100" es ilustrativo y sus insumos no cierran con el propio texto (la
   brecha de 4,91% se describe como "promesa cumplida" pero puntuaría 20 o 95
   según el orden). Los puntajes salen siempre de las bandas sobre datos reales.
3. **ILCE (apertura comercial)** — reemplaza el proxy viejo (importaciones
   i.a., que premiaba cualquier suba de importaciones):
   - `B_camb` = brecha inversa 100/(1+brecha), con la brecha CCL/mayorista
     (ADR-0006).
   - `A_efec` = alícuota efectiva: recaudación de derechos de importación +
     exportación (series `142.3_DEREC_2001_M_20/26`, ARS → USD por el A3500
     promedio mensual del BCRA) sobre el intercambio total ICA
     (`74.3_IET_0_M_16` + `74.3_IIT_0_M_25`). Normalización lineal propia:
     0% → 100 puntos, ≥15% → 0 (cierre de hecho); el doc no define la escala.
     Dato jul-2026: alícuota ≈ 4,9% → A_efec ≈ 68.
   - `T_adu` (canal verde aduanero, 20% del doc): **NO EXISTE fuente pública**
     — verificado: CKAN datos.gob.ar (`selectividad`/`destinaciones` → 0
     resultados) y ARCA solo publica PDFs de recaudación. Se renormaliza entre
     los dos componentes disponibles.
4. **Reforma del Estado — fuentes nuevas**:
   - Dotación: XLSX mensual oficial del INDEC (`serie_dotacion_apn.xlsx`,
     jul-2022→may-2026; APN dic-23 231.305 → may-26 185.498 = **−19,8%**).
     Reemplaza la serie trimestral de sector público TOTAL (incluía provincias
     y subestimaba la reforma: −0,8%). El WAF de indec.gob.ar resetea el TLS de
     Python → fallback a curl. El dataset de nómina de JGM (datos.gob.ar) está
     roto (HTTP 500) y el de puestos congelado en 2020.
   - Gasto de funcionamiento y masa salarial: series mensuales IMIG/AIF
     (`452.2_SALARIOSIOS…`+`452.2_OTROS_GASTNTO…` y `379.9_GTOS_CORR_017__49_26`),
     en **variación real vs el mismo mes de 2023** (deflactada por IPC;
     comparar el mismo mes evita el sesgo del aguinaldo). Sustituye el "% del
     PBI" del doc: persigue el mismo objetivo (aislar inflación/licuación) sin
     depender del PIB trimestral rezagado.
   - Organismos: se mantiene el proxy InfoLeg "disolucion" (18 actos = 40%,
     45 = plan completo). El Mapa del Estado tiene un CSV vivo
     (mapadelestado.dyte.gob.ar) pero es foto sin baseline dic-2023 —
     candidato a serie propia hacia adelante.
5. **Fondo de Cese (D3, conserva la clave `fal_modernizacion_laboral`)**:
   índice compuesto del doc (cobertura CCT 40 + adopción financiera 30 +
   litigiosidad 30) **renormalizado a lo disponible**:
   - Adopción financiera AUTO: FCI con "Cese Laboral" en el registro CNV
     (POST `GetFCIPorTipo`, sin auth; la RG 1071/2025 art. 2 hace obligatoria
     la denominación → substring sin falsos negativos). **Hoy: 0 de 1.656
     fondos** — el cero es un dato duro, no un faltante. Escala provisional:
     10 fondos = adopción plena (pasar a patrimonio cuando CAFCI sea accesible;
     su API pública hace fingerprinting TLS y la serie de patrimonio de
     datos.gob.ar murió en jul-2024).
   - Cobertura CCT manual (`cobertura_cct_pct` en manuales.json): el buscador
     de convenios del MTEySS es GeneXus/ASP sin API, y el boletín de
     negociación colectiva aún no clasifica la cláusula de cese.
   - Litigiosidad diferencial (diff-in-diff del doc): sin consolidado nacional
     de causas por sector. La serie SRT de juicios (XLSX de URL fija, mensual
     2010→mar-2026) se publica como **contexto** (`litigiosidad_laboral`,
     fuera del índice): mide riesgos del trabajo, no el canal indemnizatorio.
   - Resultado hoy: índice 2,9 → banda 10. D3 = 10/100: marco normativo
     completo con **cero materialización** — la lectura del doc, cuantificada.
6. **Privatizaciones por etapas**: store curado
   `data/gestion/privatizaciones.json` (9 empresas Ley Bases, etapa 0-4 por
   empresa, sembrado con la tabla jun-2026 del doc; promedio 2,06/4 = 51,4%).
   No hay fuente única automatizable (la Agencia de Transformación no publica
   dashboard; la Bicameral tampoco): se mantiene con el BO. Reemplaza el
   estimado plano de 15% "empresas transferidas".
7. **TDPS (asistencia directa)**: manual = 100 (el Dto. 198/2024 eliminó las
   Unidades de Gestión; cambio normativo fechado y total). Verificación
   presupuestaria automatizable pendiente: API Presupuesto Abierto requiere
   token (alta automática por mail) o los ZIPs sin token de
   `dgsiaf-repo.mecon.gob.ar`. La advertencia del doc queda en la ficha:
   desintermediar ≠ recortar.
8. **Piquetes (protocolo_antipiquetes)**: manual = 55% de reducción vs 2023
   (CABA, Diagnóstico Político vía doc). La API Transporte GCBA existe pero
   requiere registro con captcha (una vez); con credenciales, probar
   `/transito/v1/eventos?month=YYYY-MM&provider=1` (histórico mensual con
   duración) — si está vivo, el indicador pasa a AUTO con baseline dic-2023.
   **El estado legal del protocolo (anulado 29-dic-2025, en apelación) se
   maneja como override del analista** en ajustes_itcg.json, no como banda.
9. **RIGI**: sin cambios de fuente (ADR-0011); se verificó que NO existe dato
   estructurado de inversión ejecutada/desembolsada (el sheet oficial solo trae
   comprometida). `valor` pasa de string a numérico (% del pipeline) para
   bandearse; el detalle rico queda en `detalle_txt`. El parser de la pestaña
   `evaluacion` se hizo robusto al cambio de formato de jul-2026.

## Opciones descartadas

- **IED neta / inversión pública como indicadores del ISPPI (D4)**: las series
  existen y están verificadas (`160.2_CFIN_PASINTAL_0_T_57`,
  `372.9_GTOS_CAP_I017__36_13`), pero la fórmula ISPPI completa del doc exige
  la tasa de desembolso RIGI, que no es pública. Se pospone a una tanda futura
  (los IDs quedan documentados acá).
- **Heritage ILE como indicador de desregulación**: es anual y de fuente
  privada extranjera; queda como referencia de contraste, no puntúa.
- **Contar el ejemplo del doc como calibración**: descartado (punto 2).

## Consecuencias

- Gestión pasa de score 5,9 (promedio simple, con proxies desactualizados) a
  **ITCG 68,5 → tensión 3,1**, con lectura por dimensión: económicas 85 y
  Estado 84 (ejecutándose), social/orden 87, privatizaciones 50 (a mitad de
  camino), **laboral 10 (promesa sin ejecución — el cuello de botella)**.
- Indicadores automáticos: 6 → **11** (de 15); los 4 manuales quedan
  documentados con su camino de automatización en `manuales.json`.
- `parametrica.py` es ahora el motor común de ITCM e ITCG: una sola
  implementación de bandas/renormalización/overrides (pineada por
  tests/test_itcm.py y tests/test_itcg.py).
- El informe muestra dos índices paramétricos; la web los renderiza genérico
  (`indiceDe()` en datos.ts).
- **Riesgos**: el XLSX del INDEC imputa meses "(i)" y los revisa hacia atrás
  (se recalcula toda la serie en cada corrida); la escala de la alícuota
  efectiva (15% = cierre) y la de adopción financiera (10 fondos = plena) son
  anclas propias provisionales — revisar cuando haya más historia.
