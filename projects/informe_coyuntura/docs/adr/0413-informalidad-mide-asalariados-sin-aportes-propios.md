---
madr: 4
id: '0413'
estado: 'aceptado'
fecha: 2026-10-29
cinturon: 'vida'
indice: 'ITCIS'
indicadores: [informalidad]
archivos: ['scripts/informalidad_eph.py', 'scripts/vida_cotidiana/collectors/indec_series.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_informalidad_eph.py']
relacionado: ['0214', '0383']
ambito: 'Cinturón de impacto social · ITCIS · dimensión Empleo · componente informalidad'
origen: 'Decisión de Juan del 29-oct-2026: el indicador castigaba como informal a un trabajador registrado que factura con monotributo; pasa a la cifra oficial del INDEC, asalariados informales sin aportes propios.'
---

# ADR-0413 — La informalidad cuenta sólo al asalariado sin aportes propios

## Contexto y planteo del problema

`informalidad` medía el porcentaje de asalariados sin descuento jubilatorio
(serie `52.2_ASDJ_0_0_37` de la API de datos.gob.ar). Esa cifra mete en la misma
bolsa al asalariado en negro y al que no tiene descuento porque se paga sus
aportes por su cuenta, con monotributo o como autónomo: un trabajador registrado
que factura figuraba como informal. Desde el 4T-2023, por el cambio de
cuestionario, el INDEC publica la separación entre los informales **con** y
**sin** aportes propios.

## Factores de decisión

- Que el indicador mida lo que su nombre dice (regla del tablero).
- Cifra oficial del INDEC, automática y reproducible.
- Mantener la construcción y la base (4T-2023 exacto) del componente.
- El rezago se mide, no se copia.

## Opciones consideradas

- **Asalariados informales sin aportes propios, de las planillas del INDEC
  (elegida).**
- Seguir con el total sin descuento jubilatorio: castiga al que factura.
- Restar a mano los monotributistas con otra fuente: no es la cifra oficial y
  mezcla universos (SIPA y EPH).

## Decisión

**Qué se mide.** Porcentaje de asalariados sin descuento jubilatorio que tampoco
se paga sus aportes por su cuenta, EPH, 31 aglomerados, trimestral. La fecha de
cada punto es el inicio del trimestre.

**Fuentes** (`scripts/informalidad_eph.py`, dos planillas Excel del INDEC, sin
clave ni API):

1. Planilla de informalidad laboral,
   `cuadros_informalidad_laboral_eph_MM_AA.xlsx`, cuadro 4.1: la cifra oficial
   desde el 4T-2023. Se publica una vez al año (abril) y hoy llega al 4T-2025.
2. Planilla del informe de mercado de trabajo,
   `cuadros_tasas_indicadores_eph_MM_AA.xls` (MM = 03, 06, 09 o 12), cuadro 1.5:
   trae, por trimestre, el porcentaje de asalariados sin descuento jubilatorio y
   cuántos de ellos tienen y no tienen aportes propios. Con esto se calcula
   `informales × proporción sin aportes propios` para los trimestres que la
   planilla anual todavía no cubre.

La planilla anual manda donde existe; el cálculo sólo rellena lo posterior y la
planilla del año siguiente lo reemplaza. No se empalma en el medio porque los
dos cálculos difieren unas décimas (la planilla anual deja afuera a los
informales sin dato de aportes y eso cambia el denominador: 4T-2025 da 30,3 en
la planilla y 30,6 por la cuenta).

**Valores verificados** (planilla anual): 4T-2023 30,0 · 1T-2024 30,0 · 2T-2024
30,4 · 3T-2024 30,5 · 4T-2024 29,9 · 1T-2025 29,8 · 2T-2025 31,6 · 3T-2025 31,3 ·
4T-2025 30,3. Calculados con el informe de septiembre de 2026: 1T-2026 32,0
(37,9 × 84,5 %) y 2T-2026 31,9 (37,9 × 84,1 %), coincidente con el cálculo del
informe de prensa del 17-sep-2026.

**Errata de la fuente.** La planilla del informe trae en el 2T-2025 un 62,3 %
«con aportes propios» (el porcentaje de formales en la fila equivocada). El
lector descarta toda proporción con aportes propios fuera de 3-40 % o que no
sume 100, en vez de dejarla entrar a la serie; ese trimestre queda cubierto por
la planilla anual.

**Rezago.** Medido en la fuente: el 2T-2026 salió el 17-sep-2026, 169 días
después del inicio del trimestre; al ciclo siguiente suma unos 260. El tope de
280 días de `config.MAX_DIAS` alcanza y no cambia.

**Construcción del componente.** Igual que antes: `rebase_de_serie`, invertido,
con base en el 4T-2023 exacto (30,0). El índice pasa de 94,2 a 94,0 con los
datos de hoy. La card muestra el último punto de la serie (gate G3).

**Peso.** No cambia: 0,3419 dentro de Empleo (ADR-0383).

### Consecuencias

- La card baja de ~38 % a ~32 %: no es una mejora, es otra definición. El
  rótulo público lo dice.
- El componente casi no se mueve porque la base cambia en la misma proporción.
- Los meses del archivo se releen con el método vigente (ADR-0359).
- Si el INDEC cambia el nombre de las planillas, el lector falla en voz alta y
  el pipeline cae a la caché con aviso.

### Confirmación

`tests/test_informalidad_eph.py` prueba el parseo de las dos planillas, la
guarda de la errata, el empalme y el valor de la card sin red;
`tests/test_la_ficha_no_se_queda_atras.py` exige la ficha.

## Pros y contras de las opciones

- Elegida: cifra oficial, no castiga al que factura; el valor reciente es un
  cálculo hasta que sale la planilla anual.
- Total sin descuento: serie larga y de API, pero mide otra cosa.
- Restar monotributistas con otra fuente: no es oficial.

## Más información

Argumento en contra, recogido en la ficha: el asalariado que factura cotiza,
pero no tiene vacaciones pagas ni indemnización por despido.
