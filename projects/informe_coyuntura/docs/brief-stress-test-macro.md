# ITCM — Brief para stress test

> Para: **Heber** y **Diego** (macroeconomistas)
> De: equipo Informe de Coyuntura — CIGOB
> Fecha: 2026-06-30 · Sitio en vivo: **informe.cigob.org** (pestaña Macro)
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

**Hoy: ITCM 63,3 — "Moderadamente aflojado" — tensión 3,7 / 10.**

---

## 2. Foto actual (junio 2026)

| Dimensión | Peso | Indicador | Valor | Puntaje | Dim. |
|---|---|---|---|---|---|
| **Estabilidad monetaria** | 26% | IPC mensual | 2,15% | 65 | **69,5** |
| | | REM (expectativas) | 23,3% anual | 85 | |
| | | IDM (desequilibrio monetario) | +4,5 pp | 60 | |
| **Viabilidad fiscal-comercial** | 24% | Recaudación i.a. real | +1,8% | 60 | **70,0** |
| | | Saldo comercial 12m | +21.221 M USD | 85 | |
| **Capacidad de financiamiento** | 16% | Reservas netas | +4.122 M USD | 30 | **45,0** |
| | | IdC (capacidad prestable) | 1,012 | 60 | |
| **Actividad económica** | 11% | EMAE i.a. | +5,5% | 100 | **100,0** |
| **Competitividad externa** | 11% | TCRM (ITCRM) | 84,3 | 35 | **35,0** |
| **Inversión** | 12% | IAI (físico) | −4,2% i.a. | 35 | **53,0** |
| | | ICIP (digital) | +8,2% i.a. | 80 | |

Lectura: el índice está sostenido por **actividad** (EMAE rebotando) y un **saldo
comercial** holgado, y traccionado a la baja por **reservas netas** todavía flacas, la
**apreciación real** del peso y la **inversión física** en contracción. La inversión
**digital**, en cambio, crece — la divergencia física-vs-digital queda a la vista.

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
   - **TCRM**: calibrado por percentiles históricos del ITCRM (1997-2026): >110 competitivo,
     95-110 cómodo, 85-95 apreciación moderada, 75-85 marcada, ≤75 atraso severo. ¿Es 75-85
     la zona de "tensión" correcta para el régimen actual?
   - **IAI / ICIP**: el umbral ±2% de la propuesta original **no sobrevive al dato** (las
     series i.a. de inversión se mueven ±30-180% por la base 2024-25), así que usamos bandas
     anchas. ¿Les parece razonable o prefieren suavizar los componentes (media móvil) o
     medirlos relativos al EMAE?
   - **Reservas netas**: escala propia (>20k→100 … neg→10). 

3. **Desvíos respecto de los documentos fuente** (justificados en los ADRs):
   - **IDM** se implementa **real-real interanual** (ΔM3 priv. real − ΔM2 priv. real), no el
     nominal-real mensual del doc, que daba rojo permanente por sesgo inflacionario.
   - **Recaudación** en variación **i.a. real**, no m/m nominal.
   - **Reservas** netas "a secas" (SDDS estricto + Tesoro + Bopreal 12m), el número del mercado.
   - **REM** puntuado por su equivalente mensual (raíz-12), comparable al IPC.

4. **Solapamientos a discutir.** El IPC está en estabilidad monetaria y el IDM también es
   monetario (aunque el IDM es real-real, no re-mide inflación). El `servicios_tech` del ICIP
   es una importación (egreso de divisas) que roza el frente externo. ¿Los ven como
   doble-conteo o como dimensiones legítimamente distintas?

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
- **Decisiones de diseño**: `docs/adr/` (ADR-0001 a 0010) — una por decisión, con contexto,
  alternativas descartadas y consecuencias.
- **Pendientes y fuentes bloqueadas**: `docs/pendientes-datos.md`.
- **Metodología base del ITCM**: `docs/cinturon_macro.md`.

---

## 6. Cómo nos ayuda su revisión

Idealmente, sobre cada punto del §3: **¿lo dejarían igual, lo ajustarían (con qué número),
o lo sacarían?** Cualquier ajuste de pesos o umbrales lo aplicamos vía override —con su
nombre y fundamento— sin reescribir el índice. La idea es que el ITCM resista la mirada de
quien sabe de macro antes de darlo por definitivo.
