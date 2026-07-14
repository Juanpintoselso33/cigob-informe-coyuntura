# ADR-0055 — Presión de dolarización de carteras sensible al régimen cambiario

| | |
|---|---|
| **Estado** | Aceptado · supersede ADR-0054 |
| **Fecha** | 2026-07-14 |
| **Ámbito** | Cinturón macro · ITCM · fuentes cambiarias BCRA/ArgentinaDatos · series históricas · validación externa |
| **Precedentes directos** | ADR-0006 (brecha CCL/mayorista) · ADR-0012 (backfill) · ADR-0021 (interpolación) · ADR-0030 (meses comparables) · ADR-0053 (agregados monetarios) · ADR-0054 (dolarización de depósitos) |

## Contexto

ADR-0054 incorporó al ITCM una brecha entre el crecimiento interanual de los
depósitos privados en dólares y el crecimiento interanual real de los depósitos
en pesos. La decisión separó correctamente esa señal del IDM y evitó mezclar
valuación cambiaria dentro de un agregado monetario en pesos. Sin embargo, la
formulación basada en stocks interanuales no identifica de manera estable la
presión de los agentes por salir del peso.

El principal problema empírico es el episodio de las Cuentas Especiales de
Regularización de Activos (CERA). Durante el ingreso contemporáneo de fondos, el
stock de depósitos en dólares aumentó por un cambio regulatorio extraordinario,
no necesariamente por una decisión ordinaria de cartera. Doce meses después, la
misma discontinuidad reaparece con signo o intensidad alterados por el efecto de
base. Por lo tanto, la tasa interanual prolonga la influencia de CERA tanto en el
momento del ingreso como cuando ese nivel extraordinario entra en la base de
comparación.

Reducir la ventana a seis meses no resuelve el problema conceptual: una
formulación semestral continúa comparando stocks afectados por el mismo quiebre,
sólo desplaza y acorta sus efectos contemporáneos y de base. Tampoco resuelve el
cambio de régimen cambiario de abril de 2025. Bajo restricciones, la demanda no
satisfecha se expresa principalmente en el precio relativo del acceso al dólar;
con un mercado más abierto, una brecha baja puede coexistir con compras efectivas
altas.

El constructo de interés es, en consecuencia, **latente**: la presión de los
hogares por dolarizar sus carteras o, en términos equivalentes, por reducir su
exposición al peso. Ningún observable único lo representa de manera válida bajo
todos los regímenes. La medición debe usar el indicador observable más cercano
en cada marco institucional y traducir ambos a una escala común.

## Decisión

### 1. Reemplazar `dolarizacion_depositos` por `presion_dolarizacion`

ADR-0055 **supersede ADR-0054**. El ITCM conserva trece indicadores puntuables,
pero sustituye la brecha de stocks de depósitos por **Presión de dolarización de
carteras**, cuarto componente de la dimensión `estabilidad_monetaria`.

El indicador tiene dos etapas:

1. cada régimen convierte su observable propio en una **presión de 0 a 100**, donde
   un valor mayor representa mayor presión de salida del peso;
2. esa presión se convierte en un **puntaje ITCM de 0 a 100**, donde un valor mayor
   representa menor tensión.

La doble transformación mantiene explícita la dirección económica y permite que
los observables de precio y flujo alimenten una misma escala del índice sin
presentarlos como si fueran una única serie física homogénea.

### 2. Régimen restringido: brecha CCL/A3500 suavizada

Para los meses anteriores a abril de 2025 se utiliza la brecha entre el contado
con liquidación (CCL) y el tipo de cambio mayorista A3500.

Primero se calculan los promedios mensuales de cada cotización:

```text
brecha_mensual_t = 100 × (promedio_mensual_CCL_t /
                          promedio_mensual_A3500_t − 1)
```

La métrica del mes es el promedio simple de tres meses calendario contiguos:

```text
métrica_restringida_t = promedio(brecha_t-2, brecha_t-1, brecha_t)
```

La ventana es estricta: si falta cualquiera de los tres meses, el período no se
calcula. No se aceptan ventanas parciales ni se unen meses no contiguos.

La métrica se transforma en presión mediante interpolación lineal entre estas
anclas, con saturación fuera de los extremos:

| Brecha CCL/A3500, promedio móvil 3 meses | Presión |
|---:|---:|
| 5% | 0 |
| 15% | 25 |
| 30% | 50 |
| 50% | 75 |
| 70% | 100 |

Esta etapa interpreta la brecha como precio de una demanda de dolarización
restringida o no satisfecha plenamente en el mercado oficial.

### 3. Régimen abierto desde abril de 2025: compras netas sobre liquidez

Desde abril de 2025 se utilizan las compras netas de moneda extranjera de
**Personas Humanas** bajo el concepto “Compra-venta de billetes y divisas sin
fines específicos” del Mercado de Cambios del BCRA. El flujo se dimensiona por
el M2 transaccional privado en pesos, convertido a dólares al A3500.

La transición usa la historia disponible bajo el nuevo régimen:

- abril de 2025: ventana de 1 mes;
- mayo de 2025: ventana de 2 meses;
- junio de 2025 en adelante: ventana móvil estricta de 3 meses contiguos.

La razón se calcula sobre la suma del numerador y la suma del denominador, no
como promedio de cocientes mensuales:

```text
M2_privado_USD_m = M2_privado_ARS_m / A3500_m

métrica_abierta_t =
  100 × suma(compras_netas_USD_m) / suma(M2_privado_USD_m)
```

Las ventanas de uno y dos meses son una transición explícita, no una imputación.
A partir del tercer mes, si falta cualquier insumo de la ventana contigua, el
período se omite.

La métrica se transforma en presión mediante estas anclas:

| Compras netas / M2 privado en USD | Presión |
|---:|---:|
| 0% | 0 |
| 3% | 25 |
| 6% | 50 |
| 10% | 75 |
| 15% | 100 |

La interpolación es lineal y los valores fuera del rango se saturan en 0 o 100.
Una venta neta no genera presión negativa: queda en el piso de la escala.

### 4. Aplicar una conversión común de presión a puntaje ITCM

Ambos regímenes entregan una presión entre 0 y 100. El puntaje incorporado al
ITCM se obtiene con las siguientes anclas comunes:

| Presión | Puntaje ITCM |
|---:|---:|
| 0 | 100 |
| 25 | 85 |
| 50 | 60 |
| 75 | 35 |
| 100 | 10 |

Se interpola linealmente entre anclas y se satura en los extremos. La dirección
es inversa porque mayor presión de dolarización implica menor estabilidad
monetaria.

### 5. Conservar el peso acotado dentro de estabilidad monetaria

La dimensión `estabilidad_monetaria` conserva su peso de 26% dentro del ITCM y
su distribución interna 40/25/25/10:

| Indicador | Peso interno | Peso nominal efectivo en el ITCM |
|---|---:|---:|
| IPC mensual | 40% | 10,4% |
| Expectativa de inflación REM | 25% | 6,5% |
| IDM | 25% | 6,5% |
| Presión de dolarización de carteras | 10% | 2,6% |

El nuevo indicador conserva, por lo tanto, el **2,6% nominal del ITCM**. Ante
faltantes, la interfaz debe informar el peso efectivo que resulte de la
renormalización, no presentar el nominal como si estuviera vigente.

### 6. Aplicar reglas explícitas de datos faltantes

- No se imputan ceros, no se interpolan meses y no se trasladan observaciones
  entre regímenes.
- En el régimen restringido se exige una ventana completa de tres meses
  contiguos de brecha mensual.
- En el régimen abierto se exige que cada mes de la ventana tenga compras netas,
  M2 privado y A3500 válido. Un A3500 nulo o un denominador no positivo invalida
  el período.
- Las ventanas de uno y dos meses de abril y mayo de 2025 se identifican como
  transición parcial.
- Si la construcción fresca no produce un valor válido, se aplica el mecanismo
  general del colector macro: reutilizar el último valor válido del cache y
  marcarlo como desactualizado. Si no existe cache, el indicador se omite y el
  motor renormaliza los componentes disponibles.

### 7. Reconstruir la serie desde diciembre de 2023

El backfill comienza en diciembre de 2023. Para poder calcular ese primer punto,
la descarga del régimen restringido incluye octubre y noviembre de 2023 como
insumos de la ventana, aunque la serie publicada empiece en diciembre.

El titular y el CSV histórico deben usar la misma función de construcción. El
último punto válido de la serie debe coincidir con el valor del indicador; la
serie anterior de `dolarizacion_depositos` deja de presentarse como indicador
vigente.

### 8. Fuentes operativas

- **CCL diario:** ArgentinaDatos, cotización de contado con liquidación, precio de
  venta.
- **Tipo de cambio mayorista A3500:** BCRA, variable monetaria 5.
- **Compras netas de Personas Humanas:** anexo estadístico acumulativo del Mercado
  de Cambios del BCRA, hoja “Datos Mercado de Cambios”, concepto de billetes y
  divisas sin fines específicos.
- **M2 transaccional privado:** BCRA, variable monetaria 197.

CCL y A3500 se promedian por mes para la etapa de precio. M2 y A3500 se toman al
cierre mensual para dimensionar la etapa de flujo.

### 9. Declarar el solapamiento histórico con `cepo_mulc`

Antes de abril de 2025, `presion_dolarizacion` comparte la familia de datos
CCL/A3500 con `cepo_mulc`, indicador del cinturón de gestión. El solapamiento es
real y debe permanecer visible en la interpretación histórica:

- `cepo_mulc` registra la brecha contemporánea como señal de restricción y acceso
  al mercado cambiario;
- `presion_dolarizacion` usa un promedio estricto de tres meses para aproximar la
  presión latente de salida del peso;
- desde abril de 2025, `presion_dolarizacion` cambia a compras efectivas y deja de
  depender de la brecha.

La diferencia de constructo y de tratamiento temporal justifica conservar ambos,
pero no los vuelve estadísticamente independientes durante el tramo restringido.
Los análisis de sensibilidad y la lectura editorial deben considerar ese límite.

## Opciones consideradas

### Mantener la formulación anual de stocks de ADR-0054

Rechazada. Confunde decisiones ordinarias de cartera con el ingreso regulatorio a
CERA y prolonga la discontinuidad mediante efectos de base interanuales. Además,
una brecha de crecimiento de depósitos pierde capacidad informativa cuando el
acceso al mercado cambia de régimen.

### Usar una formulación semestral de stocks

Rechazada. Acorta el rezago, pero no elimina ni el nivel extraordinario de CERA ni
su efecto de base. Mantiene el mismo problema de constructo y agrega mayor
volatilidad sin resolver el cambio institucional de abril de 2025.

### Usar la brecha CCL/A3500 durante toda la serie

Rechazada. En un régimen abierto, una brecha baja puede ser el resultado de que la
demanda se satisface mediante compras efectivas. El precio deja de ser un proxy
suficiente de la cantidad demandada.

### Usar compras netas durante toda la serie

Rechazada. Antes de la apertura, las restricciones administrativas limitaban la
cantidad observada. El flujo efectivo subestimaría la demanda latente y no sería
comparable con el período abierto.

### Usar como benchmark operativo “compras en efectivo más cobertura” del BCRA

Rechazada como fuente operativa. La idea es conceptualmente valiosa porque
combina demanda de moneda y cobertura cambiaria, pero no existe una serie pública,
mensual, estructurada y con perímetro estable que permita reconstruir de manera
reproducible las compras en efectivo de los hogares junto con sus posiciones de
cobertura. Puede utilizarse como referencia cualitativa, no como insumo
automatizado del índice.

### Empalmar los dos observables sin una escala latente común

Rechazada. Un porcentaje de brecha y una razón de flujos sobre liquidez no tienen
la misma unidad. Presentarlos como una serie física continua ocultaría el cambio
de medición. Las dos transformaciones a presión y luego a puntaje hacen explícito
el puente metodológico.

## Limitaciones

- La presión es un constructo latente y la continuidad entre regímenes es
  metodológica, no una identidad estadística entre observables.
- Las anclas expresan juicio de calibración y deben someterse a stress test; no
  son umbrales naturales ni estimaciones causales.
- ArgentinaDatos provee una serie pública y reproducible de CCL, pero no es el
  organismo oficial del mercado cambiario.
- La etapa abierta cubre compras netas de Personas Humanas sin fines específicos;
  no incluye toda la dolarización corporativa, transferencias de activos ni todas
  las coberturas con derivados.
- Convertir M2 a dólares introduce sensibilidad al A3500 en el denominador. Se
  conserva porque dimensiona el flujo respecto de la liquidez transaccional
  disponible, pero no equivale a riqueza financiera total.
- Abril y mayo de 2025 tienen ventanas de uno y dos meses y, por lo tanto, menor
  suavización que los períodos posteriores.
- Durante el régimen restringido existe solapamiento histórico con `cepo_mulc`.

## Consecuencias

- ADR-0054 deja de describir la metodología vigente y queda superado por este
  ADR; se conserva como registro de la decisión anterior.
- El ITCM mantiene trece indicadores puntuables y el peso total de sus seis
  dimensiones.
- La dimensión de estabilidad monetaria conserva cuatro componentes y el nuevo
  indicador mantiene 10% interno, equivalente a 2,6% nominal del ITCM.
- CERA deja de dominar el indicador mediante crecimientos de stocks
  contemporáneos o efectos de base.
- La serie publicada identifica explícitamente el régimen, la métrica de origen,
  la longitud de la ventana y si la transición es parcial.
- El backfill desde diciembre de 2023 combina dos observables bajo una escala
  común declarada, sin ocultar el quiebre de abril de 2025.
- Los resultados coyunturales, la sensibilidad y la validación externa deben
  provenir de una regeneración del pipeline; este ADR no fija cifras vigentes.
