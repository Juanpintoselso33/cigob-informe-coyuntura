---
madr: 4
id: '0411'
estado: 'aceptado'
fecha: 2026-10-29
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [alquiler_real, alquiler_udesa_real]
archivos: ['scripts/vida_cotidiana/collectors/ipc_alquiler.py', 'scripts/vida_cotidiana/collectors/alquiler_udesa.py', 'scripts/vida_cotidiana/cargar_alquiler_udesa.py', 'data/vida/alquiler_udesa.json', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/itvc.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_alquiler_udesa.py', 'tests/test_alquiler_original.py']
relacionado: ['0111', '0291', '0386']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Presión de precios'
origen: 'Decisión de Juan del 29-oct-2026: las dos tarjetas de alquiler muestran el alquiler real contra el 4T-2023, no una variación; la de UdeSA se reconstruye como nivel; abril de 2024 se carga con la cifra única del informe.'
---

# ADR-0411 — Los dos alquileres se leen como nivel real contra el 4T-2023

## Contexto y planteo del problema

La dimensión de precios tiene dos miradas al alquiler y las dos se publicaban
con una tarjeta que no decía lo que puntuaba. `alquiler_real` (alquiler del IPC
del Gran Buenos Aires) mostraba la variación mensual nominal, mientras el puntaje
salía de `itvc_alquiler`, el nivel relativo a los precios contra el 4T-2023
(ADR-0111). `alquiler_udesa_real` (avisos de UdeSA – Mercado Libre, ADR-0386)
mostraba una variación real interanual y puntuaba como 100 menos esa variación,
sin base común con los demás componentes. Quien leía la tarjeta no podía ver
cuánto se encareció el alquiler desde fines de 2023, que es lo que el puntaje
mide.

## Factores de decisión

- Que la tarjeta muestre lo mismo que puntúa, leído sin invertir.
- Una unidad común para los dos alquileres: índice, fines de 2023 = 100.
- No inventar lo que la fuente no dice: UdeSA publica variaciones, no niveles.
- El puntaje y los pesos no se tocan.

## Opciones consideradas

- **Nivel real contra el 4T-2023 en las dos tarjetas (elegida).**
- Mantener las variaciones y sólo corregir el rótulo.
- Rebasear UdeSA con el acumulado de las variaciones mensuales.

## Decisión

**`alquiler_real` (rótulo «Alquiler real (INDEC)»).** La tarjeta y su
serie pasan a `100 × (alquiler_t / alquiler_base) / (general_t / general_base)`,
con ambos del GBA y base el promedio oct–dic 2023. Por encima de 100 el alquiler
se encareció en términos reales. Es la misma cuenta que `itvc_alquiler`
(`100 × base / real`), de modo que tarjeta y puntaje siguen siendo una sola
medición vista de los dos lados. Tarjeta y serie comparten
`ipc_alquiler.indice_real` y el redondeo (dos decimales), por G3.

**`alquiler_udesa_real` (rótulo «Alquiler real (Universidad de San Andrés – Mercado Libre)»).** La fuente no
publica niveles; el nivel nominal es una **reconstrucción de CIGOB**, mes a mes en
orden cronológico (`alquiler_udesa.reconstruir_niveles`):

1. sep-2023 = 100.
2. Desde oct-2023, si la interanual nominal del mes está publicada y se conoce el
   nivel de t−12: `nivel(t) = nivel(t−12) × (1 + interanual)`.
3. Si no, y la intermensual está publicada y se conoce el nivel de t−1:
   `nivel(t) = nivel(t−1) × (1 + intermensual)`.
4. Si no, el mes queda sin nivel. No se imputa ni se interpola.

Se prefiere la interanual porque encadenar las mensuales da sistemáticamente
menos que las interanuales que el propio informe publica. El nivel real es
`100 × [nivel/base_nominal] / [IPC general GBA/base_IPC]`, con base el promedio
oct–dic 2023 de cada uno. La tarjeta es ese nivel; el componente es
`10.000 / real`, la misma construcción que el del IPC.

**Abril de 2024.** La intermensual estaba en blanco porque la frase no
distinguía departamentos de casas. Se leyó el PDF: da una sola cifra, 3,2 %, «de
departamentos y casas». Juan aprobó usarla (29-oct-2026). Noviembre de 2024 sigue
sin dato y la cadena se corta ahí: el nivel de los meses siguientes sólo vuelve
cuando hay interanual publicada (jun-2025, sobre jun-2024).

**Qué no cambia.** El puntaje de `alquiler_real`, los pesos (10 % y 10 % dentro
de precios), el rezago máximo y la carga manual mensual. ADR-0386 queda vigente
en todo lo demás.

### Consecuencias

- Con el snapshot del 29-oct-2026, sep-2026: `alquiler_real` 199,87 (antes
  1,88 % mensual) y `alquiler_udesa_real` 57,57. La serie reconstruida pasa por
  64,15 en sep-2024, 63,85 en sep-2025 y 57,57 en sep-2026 (nivel nominal 185,9,
  245,2 y 295,2: ×1,319 y ×1,204).
- El componente de UdeSA vale 173,7 en crudo y la winsorización de ADR-0033 lo
  deja en 140, el techo común. La dimensión de precios, con los otros tres
  componentes del ejemplo del test, pasa de 103,7 a 106,7. Antes el componente
  valía 109,8: el cambio de construcción hace que el alquiler de los avisos
  figure más barato de lo que decía, porque ahora se compara con fines de 2023 y
  no con el año anterior.
- La lectura es opuesta a la del IPC: contratos vigentes casi duplicaron su
  precio real; los avisos nuevos valen hoy menos que a fines de 2023. La ficha
  de cada uno lo dice.
- El tramo anterior a jun-2025 se arma encadenando mensuales, que acumulan error
  y quedan por debajo de las interanuales: es el menos firme de la serie, y los
  meses sin dato son huecos.
- La serie del componente deja de arrancar en jun-2025: tiene puntos desde
  oct-2023 hasta oct-2024 y desde jun-2025.

### Confirmación

`tests/test_alquiler_udesa.py` fija la regla de reconstrucción (interanual
primero, mensual de respaldo, sin imputar), la cadena con el registro real, la
cifra de abril de 2024 y la composición de la dimensión.
`tests/test_alquiler_original.py` fija la tarjeta del IPC contra el 4T-2023.
`tests/test_la_ficha_no_se_queda_atras.py` exige la entrada en `cambios` de las
dos fichas.

## Pros y contras de las opciones

- Nivel real en las dos: unidad común, la tarjeta dice lo que puntúa; UdeSA pasa
  a depender de una reconstrucción que hay que declarar.
- Sólo el rótulo: no cambia nada del cálculo, pero la tarjeta sigue sin mostrar
  el encarecimiento acumulado.
- Rebasear UdeSA con las mensuales: es la única forma sin interanuales, pero
  subestima el nivel; por eso sólo se usa donde no hay interanual.

## Más información

PDF de abril de 2024: https://drive.google.com/file/d/1csJrTs1G09VBZtxP64DTsqH72z_SDYvy/view
(la frase textual está en `data/vida/alquiler_udesa.json`).
