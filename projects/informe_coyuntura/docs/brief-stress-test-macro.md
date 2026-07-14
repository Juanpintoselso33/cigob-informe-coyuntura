# ITCM — Brief para stress test

> Para: **Heber** y **Diego** (macroeconomistas)
> De: equipo Informe de Coyuntura — CIGOB
> Fecha: 2026-07-14 · Sitio en vivo: **informe.cigob.org** (pestaña Macro)
>
> El objetivo de este documento es que puedan **estresar el criterio económico** del
> índice. La factibilidad de datos (todo sale de fuente oficial, sin valores cargados
> a mano) y la implementación ya están resueltas y testeadas. Lo que necesitamos de
> ustedes es opinión sobre **qué entra, con qué peso y con qué umbrales**. Donde
> tomamos una decisión de juicio, está marcada como tal.

---

## 1. Qué es y cómo se lee

El **ITCM (Índice de Tensión del Cinturón Macroeconómico)** resume el frente macro en
una escala **0–100**, donde **mayor = menos tensión** (cinturón "aflojado") y menor =
más tensión ("apretado"). La tensión 0–10 que se compara con los otros cinturones del
informe se deriva como **tensión = (100 − ITCM) / 10**.

El ITCM es un **promedio ponderado por dimensiones**; dentro de cada dimensión, cada
indicador se traduce a un puntaje 0–100 por **bandas** (tablas de umbrales) y se
promedia. Convención de bordes: límite inferior exclusivo, superior inclusivo.

**Hoy: ITCM 57,5 — "Moderadamente apretado" — tensión 4,2 / 10.**

---

## 2. Foto actual (últimos datos disponibles al 14-jul-2026)

| Dimensión | Peso | Indicador | Valor | Puntaje | Dim. |
|---|---|---|---|---|---|
| **Estabilidad monetaria** | 26% | IPC mensual | 2,15% | 72,0 | **63,4** |
| | | REM (expectativas) | 22,3% anual | 81,2 | |
| | | IDM (desequilibrio monetario) | +4,3 pp | 53,3 | |
| | | Dolarización de depósitos | +29,07 pp | 10,0 | |
| **Viabilidad fiscal-comercial** | 24% | Recaudación i.a. real (media móvil 3m) | −2,3% | 40,8 | **58,5** |
| | | Saldo comercial 12m | +21.221 M USD | 85,0 | |
| **Capacidad de financiamiento** | 16% | Reservas netas | +4.122 M USD | 36,5 | **44,7** |
| | | IdC (capacidad prestable) | −0,31 σ | 49,7 | |
| | | Crédito privado i.a. real | +9,5% | 56,0 | |
| **Actividad económica** | 11% | EMAE i.a. | +1,64% | 61,1 | **61,1** |
| **Competitividad externa** | 11% | TCRM (ITCRM) | 85,04 | 47,6 | **47,6** |
| **Inversión** | 12% | IAI (físico) | +0,31% i.a. | 61,0 | **65,9** |
| | | ICIP (digital) | +8,3% i.a. | 73,3 | |

Lectura: el saldo comercial y las expectativas de inflación sostienen el índice. La
principal tensión de estabilidad monetaria es la **dolarización de depósitos**: los
depósitos privados en dólares crecieron 27,76% i.a., mientras los depósitos reales en
pesos cayeron 1,31% i.a.; la brecha resultante es 29,07 puntos porcentuales. También
presionan la recaudación real, las reservas netas y la competitividad cambiaria. La
actividad y la inversión muestran una situación intermedia, sin la fortaleza que tenían
en la foto de junio.

### Robustez y contraste externo

- Monte Carlo embebido (1.000 simulaciones): **ITCM 57,5**, intervalo p05-p95
  **55,9–59,0**; tensión compatible **4,1–4,4**.
- Monte Carlo ampliado (2.000 simulaciones): al excluir sólo la dolarización de
  depósitos, el ITCM contrafactual es **59,1** (**+1,6 puntos**).
- Reconstrucción histórica: 30 meses (dic-2023 a may-2026). Correlación en niveles
  con riesgo país: **−0,741**; en primeras diferencias: **0,060**. La evidencia
  respalda una asociación de mediano plazo, no una capacidad de anticipación mensual.

---

## 3. Decisiones de criterio (lo que pedimos que estresen)

Todo lo siguiente es **juicio nuestro**, no una verdad revelada. Es pisable —cada
indicador admite un override del analista con justificación y vencimiento— así que si
proponen otros números, los incorporamos sin tocar código.

1. **Pesos de las dimensiones.** La paramétrica original de CIGOB definía 4 dimensiones
   (35/30/20/15). Nosotros agregamos dos —**competitividad externa** e **inversión**— y
   recortamos las demás en proporción → **26/24/16/11/11/12**. ¿Les cierra ese reparto?
   ¿Inversión y competitividad deberían pesar más/menos?

2. **Umbrales de las bandas.** Algunas son nuestras:
   - **Dolarización de depósitos**: ≤−25 pp → 100; −25 a 0 → 85; 0 a 10 → 60;
     10 a 20 → 35; >20 → 10, con interpolación entre anclas. Se calibró con
     2018–2023; el ingreso extraordinario de dólares del CERA se conserva en la serie
     como quiebre regulatorio, pero no se usa para recalibrar. ¿La brecha actual debe
     tratarse como tensión monetaria con esta severidad?
   - **TCRM**: calibrado por percentiles históricos del ITCRM (1997-2026): >110 competitivo,
     95-110 cómodo, 85-95 apreciación moderada, 75-85 marcada, ≤75 atraso severo. ¿Es 75-85
     la zona de "tensión" correcta para el régimen actual?
   - **IAI / ICIP**: el umbral ±2% de la propuesta original **no sobrevive al dato** (las
     series i.a. de inversión se mueven ±30-180% por la base 2024-25), así que usamos bandas
     anchas. ¿Les parece razonable o prefieren suavizar los componentes (media móvil) o
     medirlos relativos al EMAE?
   - **Reservas netas**: escala propia (>20k→100 … neg→10). 

3. **Desvíos respecto de los documentos fuente** (justificados en los ADRs):
   - **IDM** se implementa **real-real interanual** (ΔM3 privado real − ΔM2
     transaccional privado real), no el nominal-real mensual del documento, que daba
     rojo permanente por sesgo inflacionario.
   - Los depósitos en dólares no se mezclan dentro de un M3 ampliado: se publican como
     **indicador independiente**, comparando su crecimiento en USD con el crecimiento
     real de los depósitos en pesos. Así se evita introducir valuación cambiaria dentro
     del IDM y se mantiene visible la preferencia por moneda.
   - **Recaudación** en variación **i.a. real**, no m/m nominal.
   - **Reservas** netas "a secas" (SDDS estricto + Tesoro + Bopreal 12m), el número del mercado.
   - **REM** puntuado por su equivalente mensual (raíz-12), comparable al IPC.

4. **Solapamientos a discutir.** El IPC, el IDM y la dolarización conviven en
   estabilidad monetaria, pero miden mecanismos distintos: precios corrientes, holgura
   de pesos y preferencia relativa por moneda. El `servicios_tech` del ICIP es una
   importación (egreso de divisas) que roza el frente externo. ¿Los ven como
   doble-conteo o como señales complementarias? ¿Es adecuado que la dolarización pese
   10% dentro de la dimensión —2,6% del ITCM—?

5. **Agregación.** Hoy es **promedio ponderado** de puntajes de banda. ¿Tiene sentido, o
   alguna dimensión (p. ej. reservas) debería actuar como **umbral duro** que domine cuando
   está en rojo?

---

## 4. Qué quedó con datos parciales (y por qué)

Por transparencia: dos componentes corren incompletos porque la fuente oficial no los
publica como serie automatizable (investigado a fondo, detalle en `docs/pendientes-datos.md`):

- **IAI** corre con 2 de 3 componentes (ISAC construcción + bienes de capital importados,
  65/35). El tercero —**patentamientos comerciales**— se está **acumulando** mes a mes desde
  la DNRPA (que no expone histórico) y se sumará solo hacia mediados de 2027.
- **ICIP** corre con 2 componentes (servicios tech + productividad). El **hardware hi-tech**
  por posición NCM no existe como serie (el NCM oficial es a 2 dígitos y está 16 meses viejo).

---

## 5. Material de referencia

- **Sitio en vivo**: informe.cigob.org → Macro (cada indicador tiene ficha con qué mide,
  fuente, cómo incide en el score, y evolución histórica descargable).
- **Decisiones de diseño**: `docs/adr/` — en particular ADR-0053 (IDM y
  transparencia de ponderaciones) y ADR-0054 (dolarización de depósitos), con contexto,
  alternativas descartadas y consecuencias.
- **Pendientes y fuentes bloqueadas**: `docs/pendientes-datos.md`.
- **Metodología base del ITCM (diseño original, archivado)**: `docs/archivo/cinturon_macro.md`. Versión vigente: `scripts/itcm.py`.

---

## 6. Cómo nos ayuda su revisión

Idealmente, sobre cada punto del §3: **¿lo dejarían igual, lo ajustarían (con qué número),
o lo sacarían?** Cualquier ajuste de pesos o umbrales lo aplicamos vía override —con su
nombre y fundamento— sin reescribir el índice. La idea es que el ITCM resista la mirada de
quien sabe de macro antes de darlo por definitivo.
