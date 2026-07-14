# ADR-0053 — Transparencia y agregados monetarios del IDM

| | |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-13 |
| **Ámbito** | IDM del ITCM · web (`IndicadorModal.astro`, `metodologia/[id].astro`, `descripciones.ts`, `fichas.ts`) · tests de display |
| **Precedentes directos** | ADR-0007 (fichas conceptuales) · ADR-0009 (metodología del IDM) · ADR-0051 (sin cards de contexto) |
| **Expediente** | `docs/bmad-output/implementation-artifacts/investigations/agregados-monetarios-itcm-investigation.md` |

## Contexto

Una revisión editorial del IDM planteó tres cuestiones:

1. usar el **M2 Transaccional del Sector Privado**, definido como circulante en
   poder del público más cuentas corrientes y cajas de ahorro privadas en pesos,
   excluyendo depósitos a la vista remunerados de personas jurídicas;
2. reemplazar el M3 privado en pesos por un **M3 prima o M3\*** que incorporara
   depósitos privados en dólares;
3. explicar con claridad cuánto pesa el IDM dentro del ITCM.

La auditoría confirmó que la primera propuesta **ya estaba implementada**. El IDM
usa la variable 197 del BCRA, “M2 transaccional del sector privado”, pero la
explicación pública no enumeraba sus componentes y exclusión.

La metodología vigente, definida por ADR-0009, es:

```text
IDM = crecimiento real i.a. del M3 privado en pesos
    − crecimiento real i.a. del M2 transaccional privado en pesos
```

El IDM pesa 30% dentro de la dimensión de estabilidad monetaria. Esa dimensión
pesa actualmente 26% del ITCM, por lo que el peso nominal efectivo del indicador
es:

```text
30% × 26% = 7,8% del ITCM
```

La ficha metodológica mostraba parte de esta información, pero el modal principal
sólo indicaba dimensión y peso interno. Además, `aporte_score` expresa una
**tensión equivalente sobre 10**, no la contribución aritmética sumable al índice.
La proximidad visual de ambos conceptos podía inducir a interpretarlos como el
mismo valor.

### Auditoría del M3 ampliado

Se reconstruyó una variante privada bimonetaria:

```text
M3* privado = BCRA 17 + BCRA 100 + BCRA 104
```

La variable 104 son depósitos privados no financieros en moneda extranjera
expresados en pesos. La reconstrucción es técnicamente automatizable y el BCRA
utilizó históricamente el concepto M3*, aunque su perímetro no fue completamente
estable y los informes actuales presentan el M3 privado en pesos y los depósitos
en moneda extranjera por separado.

El backtest comparó 30 observaciones mensuales entre diciembre de 2023 y mayo de
2026:

- la variante M3* elevó el IDM en promedio **6,91 puntos porcentuales**;
- fue mayor que el IDM vigente en **29 de 30 meses**;
- cambió el signo de la lectura en **cinco meses**;
- la diferencia máxima fue **+19,10 puntos** en noviembre de 2024;
- en mayo de 2026 llevó el IDM de **4,30 a 8,18 puntos**;
- con las bandas vigentes, el puntaje hubiera pasado de aproximadamente 53,3 a
  10, reduciendo mecánicamente el ITCM cerca de 3,38 puntos;
- en el promedio del período, aproximadamente 68,7% del crecimiento de los
  depósitos en dólares expresados en pesos provino de la valuación cambiaria;
- los ingresos extraordinarios de depósitos por CERA también alteraron de forma
  material la serie, sin equivaler automáticamente a creación o exceso de pesos
  transaccionales.

La sustitución, por lo tanto, no sería una ampliación neutral. Cambiaría el
constructo desde una comparación pesos/pesos a otra entre liquidez bimonetaria y
demanda transaccional exclusivamente en pesos.

## Decisión

### 1. Conservar los agregados y la metodología puntuable

Se conserva el M3 privado en pesos del ADR-0009 y el M2 Transaccional del Sector
Privado de la variable BCRA 197. No cambian fórmula, insumos, pesos, bandas,
series ni backfill.

M3* **no reemplaza** al M3 privado dentro del IDM. La liquidez bimonetaria podría
ser objeto de un indicador futuro separado, pero requeriría:

- objetivo y denominador funcionalmente comparables;
- separación entre cantidad de depósitos y valuación cambiaria;
- tratamiento explícito de CERA y otros cambios regulatorios;
- nuevas bandas y serie histórica;
- análisis de solapamiento con TCRM y reservas;
- un ADR propio.

No se crea una card contextual de M3*: ADR-0051 fijó la regla pareja de que el
tablero no publica cards que no puntúan.

### 2. Precisar la definición pública del M2

La descripción conceptual del IDM explicita que el M2 transaccional incluye:

- circulante en poder del público;
- cuentas corrientes privadas en pesos;
- cajas de ahorro privadas en pesos;
- exclusión de depósitos a la vista remunerados de personas jurídicas.

Conforme a ADR-0007, la descripción pública explica el concepto y su relevancia.
Los organismos, variables, APIs y transformaciones permanecen en la ficha
técnica, no en el campo “qué aporta”.

### 3. Publicar la cadena completa de ponderación y aporte

El modal y la ficha metodológica muestran juntos:

```text
peso interno × peso de la dimensión = peso efectivo del indicador
puntaje aplicado × peso efectivo = aporte aritmético al índice
```

Los valores se leen del snapshot vigente; no se hardcodean números coyunturales.
La implementación sigue estas prioridades:

1. `peso_efectivo` almacenado en el indicador dentro de la dimensión;
2. `peso_efectivo` publicado en la card;
3. producto entre peso efectivo/nominal de la dimensión y peso interno, sólo
   como fallback para snapshots anteriores.

Para el puntaje:

1. `puntaje_aplicado`;
2. `puntaje_banda`;
3. `puntaje_<índice>` publicado en la card, como fallback histórico.

El aporte aritmético es siempre:

```text
aporte al índice = puntaje aplicado × peso efectivo
```

No se usa `aporte_score` para este cálculo. Ese campo conserva su significado de
tensión equivalente sobre 10 y se presenta separado, con una aclaración expresa.

### 4. Respetar renormalizaciones, contexto e ITVC base 100

- Si hay faltantes y los pesos efectivos difieren de los nominales, la interfaz
  publica el peso efectivo vigente y evita una igualdad nominal falsa.
- Un indicador con `en_indice: false`, o ausente de las dimensiones, no muestra
  ponderaciones ni aporte residual.
- Para ITVC se habla de **nivel aplicado**, no de puntaje `/100`; la contribución
  se expresa de todos modos en puntos del ITVC.
- La ausencia de un valor no se convierte en cero: las líneas que no puedan
  derivarse se omiten.

## Opciones consideradas

### Incorporar M3* directamente al IDM

Rechazada. Mezcla una oferta bimonetaria con una demanda transaccional en pesos,
introduce valuación cambiaria y responde a flujos regulatorios extraordinarios.
El backtest demuestra desplazamiento de nivel, cambios de signo y saturación de
las bandas vigentes.

### Publicar M3* como card de contexto

Rechazada. Contradice la regla institucional de ADR-0051: el tablero no expone
cards que no integran la puntuación. La auditoría queda disponible en el
expediente y puede reabrirse si se diseña un indicador puntuable independiente.

### Mostrar sólo pesos nominales

Rechazada. Ante faltantes, el motor renormaliza; mostrar el producto nominal
podría no reconciliar con el índice publicado.

### Usar `aporte_score` como contribución al ITCM

Rechazada. Es una tensión equivalente sobre 10 y no una magnitud sumable al
índice. Para el snapshot auditado, 4,7/10 y aproximadamente 4,15 puntos del ITCM
son conceptos diferentes.

### Hardcodear 30%, 26%, 7,8% y el aporte actual

Rechazada. Los pesos pueden cambiar por configuración o renormalización, y el
puntaje se actualiza con cada período. La web debe leer el snapshot vigente.

### Extraer un helper común de ponderaciones

Rechazada por ahora. Sólo hay dos consumidores y producen salidas diferentes:
el modal serializa metadata para JavaScript cliente y la página metodológica
renderiza en Astro. Se mantiene una derivación localizada con el mismo contrato y
regresiones estáticas.

### Mantener la presentación fragmentada

Rechazada. Obliga al lector a reconstruir la ponderación entre distintas
pantallas y facilita confundir tensión equivalente con aporte aritmético.

## Consecuencias

- El IDM conserva exactamente su valor, puntaje, serie, bandas y peso efectivo.
- La definición del M2 queda alineada con la metodología oficial de la variable
  BCRA 197.
- El lector puede reconciliar en una sola vista la incidencia del indicador en el
  ITCM.
- Los ajustes del analista y las renormalizaciones por faltantes quedan reflejados
  mediante `puntaje_aplicado` y `peso_efectivo`.
- `aporte_score` permanece disponible, pero inequívocamente separado del aporte
  aritmético.
- La presentación genérica beneficia también a ITCG, ITCP e ITVC, respetando la
  semántica base 100 de este último.
- Existe una pequeña duplicación deliberada de la derivación entre el modal y la
  ficha metodológica; se cubre con tests de contrato de la capa pública.
- No se ejecutan colectores ni se regeneran `informe.json`, `series.json` o
  salidas históricas porque esta decisión no modifica datos ni metodología.
- Este ADR complementa ADR-0007 y ADR-0009; no los reemplaza ni altera.
