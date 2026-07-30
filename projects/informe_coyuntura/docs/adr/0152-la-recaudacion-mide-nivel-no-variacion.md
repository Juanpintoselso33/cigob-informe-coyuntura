# ADR-0152 — La recaudación pasa a medir NIVEL, y suma los impuestos provinciales

- **Estado**: Aceptado
- **Fecha**: 2026-07-29
- **Ámbito**: cinturón macro (ITCM), dimensión viabilidad fiscal-comercial
- **Reemplaza la métrica de**: ADR-0029 (promedio móvil 3 meses sobre la
  interanual) y mantiene la decisión de fuente de ADR-0127 (DGI, no total)
- **Relacionados**: ADR-0045 (cuándo se puede calibrar contra lo observado),
  ADR-0021 (puntaje interpolado), ADR-0072 (el indicador mide base imponible,
  no caja)

## Contexto

Dos pedidos del editor sobre el mismo indicador: sumar los impuestos
provinciales de la Comisión Arbitral, y subir la frecuencia. Al relevar la
fuente provincial apareció una tercera cosa, más de fondo, que el editor
señaló sin vueltas: **teniendo el dato mensual, la variación interanual no se
justifica.**

Tenía razón, y el argumento es fuerte por dos lados.

## 1. La interanual desperdiciaba el dato y arrastraba la base

La métrica anterior era la variación real contra el mismo mes del año anterior,
promediada sobre tres meses. Con el dato de junio de 2026 informaba **+3,3%**
—«creciendo»— porque la comparación era contra un 2025 deprimido. El nivel real
del mismo mes dice **88,2**, o sea **11,8% por debajo del 4T-2023**.

Las dos son ciertas. Para un índice de tensión la segunda es la que informa: la
pregunta no es «¿creció respecto de un mes cualquiera de hace un año?» sino
«¿cuánta base imponible real queda respecto del punto de partida?». Es además el
idioma que ya habla el ITVC entero (base 100 = 4T-2023).

Y hay un costo concreto que la interanual imponía: **necesita el año anterior en
cada punto.** Por eso el relevamiento de la fuente provincial incluyó
reconstruir 2022 — trabajo que un nivel rebaseado no habría necesitado, porque
le basta la base oct-dic 2023.

## 2. El nivel crudo no servía, y la corrección estacional sí

El nivel mensual crudo tiene **30,5 puntos** de amplitud entre el mes calendario
más alto y el más bajo: mayo (factor 1,182) y junio (1,119) concentran
vencimientos y aguinaldo, marzo es el piso (0,861). Publicar eso sería medir el
calendario tributario. **Ese es el motivo real por el que ADR-0029 había elegido
la interanual**, y no se puede ignorar.

La salida no es volver a la interanual sino desestacionalizar: cociente sobre
media móvil centrada de doce meses, factores promediados por mes calendario y
normalizados a promedio 1 para no inventar nivel. Estacionalidad residual:
**3,1 puntos**, una caída del 90%. Es el mismo criterio que el proyecto ya usa
en `itvc_ipi` e `itvc_isac`, que toman las series desestacionalizadas del INDEC;
acá hay que calcular los factores porque la fuente no las publica.

Comparación de las tres candidatas, desde dic-2023:

| métrica | rango | σ | resolución | valor jun-2026 |
|---|---|---|---|---|
| interanual pm3 (anterior) | 18,0 | 5,5 | diluida 12m | +3,3% |
| nivel real, promedio móvil 12m | 11,7 | 3,5 | diluida 12m | 92,7 |
| **nivel real desestacionalizado** | **26,8** | 4,9 | **mensual** | **88,2** |

La elegida gana en discriminación (rango 26,8 contra 18,0, criterio de ADR-0042)
**y** conserva la resolución mensual. El promedio móvil de 12 meses fue
descartado por lo mismo que la interanual: vuelve a diluir el dato mensual.

## 3. Lo provincial agrega información propia

La fuente es la gacetilla mensual de la Comisión Arbitral: SIFERE, SIRCREB,
SIRCAR, SIRTAC, SIRPEI y SIRCUPA. **No es recaudación provincial total** —cada
provincia recauda además de sus contribuyentes locales— y se declara así en la
ficha. Sobre la base medida aporta **15,5%**.

Contra la serie nacional, con las mismas transformaciones: **r = −0,274**, y
**18 de 28 meses con signo opuesto**. En 2024 el nacional recuperaba (+5%)
mientras el provincial caía (−19%); en el segundo semestre de 2025 se invirtió.

Se verificó que no fuera artefacto de cobertura, que era el riesgo obvio
—regímenes y jurisdicciones incorporándose inflan la base sin que cambie la
actividad—:

| serie | r vs nacional |
|---|---|
| total COMARB | −0,274 |
| **SIFERE solo** (núcleo, vigente desde antes de 2023) | **−0,254** |
| SIRCUPA (el único que rampea, +88% anual) | +0,452 |

SIFERE solo da la misma independencia que el total, y la composición es estable
en tres años (SIFERE 45,9%→42,6%, SIRCREB 27,7%→28,5%, SIRCAR 14,2%→14,5%).
SIRCUPA pesa 0,3%→1,2%: no puede mover el agregado.

## Decisión

1. `recaudacion` mide el **nivel de base imponible real desestacionalizada**,
   nacional (DGI) + provincial (COMARB) sumados en nivel, con **100 = promedio
   del 4T-2023**. Unidad publicada: `índice (100 = 4T-2023)`.
2. **Bandas nuevas**, porque las anteriores no eran traducibles: estaban
   ancladas al cero de una variación y el punto con significado de un nivel
   base-100 es el 100. Los cortes son pasos de diez puntos de esa base —unidad
   redonda y conceptual—: ≥110 → 100 · 100-110 → 85 · 90-100 → 60 · 80-90 → 35
   · <80 → 10. Fijadas sobre esa grilla y **no** sobre la distribución
   observada; ADR-0045 sólo autoriza calibrar contra lo observado si el extremo
   es inalcanzable, y no es el caso (la serie recorre 88,2 a 114,9).
3. **Una sola implementación del cálculo**, en `comarb.base_imponible_real_sa`.
   La card devuelve el último punto de la misma serie que publica
   `descargar_series`, así que no pueden divergir — G3 por construcción, misma
   disciplina que `apoyo_empresario`. Las dos usan `comarb.LIMITE_MESES`: los
   factores estacionales dependen de la ventana, así que dos ventanas distintas
   producirían dos series distintas.

## Efecto

| | valor | puntaje |
|---|---|---|
| antes (interanual) | +3,3% | 63,2 |
| ahora (nivel SA) | 88,2 | **43,0** |

**ITCM 63,0 → 61,5.** El indicador pesa 7,2% del índice. La caída del puntaje no
es un deterioro nuevo de la economía: es que la métrica anterior informaba
crecimiento contra una base deprimida mientras el nivel seguía bien por debajo
del punto de partida.

## Corroboración externa: la descomposición de la OPC

La Oficina de Presupuesto del Congreso publica en su Monitor de Recaudación
Tributaria Nacional la **variación real por principal determinante de la base
imponible**, que es una lectura independiente de lo mismo que mide este
indicador. Para jun-2026, variación real interanual:

| determinante | jun-2026 | ene-jun 2026 |
|---|---|---|
| Actividad | **−0,1%** | **−2,0%** |
| Masa salarial | −0,4% | −4,0% |
| Comercio exterior | −19,0% | −31,2% |
| Total | −4,5% | −4,8% |

Dos cosas quedan corroboradas por una fuente que no es la nuestra:

1. **La métrica anterior daba una lectura optimista.** Informaba +3,3%
   («creciendo») mientras la OPC ve los determinantes domésticos planos o
   negativos. El nivel en 88,2 es consistente con esa descomposición; la
   variación interanual no lo era.
2. **Excluir la aduana era correcto** (ADR-0127): comercio exterior −31,2% en el
   semestre contra actividad −2,0%. La brecha es el recorte de retenciones, no
   deterioro de la economía real.

## Consecuencias

- La serie **arranca en ene-2022** (54 puntos) contra 2023-03 de la anterior, y
  gana resolución mensual.
- **Dos propiedades incómodas que van declaradas en la ficha, no escondidas**:
  el indicador es más nervioso (jun-2026 cae 9,5 puntos contra may-2026, con
  3-4 observaciones por mes calendario todavía), y **revisa el pasado**, porque
  los factores estacionales se recalculan al acumular meses.
- **«Recaudación diaria»: no existe como serie publicada.** El pedido original
  la incluía y el relevamiento se cierra en negativo, con las consultas hechas
  para que nadie repita el camino: catálogo nacional de series (sólo mensual,
  trimestral y anual para «Principales subgrupos de recaudación tributaria»);
  informes de ARCA (mensual, trimestral, anual); página de Recaudación de
  Hacienda (XLSX mensuales desde 1997); y el Monitor de la OPC, que también es
  mensual. La coparticipación **sí** se transfiere a diario por ley 23.548, pero
  se publica agregada por mes — la serie RON que ya usa `iaf_transferencias`.
  Si alguna vez aparece, el indicador la aprovecha sin cambiar de métrica: el
  nivel desestacionalizado admite mayor frecuencia, la interanual no lo hacía
  igual de bien.
- **El Monitor de la OPC se publica como IMÁGENES** (`MRT_MM_AAAA_PageN.jpg`),
  sin planilla ni PDF con texto. Automatizarlo exigiría leer de píxeles, así que
  por ahora la corroboración de arriba se hizo a mano y queda fechada.
