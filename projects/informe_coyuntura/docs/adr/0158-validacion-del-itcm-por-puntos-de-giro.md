---
madr: 4
id: '0158'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'macro'
archivos: ['scripts/puntos_de_giro.py']
relacionado: ['0167', '0226']
cerrado_por: ['0159']
ambito: 'validación externa del ITCM; módulo `scripts/puntos_de_giro.py`'
---

# ADR-0158 — El ITCM se valida por puntos de giro, no sólo por correlación

- **Relacionados**: ADR-0154 (el líder pasa a ancla del ITCM), ADR-0155 (ancla
  del ITVC), ADR-0019 D6 (validación externa), ADR-0031 (matriz cruzada)

## Contexto y planteo del problema

El editor no quedó conforme con la validación externa y señaló el problema de
fondo: **validar un compuesto de seis dimensiones contra UNA variable es comparar
peras con manzanas.** Tenía razón, y al investigar cómo lo resuelven índices
similares apareció algo que cambia el encuadre.

## Opciones consideradas

- **Validar el ITCM también por puntos de giro** — elegida, siguiendo el criterio de la OCDE: el compuesto debe dar menos señales falsas y menos giros perdidos que cualquiera de sus componentes sueltos.
- **Validar sólo por correlación** — insuficiente: no dice si el compuesto aporta algo por encima de mirar los indicadores por separado.

## Decisión

Los cuatro cinturones no son el mismo tipo de objeto y no les corresponde el
mismo régimen:

- el **ITCM** es un compuesto económico y sí puede tener serie de referencia →
  **este ADR** le agrega validación por puntos de giro;
- el **ITVC/ITCG/ITCP** son socioeconómicos → panel de estadísticas relacionadas
  con las diferencias explicadas, que queda como trabajo siguiente.

`scripts/puntos_de_giro.py` implementa Bry-Boschan simplificado: ciclo como
desviación de una media móvil centrada, extremos locales, y **alternancia +
duración mínima de fase iteradas hasta converger**.

### Consecuencias

- La sección de macro publica la concordancia y **declara por qué no publica el
  adelanto**. Cuando entren meses, los provisorios se confirman solos y el texto
  pasa a informarlo — la condición está en el código, no en un recordatorio.
- La ventana es de 13 meses y la fase mínima de 5. El sistema original usa 75
  meses de media móvil; con series de ~30 eso es imposible. Es la adaptación a la
  muestra que hay y está declarada en el módulo.
- El test que la OCDE usa como criterio de éxito quedó **implementado en el
  mismo día** (ver abajo).
- **Queda pendiente** el régimen socioeconómico para los otros tres cinturones.

## Más información

### Lo que hacen otros

**Handbook OCDE/JRC, paso 9** (el que este proyecto ya cita): correlacionar con
otros indicadores publicados —en plural— *y* «identificar vínculos mediante
regresiones». Nuestra implementación se había quedado con un par y un Pearson.

**Guías UNECE/ONU sobre indicadores compuestos (2019)** — parten la familia en
dos, y es la distinción que nos faltaba:

> «Los indicadores compuestos **económicos** normalmente tienen una serie de
> referencia, mientras que los **socioeconómicos** normalmente no la tienen.»

Y para los que no la tienen (§6.61): compararlos con **varias** estadísticas
relacionadas, y «las diferencias respecto de esas estadísticas **deben
explicarse** cuando el indicador se publica».

**Sistema de indicadores líderes de la OCDE**: hay una serie de referencia
designada y la validación **no es por correlación** sino por **puntos de giro**
—Bry-Boschan, adelanto, señales falsas—, con un criterio comparativo hacia
adentro: un compuesto debe dar menos señales falsas que cualquiera de sus
componentes.

**Precedente del caso incómodo**: el índice de situación de vida del SCP
holandés —el que las guías citan como práctica de referencia— valida su índice
objetivo contra medidas subjetivas de felicidad y **publica que explica apenas el
4% de su variación**. Relación débil, publicada como resultado.

### Dos cosas que hubo que hacer bien, y que la primera versión hizo mal

**1. La alternancia y la fase mínima tienen que converger juntas.** El primer
prototipo aplicaba la alternancia una vez y después el filtro de duración, que la
volvía a romper: producía secuencias valle-valle y pico-pico-pico, y con ellas un
«adelanto medio» calculado sobre giros que no eran giros. Por eso `alternan()` es
parte de la interfaz y se afirma en cada test.

**2. Los giros cerca de los extremos no se pueden confirmar.** Ahí la tendencia
se estima con una ventana incompleta. Sin tratarlo, una serie **monótona**
—sin ciclo alguno— devolvía giros: artefactos de amplitud ~0 nacidos de la
asimetría del borde. Se agregó amplitud mínima relativa y, sobre todo, la marca
de **provisorio**, que es como el sistema de la OCDE trata los giros recientes.

### Resultado, con lo que NO se puede afirmar por delante

| | |
|---|---|
| concordancia de fase ITCM ↔ actividad | **73%** de 30 meses (azar = 50%) |
| giros del ITCM desde dic-2023 | 3 (valle ene-2024 · pico ene-2025 · valle feb-2026) |
| de ésos, **provisorios** | **2** |
| confirmados | **1** |

**El adelanto no se puede estimar todavía**: un promedio sobre un giro confirmado
no es un promedio, y así se publica. La concordancia sí es utilizable hoy porque
usa los 30 meses y no sólo los giros.

Esto es además una mejora sobre lo que había: el par Pearson en niveles daba
+0,698 y no permitía distinguir co-movimiento de tendencia compartida. La
concordancia de fase es inmune a eso por construcción.

### Adenda (mismo día): el compuesto contra sus componentes

Era el pendiente declarado arriba, y es la pregunta que justifica construir un
índice en vez de mirar los indicadores sueltos. El criterio de la OCDE: el
compuesto debe dar **menos señales falsas y menos giros perdidos** que cualquiera
de sus partes.

- **señal falsa** = la serie gira y la referencia no lo hace cerca;
- **giro perdido** = la referencia gira y la serie no lo acompaña.

Resultado sobre el ITCM, contra el ciclo de la actividad:

| | señales falsas | giros perdidos | total |
|---|---|---|---|
| **ITCM (compuesto)** | **0** | **0** | **0** |
| `ipi_manufacturero` | 0 | 0 | 0 |
| `saldo_comercial_12m` | 0 | 0 | 0 |
| `costo_financiamiento_tesoro` | 1 | 0 | 1 |
| `idc` · `ipc_total` · `reservas_bcra` | 0 | 1 | 1 |
| … | | | |
| `presion_dolarizacion` | 3 | 3 | 6 |

De los **15 componentes** con historia suficiente: **13 se equivocan más, 2
empatan y ninguno lo supera.** El índice hace lo que un compuesto debe hacer.

Dos salvedades que van con el número:

- con 3 giros en la ventana, «cero y cero» es un resultado alcanzable por una
  muestra corta tanto como por un buen índice. Por eso se publica junto con el
  conteo de giros, no solo;
- la referencia es el Índice Líder, que es a su vez un compuesto de señales de
  actividad, así que los componentes de la dimensión de actividad (`emae_ia`,
  `ipi_manufacturero`) le quedan cerca por construcción. Que igual no lo superen
  es lo que da fuerza al resultado.

Un detalle de implementación que un test cuida: los giros de la referencia
**fuera del solape** no se cuentan como perdidos. Contarlos castigaría a un
indicador por no haber existido todavía, y con series que arrancan en fechas
distintas eso habría producido un ranking falso.
