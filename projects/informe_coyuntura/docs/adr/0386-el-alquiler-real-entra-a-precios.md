---
madr: 4
id: '0386'
estado: 'aceptado'
fecha: 2026-10-27
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [alquiler_udesa_real, alquiler_real]
archivos: ['scripts/itvc.py', 'scripts/publicar.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/procedencia_anclas.py', 'config.py', 'scripts/vida_cotidiana/main.py', 'scripts/vida_cotidiana/collectors/alquiler_udesa.py', 'scripts/vida_cotidiana/cargar_alquiler_udesa.py', 'data/vida/alquiler_udesa.json', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/datos.ts', 'web/src/lib/formulas.ts']
relacionado: ['0359', '0373', '0411']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Presión de precios'
origen: 'Reunión del 26-oct-2026: «Precios: se mantienen la inflación de alimentos y la canasta de servicios públicos; Juan va a evaluar sumar el costo real del alquiler de UdeSA (CIF) con Mercado Libre Inmuebles.» Decisión de Juan del 27-oct-2026: carga manual mensual.'
---

# ADR-0386 — El alquiler de UdeSA – Mercado Libre entra a precios

## Contexto y planteo del problema

La dimensión de precios mide alimentos, servicios públicos y el alquiler del IPC
del Gran Buenos Aires (`alquiler_real`, ADR-0111). Ese alquiler sigue contratos
vigentes, que se ajustan con rezago: dice poco de lo que enfrenta quien sale a
alquilar hoy. La reunión del 26-oct pidió evaluar el alquiler de los avisos de
UdeSA – Mercado Libre Inmuebles.

Un relevamiento previo concluyó que esa fuente no se puede automatizar: sólo
publica un PDF por mes en carpetas de Google Drive, el conjunto de datos que el
propio informe dice ofrecer no existe en la página, las cifras están en la
prosa, y no hay condiciones de reutilización. Juan resolvió cargarla **a mano,
una vez por mes**, leyendo el PDF.

Aviso de nombre: `alquiler_real` ya existía y es el del IPC. El nuevo se llama
`alquiler_udesa_real`; no reemplaza al anterior.

## Factores de decisión

- Que cada cifra salga de una frase textual del PDF y quede citada.
- No interpolar ni encadenar lo que la fuente no dice.
- La reunión dejó alimentos y servicios públicos como estaban.
- No mover el peso de la dimensión (0,25).

## Opciones consideradas

- **Dividir el 20 % de la vivienda entre las dos miradas (elegida).**
- Ceder proporcionalmente de los tres componentes (regla de ADR-0130/0153).
- Reemplazar el alquiler del IPC por el de UdeSA.

## Decisión

**Qué se carga.** `data/vida/alquiler_udesa.json`: una entrada por mes con la
variación interanual nominal de los departamentos de AMBA en pesos corrientes
(`interanual_deptos_amba_pct`), la intermensual cuando el texto la da sin
ambigüedad, la frase textual, la URL del PDF y la fecha de carga. El precio
mediano por m² sólo está en gráficos de imagen y no se carga.

**Historia: 45 meses leídos (ene-2023 a sep-2026), 16 con la serie principal.**
El informe da la interanual nominal de AMBA recién desde junio de 2025. Hasta
mayo de 2023 expresa el alquiler en pesos constantes y de junio de 2023 a mayo
de 2025 trae la intermensual de AMBA y la interanual sólo por zona (CABA y
GBA). Esos 29 meses quedan sin dato en `sin_dato`: no se interpolan ni se
encadenan desde las intermensuales. Dos de las intermensuales (abr-2024 y
nov-2024) tampoco se cargan: la frase no permite distinguir la cifra de
departamentos de la de casas.

**Cálculo.** `real = (1 + nominal) / (1 + IPC) − 1`, con el IPC interanual del
mismo mes del nivel general del GBA de la planilla original del INDEC (la que
usa `alquiler_real`, ADR-0291). El alquiler es de AMBA, así que se deflacta con
el índice de la misma plaza y no con el nacional.

**Componente.** `100 − real` en puntos. 100 = el alquiler pedido subió igual que
los precios en el año; por debajo, más caro en términos reales (deterioro),
con el signo de la dimensión. **No se rebasea al 4T-2023**: la fuente sólo da
variaciones interanuales y no hay forma honesta de encadenarlas. Por eso este
componente mira el último año y el del IPC, el acumulado desde 2023; no son
comparables en nivel (ver Consecuencias).

**Peso: 10 % de la dimensión (2,5 % del índice).** Sale de la mitad del que
tenía el alquiler del IPC (20 % → 10 %): son dos miradas al mismo gasto, y el
20 % lo fijó ADR-0111 por la proporción de hogares inquilinos. Alimentos (35 %) y
servicios públicos (45 %) no se tocan, como pidió la reunión. El peso de la
dimensión no cambia.

**Rezago y faltantes.** `MAX_DIAS['alquiler_udesa_real'] = 105`: el punto del mes
M necesita además el IPC de M, que sale a mediados de M+1. Si el mes no está
cargado la tarjeta conserva el último valor como desactualizado. A los 45 días
sin carga nueva el colector emite un `[COTEJO_MANUAL]` que llega a Slack.

**Carga mensual.** `scripts/vida_cotidiana/cargar_alquiler_udesa.py --mes AAAA-MM
--valor X --url … --frase "…"`. Valida formato y rango, exige la frase,
rechaza un mes repetido y un mes futuro.

### Consecuencias

- Con el snapshot del 27-oct-2026: nominal 20,4 % (sep-2026), IPC GBA
  interanual 33,5 %, real −9,8 % → componente 109,8.
- Dimensión de precios 97,7 → 103,7; índice de impacto social 95,7 → 97,2;
  tensión 5,9 → 5,6. Con la otra opción (cesión proporcional del 10 %) habría
  sido 99,0 y 96,0.
- El salto es grande porque las dos miradas dicen cosas muy distintas: el
  alquiler del IPC está en el piso del tablero (50,0, acumulado desde 2023) y el
  de los avisos cae en términos reales en el último año (109,8). Eso es
  información —el alquiler que se pide lleva meses perdiendo contra la
  inflación—, pero no es una mejora para quien ya alquila ni para el acumulado
  del mandato, y la ficha lo dice.
- La serie del componente arranca en jun-2025 (16 puntos); la reconstrucción
  histórica del índice no lo usa antes.
- Es un indicador de carga manual: si nadie lo carga, queda desactualizado y el
  aviso lo recuerda. No hay reutilización declarada por la fuente: se citan
  cifras con frase y enlace.

### Confirmación

`tests/test_alquiler_udesa.py` fija el registro, el cálculo, el script de carga,
el aviso de atraso y la composición de la dimensión. `tests/test_publicar.py`
espera 19 componentes.

## Pros y contras de las opciones

- Dividir el 20 %: alimentos y servicios quedan como pidió la reunión y el
  gasto de vivienda sigue pesando lo que ADR-0111 fijó; el alquiler del IPC
  pierde la mitad de su peso.
- Cesión proporcional: respeta la regla de las altas anteriores pero toca a
  alimentos y servicios, que la reunión dijo mantener, y la vivienda pasaría a
  pesar 28 %.
- Reemplazar: más simple, pero tira la única medición de contratos vigentes y
  la de UdeSA arranca en jun-2025 con 16 puntos.

## Más información

Fuente: https://www.udesa.edu.ar/indices-mercado-libre (Centro de Estudios
Cuantitativos en Negocios, UdeSA; datos de avisos de Mercado Libre Inmuebles).
Relevamiento de factibilidad del 27-oct-2026. Las 45 frases textuales y las URL
de cada PDF están en el registro.
