---
madr: 4
id: '0130'
estado: 'aceptado'
fecha: 2026-07-25
cinturon: 'vida'
indicadores: [empleo_registrado, empleo]
complementa: ['0112']
relacionado: ['0127', '0218', '0219', '0223', '0225']
modificado_por: ['0214']
complementado_por: ['0214']
ambito: 'ITVC · `empleo_registrado` (nuevo) · dimensión `empleo` · serie'
origen: 'Hallazgo al separar la recaudación por componente (ADR-0127)'
---

# ADR-0130 — La dimensión de empleo pasa a medir empleo

| **Complementa** | ADR-0112 (entrada del índice líder) |

## Contexto y planteo del problema

La dimensión se llama **empleo** y ninguno de sus cuatro componentes medía
empleo:

| componente | qué mide en realidad |
|---|---|
| `mortalidad_pymes` | producción industrial (IPI) |
| `despacho_cemento` | construcción (ISAC) |
| `pluriempleo` | cuántos ocupados tienen más de un trabajo |
| `indice_lider` | anticipación de puntos de giro |

Los cuatro son razonables como señales de contexto laboral. Ninguno cuenta
puestos de trabajo.

## Opciones consideradas

- **Entra `empleo_registrado`** —asalariados del sector privado declarados al SIPA— expresado en base 100 = 4T-2023 como el resto de los componentes — elegida.
- **Seguir midiendo la dimensión con lo que tenía** — reemplazado: la dimensión de empleo pasa a medir empleo.

## Decisión

Entra **`empleo_registrado`**: asalariados del sector privado declarados al
SIPA. La card publica el nivel en miles de puestos; el índice del cinturón lo
expresa en base 100 = 4T-2023, como el resto de los componentes (ADR-0018).

| | |
|---|---|
| dic-2023 | 6.379,1 mil puestos |
| **abr-2026** | **6.130,1 mil puestos** |
| variación | **−249,0 mil (−3,90%)** |
| índice B100 | **96,09** |

**La caída interanual no se interrumpió en ningún mes desde ago-2025**, y el
pico de toda la serie es ago-2023, anterior al mandato.

### Pesos

Entra con **0,35 y pasa a ser el componente principal**: es el único que mide
directamente lo que la dimensión dice medir. Los cuatro existentes ceden
proporcionalmente (×0,65) y conservan su orden relativo — mismo procedimiento
que ADR-0112. El peso **nominal de la dimensión no se toca** (15% del ITVC).

| | antes | ahora |
|---|---|---|
| **empleo_registrado** | — | **0,35** |
| mortalidad_pymes | 0,36 | 0,23 |
| despacho_cemento | 0,32 | 0,21 |
| indice_lider | 0,20 | 0,13 |
| pluriempleo | 0,12 | 0,08 |

## Más información

### Limitaciones

- **Cuenta puestos, no personas.** Un trabajador con dos empleos registrados
  cuenta dos veces.
- **El empleo no registrado queda afuera por definición** — alrededor de un
  tercio del empleo total en Argentina. Mide el empleo formal y no debe leerse
  como el mercado laboral completo.
- **No dice nada sobre salarios.** No captura si el empleo que queda está mejor
  o peor pago que el que se perdió. Esa parte la mira `brecha_salario_cbt`.
- **Las declaraciones se revisan hacia atrás** durante varios meses: los
  últimos puntos pueden moverse.
- Los otros cuatro componentes **siguen adentro y siguen siendo proxies**. La
  dimensión mejora, no queda resuelta: sigue llamándose "prospectivas de
  empleo" y sólo uno de sus cinco componentes mira hacia adelante.

### Cómo apareció

Al pasar la recaudación a DGI (ADR-0127) quedó afuera la seguridad social, y se
anotó como limitación que esa parte "sigue su propia dinámica —cae en términos
reales desde fines de 2025— y vale la pena mirarla aparte".

Al ir a mirarla apareció algo más grande: **existe el dato directo de empleo
registrado, mensual y publicado, y el cinturón no lo usaba.**

### Por qué el sector privado y no el total

El empleo público se publica por separado y no entra. La dimensión describe las
condiciones del mercado de trabajo que enfrenta un hogar; el tamaño del Estado
ya se mide —y se puntúa— en el cinturón de gestión (`reduccion_estado`).
Sumarlo acá haría que una reducción de la planta estatal **empeorara el cinturón
de vida cotidiana al mismo tiempo que mejora el de gestión, con el mismo dato**.

### Por qué la serie CON estacionalidad

La comparación es contra una base fija de tres meses (4T-2023), no contra el
mes anterior: la estacionalidad de la base y la del mes corriente se compensan.
Mismo criterio que el resto de los componentes B100 del cinturón.

### La trampa que costó una corrida en falso

`scripts/vida_cotidiana/collectors/indec_series.py` tiene una **whitelist
explícita por sección**: agregar una serie a `INDEC_SERIES` en `config.py` no
alcanza para que el colector la emita, hay que sumar la clave al bucle
correspondiente.

En el primer intento se hizo sólo lo primero. El resultado fue una card sin
valor y un `G1 sin valor` en el gate — un síntoma que no apunta para nada a la
causa. Queda un comentario en el bucle para que el próximo no pierda el rato.
