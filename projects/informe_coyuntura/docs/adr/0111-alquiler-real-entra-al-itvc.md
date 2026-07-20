# ADR-0111 — El costo del alquiler entra al cinturón; pobreza y expectativas no

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | ITVC · dimensión `precios` · `alquiler_real` (nuevo) · serie `itvc_alquiler` |
| **Fecha** | 2026-07-20 |
| **Origen** | Auditoría de Vida Cotidiana, punto 3.6 y recomendación 4 (prioridad alta) |

## Contexto

La auditoría señaló tres ausencias frente al objetivo declarado del cinturón
—capturar el humor social que se traduce en voto—: **pobreza/indigencia**,
**costo de vivienda/alquileres** y **expectativas a futuro**.

Se relevaron las tres contra la API de series de datos.gob.ar. Las consultas
quedan registradas para que el resultado sea auditable.

## Alquiler: entra

**Serie**: `104.1_I2RE_2016_M_25` — IPC-GBA, alquiler de la vivienda, mensual
desde abr-2016. Deflactada por `103.1_I2N_2016_M_19` (nivel general de GBA).

Construcción idéntica a `ipc_alimentos` (ADR-0033): encarecimiento **relativo**,
no nominal, rebaseado a 100 = 4T-2023. Es la pregunta de precios pura,
independiente del salario, para no repetir el ratio que ya mide la brecha
salario/CBT.

**El resultado es contundente: 107,7 en dic-2023 → 64,3 en jun-2026.** El
alquiler subió alrededor de un 55% más que el resto de los precios del
aglomerado, en caída monótona durante todo el mandato. Ningún componente del
cinturón capturaba eso.

### Que aporta señal propia está medido, no supuesto

Contra los catorce componentes existentes, en **cambios mes a mes** (la lectura
que separa co-tendencia de información repetida, ADR-0085/0108):

| componente | niveles | diferencias |
|---|---|---|
| `ipc_alimentos` | −0,914 | **−0,557** |
| `brecha_salario_cbt` | −0,890 | −0,497 |
| `endeudamiento_familiar` | −0,852 | −0,160 |
| `sentimiento_digital` | −0,785 | −0,130 |

Ninguna supera el umbral de 0,7 al destendenciar. La más alta (−0,557 con
alimentos, ambos precios) es comparable al mayor acoplamiento **ya existente**
dentro del cinturón (+0,512 entre salario y endeudamiento).

### Peso

Entra a **Presión de precios con 20%**: tarifas 45 · alimentos 35 · alquiler 20.
El peso **nominal de la dimensión no se toca** (sigue 25%), así que la
arquitectura de cinco dimensiones queda intacta.

El criterio no es el número que produce: **el alquiler golpea a los hogares
inquilinos —alrededor de un tercio de los urbanos— mientras tarifas y alimentos
pesan sobre todos**, y por eso entra por debajo de los otros dos, que ceden
proporcionalmente conservando su orden relativo.

**ITVC 95,4 → 94,6 · tensión 5,9 → 6,1.**

### Limitación

**Sólo mide el Gran Buenos Aires.** Es la única apertura de alquiler que publica
INDEC: cinco consultas distintas —"IPC nacional alquiler de la vivienda",
"alquiler vivienda nacional índice precios", "IPC aperturas vivienda alquiler",
"alquiler efectivo vivienda", "locación vivienda índice"— devuelven, fuera de la
serie de GBA y su gemela trimestral, sólo actividad inmobiliaria, empleo del
sector y deflactores implícitos del VAB. Ninguno es el costo de alquilar.

Por eso se deflacta con el nivel general **de GBA** y no con el nacional:
dividir un precio de una plaza por el índice de otra mezclaría dos mercados en
el mismo cociente.

## Pobreza: no entra, y el hueco es menor de lo que parece

La serie existe y es buena: `64.2_POBLACION_NUA_0_0_34_74` — población bajo la
línea de pobreza, **nacional, semestral, desde 2003**. Su arco bajo este mandato
es fuerte: 40,1% (S2-2023) → **52,9%** (S2-2024) → **28,2%** (S2-2025).

No entra por dos razones:

1. **El cinturón ya mide contra la línea de pobreza.** `brecha_salario_cbt` es
   RIPTE / CBT, y la CBT **es** la línea de pobreza del hogar. Sumar la línea
   como componente propio sería contar dos veces el denominador de un
   componente existente. Lo que la tasa aporta de nuevo es *distribución* —
   cuánta gente está debajo—, no *nivel*.
2. **Es semestral con rezago largo**, en un cinturón mensual: quedaría constante
   seis meses seguidos y aportaría un escalón dos veces al año.

**Queda como candidata a card de contexto**, donde su carga simbólica se publica
sin distorsionar la frecuencia del índice. Es una decisión editorial pendiente.

## Expectativas: no entra

Las únicas series de expectativas vivas son de **inflación esperada**
(`431.1_EXPECTATIVANA_M_0_0_29_85`, mediana del REM: 150% en dic-2023 → 25% en
ene-2026). Dos problemas:

1. **Terminan en 2026-01** — seis meses de rezago contra un cinturón cuyo dato
   más fresco es de julio.
2. **El REM ya está en el ITCM** como `rem_ipc_12m`. Incorporarlo acá pondría la
   misma fuente a puntuar en dos cinturones.

El ICC de la UTDT se desagrega por situación personal / macro / bienes durables
y por región, **no** por presente vs. futuro, así que no ofrece el corte de
expectativas que la auditoría imaginaba. La ausencia de una medida prospectiva
es real y queda declarada.

## Consecuencias

- Alta completa: config, serie (`itvc_alquiler`, 33 puntos desde oct-2023),
  colector, dimensión, mapeo de publicación, y los cinco archivos web
  (label, unidades corta y larga, descripción, fórmula, ficha).
- Tres tests cambiaron de número esperado y **cada uno dice por qué**: el
  ejemplo del documento renormaliza precios sobre dos componentes porque no
  trae el tercero, y el guard de conteo pasa de 14 a 15 — el mismo guard que
  detectó a `sentimiento_digital` desapareciendo del snapshot.
- El ITVC pasa a 15 componentes y el tablero a 59 indicadores.
