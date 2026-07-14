# ITCM — Brief para stress test

> Para: **Heber** y **Diego** (macroeconomistas)
> De: equipo Informe de Coyuntura — CIGOB
> Fecha: 2026-07-14 · Sitio en vivo: **informe.cigob.org** (pestaña Macro)
>
> El objetivo de este documento es que puedan **estresar el criterio económico** del
> índice. La factibilidad de datos y la metodología operativa están definidas. Lo que
> necesitamos de ustedes es opinión sobre **qué entra, con qué peso y con qué umbrales**.
> Donde tomamos una decisión de juicio, está marcada como tal.

---

## 1. Qué es y cómo se lee

El **ITCM (Índice de Tensión del Cinturón Macroeconómico)** resume el frente macro en
una escala **0–100**, donde **mayor = menos tensión** (cinturón “aflojado”) y menor =
más tensión (“apretado”). La tensión 0–10 que se compara con los otros cinturones del
informe se deriva como **tensión = (100 − ITCM) / 10**.

El ITCM es un **promedio ponderado por dimensiones**. Dentro de cada dimensión, los
indicadores se traducen a puntajes 0–100 mediante anclas e interpolación lineal. Las
seis dimensiones conservan los pesos **26/24/16/11/11/12**.

La foto regenerada al 14 de julio de 2026 ubica al ITCM en **59,0 puntos** —tensión
**4,1**, banda **moderadamente apretado**—. Las cifras coyunturales y de robustez que
siguen pertenecen íntegramente a la nueva formulación sensible al régimen.

---

## 2. Composición vigente

| Dimensión | Peso | Indicadores |
|---|---:|---|
| **Estabilidad monetaria** | 26% | IPC mensual, REM, IDM, presión de dolarización de carteras |
| **Viabilidad fiscal-comercial** | 24% | Recaudación i.a. real —media móvil 3m—, saldo comercial 12m |
| **Capacidad de financiamiento** | 16% | Reservas netas, IdC, crédito privado i.a. real |
| **Actividad económica** | 11% | EMAE i.a. |
| **Competitividad externa** | 11% | TCRM (ITCRM) |
| **Inversión** | 12% | IAI físico, ICIP digital |

Estabilidad monetaria mantiene la distribución interna **40/25/25/10**. La presión de
dolarización pesa 10% dentro de la dimensión, equivalente a **2,6% nominal del ITCM**.
Si faltan componentes, el motor renormaliza y el peso efectivo puede diferir.

### La señal de dolarización fue rediseñada

La variable de interés no es un stock particular, sino un constructo latente: la
**presión de los hogares por reducir su exposición al peso**. El observable cambia con
el régimen cambiario.

#### Régimen restringido — hasta marzo de 2025

Se calcula la brecha mensual entre el promedio del CCL y el promedio del A3500, y luego
se toma un promedio de **tres meses calendario estrictamente contiguos**. Si falta uno,
el período se omite.

| Brecha CCL/A3500, promedio móvil 3m | Presión 0–100 |
|---:|---:|
| 5% | 0 |
| 15% | 25 |
| 30% | 50 |
| 50% | 75 |
| 70% | 100 |

#### Régimen abierto — desde abril de 2025

Se usan las compras netas de moneda extranjera de Personas Humanas, sin fines
específicos, informadas por el Mercado de Cambios del BCRA. El flujo se divide por el
M2 transaccional privado convertido a dólares al A3500.

La transición utiliza una ventana de un mes en abril, dos en mayo y tres meses
contiguos desde junio de 2025. La fórmula suma primero los numeradores y los
denominadores de la ventana:

```text
100 × suma(compras netas USD) / suma(M2 privado ARS / A3500)
```

No se promedian cocientes mensuales.

| Compras netas / M2 privado en USD | Presión 0–100 |
|---:|---:|
| 0% | 0 |
| 3% | 25 |
| 6% | 50 |
| 10% | 75 |
| 15% | 100 |

#### Conversión común al ITCM

Ambos observables se traducen primero a presión y luego a un puntaje común:

| Presión | Puntaje ITCM |
|---:|---:|
| 0 | 100 |
| 25 | 85 |
| 50 | 60 |
| 75 | 35 |
| 100 | 10 |

La doble escala es deliberada: evita presentar una brecha de precios y una razón de
flujos como si tuvieran la misma unidad, pero permite que ambas aproximen el mismo
constructo económico.

### Por qué se descartó la fórmula de depósitos

La brecha entre el crecimiento interanual de depósitos privados en dólares y el
crecimiento real de los depósitos en pesos quedó afectada por el ingreso extraordinario
a las CERA. El episodio aparece tanto de forma contemporánea como a través de efectos
de base cuando el nivel extraordinario entra en la comparación interanual.

Una ventana semestral tampoco resuelve el problema: acorta el período, pero sigue
comparando stocks atravesados por el mismo quiebre regulatorio. Además, ninguna de las
dos variantes responde bien al cambio de régimen de abril de 2025: con restricciones,
la presión se expresa en la brecha; con apertura, puede expresarse en compras efectivas
sin ampliar esa brecha.

---

## 3. Decisiones de criterio que pedimos estresar

Todo lo siguiente es **juicio metodológico**, no una verdad natural. Cada indicador
admite ajustes documentados, de modo que una propuesta alternativa puede incorporarse
sin romper la trazabilidad.

1. **Pesos de las dimensiones.** La paramétrica original de CIGOB definía cuatro
   dimensiones (35/30/20/15). Se agregaron **competitividad externa** e **inversión** y
   se recortaron las demás en proporción hasta **26/24/16/11/11/12**. ¿Les resulta
   adecuado ese reparto?

2. **Peso de la presión de dolarización.** El indicador pesa 10% dentro de estabilidad
   monetaria y 2,6% nominal del ITCM. ¿Es suficiente para representar una salida
   persistente del peso sin sobrerreaccionar a episodios puntuales?

3. **Anclas por régimen.** Pedimos revisar especialmente:
   - brecha CCL/A3500 de **5/15/30/50/70%** para presión **0/25/50/75/100**;
   - compras netas sobre M2 de **0/3/6/10/15%** para la misma escala de presión;
   - conversión de presión **0/25/50/75/100** a puntaje ITCM
     **100/85/60/35/10**.

4. **Ventana temporal.** En ambos regímenes se privilegia una ventana de tres meses
   contiguos. En el régimen abierto, abril y mayo de 2025 usan uno y dos meses para no
   inventar historia previa al nuevo marco. ¿La suavización es adecuada o debería ser
   más larga?

5. **Denominador del régimen abierto.** M2 privado en USD dimensiona las compras por la
   liquidez transaccional disponible. No representa riqueza financiera total y depende
   del A3500 usado para la conversión. ¿Preferirían otro denominador reproducible?

6. **Solapamiento con `cepo_mulc`.** En el tramo restringido, ambos indicadores usan la
   familia CCL/A3500. `cepo_mulc` mide la restricción contemporánea en gestión; la
   presión de dolarización usa un promedio de tres meses en macro. Desde abril de 2025,
   esta última cambia a compras efectivas. ¿La diferencia de constructo justifica
   conservar ambos o consideran excesivo el solapamiento histórico?

7. **Otros umbrales relevantes.** También quedan abiertos al stress test:
   - **TCRM**: percentiles históricos del ITCRM para distinguir competitividad, zona
     cómoda, apreciación y atraso;
   - **IAI / ICIP**: bandas amplias porque las series interanuales de inversión presentan
     variaciones muy superiores al ±2% de la propuesta original;
   - **reservas netas**: escala propia de disponibilidad externa.

8. **Agregación.** El ITCM usa promedio ponderado. ¿Alguna dimensión —por ejemplo,
   reservas— debería actuar como umbral duro cuando alcanza una zona crítica?

---

## 4. Fuentes, faltantes y límites

### Fuentes de la presión de dolarización

- ArgentinaDatos: CCL diario.
- BCRA: A3500, variable monetaria 5.
- BCRA: M2 transaccional privado, variable monetaria 197.
- BCRA: anexo del Mercado de Cambios, Personas Humanas, compra-venta de billetes y
  divisas sin fines específicos.

La serie se reconstruye desde diciembre de 2023. Octubre y noviembre de 2023 se usan
sólo como insumos para completar la primera ventana trimestral. En esa primera
observación, la brecha mensual de diciembre fue **50,12%**, pero el observable vigente
es el promedio octubre-diciembre, **118,56%**, que satura la presión en 100. El valor
75,15 de un prototipo previo provenía de aplicar las anclas sólo al mes de diciembre y
no integra la serie definitiva.

### Tratamiento de faltantes

No se imputan ceros, no se interpolan meses ni se unen períodos no contiguos. Si falta
un insumo de la ventana requerida, ese mes no se calcula. Si falla la actualización,
el colector macro conserva el último valor válido del cache y lo identifica como
desactualizado; sin cache, el motor omite el indicador y renormaliza.

### Límites sustantivos

- La continuidad entre regímenes es metodológica, no una identidad estadística.
- Las compras de Personas Humanas no cubren dolarización corporativa, transferencias de
  activos ni todas las coberturas con derivados.
- La referencia del BCRA que combina “efectivo más cobertura” es conceptualmente útil,
  pero no ofrece una serie pública mensual, estructurada y con perímetro estable
  que pueda reproducirse operativamente. Se usa como referencia cualitativa, no como
  insumo del ITCM.
- El CCL de ArgentinaDatos es una fuente pública reproducible, pero no el organismo
  oficial del mercado cambiario.
- Las anclas son decisiones de calibración y no estimaciones causales.

### Otros componentes con datos parciales

- **IAI** corre con ISAC y bienes de capital importados mientras se acumula la serie de
  patentamientos comerciales de DNRPA.
- **ICIP** corre con servicios tecnológicos y productividad; el hardware de alta
  tecnología por posición NCM no está disponible como serie operativa con el detalle y
  la actualidad requeridos.

---

## 5. Resultados regenerados y robustez

La observación disponible más reciente del indicador corresponde a mayo de 2026:

- compras netas de USD de Personas Humanas: **5,43% del M2 privado** en la ventana
  móvil de tres meses;
- presión resultante: **45,24 puntos**;
- puntaje aplicado dentro de estabilidad monetaria: **64,8 puntos**;
- peso efectivo nominal: **2,6% del ITCM**, con un aporte ponderado de **1,7 puntos**;
- puntaje de la dimensión estabilidad monetaria: **68,9 puntos**.

La serie tiene **30 observaciones mensuales**, desde diciembre de 2023 hasta mayo de
2026. La batería de sensibilidad y validación fue recalculada, sin trasladar resultados
de la fórmula descartada de stocks:

- Monte Carlo embebido, 1.000 simulaciones: ITCM p05–p95 **57,2–60,4**, equivalente a
  tensión **4,0–4,3**;
- Monte Carlo independiente, 2.000 simulaciones combinando pesos e insumos: ITCM
  p05–p95 **57,3–60,4**;
- leave-one-out: sin presión de dolarización, el ITCM pasa de **59,0 a 59,1**; el
  indicador no domina el resultado agregado;
- validación con riesgo país: correlación **−0,749 en niveles** (n=30) y **−0,01 en
  primeras diferencias** (n=29). En ventanas de seis meses la relación es **−0,64**;
- el mercado se mueve antes que las fuentes mensuales del índice: el salto del riesgo
  de un mes correlaciona **−0,43** con el salto del ITCM del mes siguiente.

La lectura es que el ITCM y el riesgo país comparten una trayectoria de fondo, pero no
los sobresaltos mensuales. Queda abierto al stress test externo si el solapamiento
histórico con `cepo_mulc`, limitado al régimen restringido, justifica mantener ambas
señales.

---

## 6. Material de referencia y pedido de revisión

- **Sitio en vivo**: informe.cigob.org → Macro.
- **Decisiones de diseño**: `docs/adr/`, en particular ADR-0053 (IDM y transparencia
  de ponderaciones) y ADR-0055 (presión de dolarización de carteras, que supersede
  ADR-0054).
- **Pendientes y fuentes bloqueadas**: `docs/pendientes-datos.md`.
- **Metodología base del ITCM —diseño original archivado—**:
  `docs/archivo/cinturon_macro.md`. La versión vigente surge del motor y los ADRs.

Idealmente, sobre cada punto del §3: **¿lo dejarían igual, lo ajustarían —con qué
número— o lo sacarían?** La meta es que el ITCM resista una revisión macroeconómica
externa antes de considerar definitiva la calibración.
