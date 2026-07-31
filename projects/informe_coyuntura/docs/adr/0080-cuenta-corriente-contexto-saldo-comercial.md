---
madr: 4
id: '0080'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [saldo_comercial_12m, cuenta_corriente]
relacionado: ['0056', '0077']
ambito: 'Cinturón macro · `saldo_comercial_12m` · serie acompañante `cuenta_corriente`'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), observación 8'
---

# ADR-0080 — La cuenta corriente acompaña al saldo comercial, y el texto público se corrige

## Contexto y planteo del problema

La auditoría pedía la cuenta corriente "como contexto del saldo comercial",
marcándola como trimestral y por lo tanto no puntuable.

**Una primera revisión la declaró bloqueada por falta de fuente. Esa conclusión
era incorrecta**: se buscó en la API de datos.gob.ar con términos que no
devolvían resultados y se dio el punto por cerrado sin insistir. La serie
existe, es oficial y está vigente.

## Opciones consideradas

- **Cuenta corriente del INDEC**, en base devengada — elegida.
- **Cuenta Corriente Cambiaria del BCRA**, mensual y más fresca — evaluada y descartada: mide los dólares que efectivamente pasaron por el mercado de cambios, no las transacciones devengadas. Son conceptos distintos y bajo restricciones cambiarias divergen mucho.

## Decisión

### 1. Entra `cuenta_corriente` como serie acompañante

En el gráfico del saldo comercial, con el patrón del TCRM y del núcleo del IPC:
dos curvas en el mismo eje, más una línea de referencia en cero rotulada
"equilibrio externo". **No puntúa** y no altera ningún peso.

- Fuente: **INDEC, balanza de pagos** (`160.2_TL_CUENNTE_0_T_22`), trimestral.
- **Acumulada a cuatro trimestres**, no el trimestre suelto: el indicador que
  acompaña es un acumulado de doce meses y compararlo contra un trimestre
  mezclaría escalas.

**Por qué el INDEC y no el balance cambiario del BCRA.** Existe una segunda
serie —"Cuenta Corriente Cambiaria", mensual y más fresca (abr-2026 contra
1T-2026)— que se evaluó y se descartó: mide los dólares que **efectivamente
pasaron por el mercado de cambios**, no las transacciones **devengadas**. Son
conceptos distintos y bajo restricciones cambiarias divergen mucho. La cuenta
corriente propiamente dicha es la del INDEC, y es la que sostiene el contraste
de arriba.

### 2. Se corrige el texto público

La descripción pasa a decir que el indicador **muestra si el intercambio de
bienes aporta o resta dólares**, y que eso no alcanza para saber si el sector
externo en conjunto los genera.

### 3. Se declara la limitación en la ficha, con el número

Se agrega como primera limitación, con la magnitud concreta del drenaje y la
comparación superávit-de-bienes contra déficit-de-cuenta-corriente.

### Consecuencias

- El ITCM **no cambia**: la cuenta corriente no puntúa y el saldo comercial
  sigue con su banda y su peso.
- Lo que cambia es la **honestidad de la lectura**: el lector que abra el
  indicador ve las dos curvas y entiende que el superávit comercial convive con
  un déficit externo.
- Serie de **9 puntos trimestrales** desde 1T-2024.

## Más información

### Precedentes directos

ADR-0077 (patrón de serie acompañante en el modal) · ADR-0056 (regla automática del saldo)

### Limitaciones

- **Rezago**: la balanza de pagos se publica con más demora que el ICA. Al
  momento de esta decisión el saldo comercial llegaba a may-2026 y la cuenta
  corriente a 1T-2026.
- **Frecuencia distinta en un mismo gráfico**: la curva trimestral se dibuja
  suavizada junto a una mensual y visualmente puede leerse como si tuviera la
  misma densidad de observaciones. El tooltip muestra las fechas reales y la
  unidad declara el acumulado de cuatro trimestres.
- La cuenta corriente **tampoco es la foto completa** del frente externo: la
  cuenta financiera y la variación de reservas cuentan la otra mitad.
- Que el drenaje sea de ~17.600 millones anuales es una constatación del
  período reciente, no una constante estructural.

### Lo que apareció al mirarla

El hallazgo excede el pedido original. Contrastando ambas magnitudes en base
anual comparable:

| trimestre | saldo comercial 12m | cuenta corriente 12m |
|---|---|---|
| 2024-10 | +16.428 | +5.891 |
| 2025-04 | +13.995 | **−5.279** |
| 2025-07 | +10.396 | **−8.005** |
| 2025-10 | +9.817 | **−7.788** |
| 2026-01 | +13.347 | **−4.281** |

*(millones de dólares)*

**El saldo comercial marca superávit sólido mientras la cuenta corriente está en
déficit**, con una brecha estable en torno a los **17.600 millones de dólares
anuales**: servicios, intereses de la deuda y utilidades giradas al exterior
drenan más de lo que aporta el superávit de bienes.

Y el texto público del indicador afirmaba exactamente lo que los datos
desmienten:

> *"Indica si el sector externo genera o drena los dólares que necesita el
> programa."*

Es justamente lo que el saldo de bienes **no** indica. Ninguna de las tres
limitaciones que la ficha declaraba mencionaba esta brecha de cobertura.

### Lección de proceso

Este punto se había declarado **bloqueado por falta de fuente** sin insistir lo
suficiente. La fuente existía, era oficial, y al mirarla apareció una
inconsistencia en el texto público de un indicador que **sí puntúa**. Declarar
un punto como "sin fuente disponible" exige el mismo estándar de evidencia que
cualquier otra conclusión.
