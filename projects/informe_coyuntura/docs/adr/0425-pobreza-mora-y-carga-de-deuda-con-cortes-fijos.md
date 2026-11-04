---
madr: 4
id: '0425'
estado: 'aceptado'
fecha: 2026-11-04
cinturon: 'vida'
indice: 'ITVC'
indicadores: [pobreza_nowcast, mora_familias, carga_servicio_deuda_hogares]
archivos: ['scripts/itvc.py', 'scripts/descargar_series.py', 'scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts']
relacionado: ['0153', '0067', '0231', '0235', '0367', '0424']
ambito: 'ITCIS · ingresos (`pobreza_nowcast`) y vulnerabilidad financiera (`mora_familias`, `carga_servicio_deuda_hogares`)'
origen: 'Revisión de Luis del 3-nov-2026 (pobreza con cortes fijos, verde ≤ 15; mora y carga con análisis comparado). Juan, 4-nov: verde de pobreza en 20 y los demás corridos; mora y carga como la propuesta.'
---

# ADR-0425 — Pobreza, mora y carga de la deuda con cortes fijos

## Contexto y planteo del problema

Los tres se leían contra fines de 2023 ([[0153]], [[0067]], [[0231]]), una base que engaña
en los tres: la pobreza del 2º semestre de 2023 (41,7 %) era de crisis, así que cualquier
mejora salía verde (31,3 % daba 133,2); y en 2023 casi no había crédito, así que la mora y
la carga eran bajas por eso (la mora de hoy daba 17,1 y la carga 42,3, fuera de escala).

## Factores de decisión

- Niveles que un lector reconozca, como la inflación con los cortes de Luis ([[0367]]).
- Referencias externas citables: la región para la pobreza, países con crédito de consumo
  para la mora y la carga.

## Opciones consideradas

- **Cortes fijos en la escala común del ITCIS (elegida).**
- Mantener la base 4T-2023 y aclararlo en la ficha: el color seguiría diciendo lo contrario
  de lo que dice el nivel.

## Decisión

Cortes (menos es mejor; verde hasta, amarillo hasta, naranja hasta; arriba, rojo):

- Pobreza: 20 · 30 · 40 %. Verde = la región (Uruguay 16,6 %, Paraguay 16,0 %, Chile
  17,3 %); amarillo hasta lo mejor de la Argentina reciente (25,7 % en 2017, 28,2 % en el
  2S-2025); naranja, 2019-2023; rojo, crisis. Luis había propuesto verde ≤ 15; Juan lo
  corrió a 20.
- Mora de las familias: 5 · 8 · 12 %. Consumo a 90 días en Chile, México, Colombia, Perú y
  Uruguay: 2,5-5,5 %; récord de Brasil, 8,1 %; Argentina con crédito (2011-2019), 2-4 %.
- Carga del servicio de la deuda: 15 · 20 · 30 % de la masa salarial. 20 % es el mínimo
  reciente de Brasil y 30 % el umbral de sobreendeudamiento de la literatura (récord
  brasileño, 29,7 %).

`itvc.indice_por_cortes` lleva el valor a la escala común con los cortes en los bordes de
color (índice 105, 95 y 85 = tensión 4, 6 y 8), lineal entre cortes y con la pendiente del
tramo vecino hacia los extremos (125 y 75). La card, la serie `itvc_pobreza` y la
reconstrucción de `validacion_externa` usan la misma función; la card publica los tramos en
la unidad del indicador. La pobreza deja de necesitar la base del INDEC ([[0424]]).

### Consecuencias

- Con los datos del 4-nov-2026: pobreza 133,2 → 93,7 (verde → naranja); mora 17,1 → 78,4
  (sigue roja); carga 42,3 → 90,9 (roja → naranja).
- La carga es la más floja: sus referencias usan ingreso disponible y no masa salarial, y no
  hay serie argentina previa para contrastar.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_itvc_cortes_fijos.py` fija los bordes de color y que card, serie y
reconstrucción usen la misma función.

## Pros y contras de las opciones

- Cortes fijos: el color dice lo que dice el nivel; las referencias son de otros países.
- Base 4T-2023: comparable con el arranque del mandato, pero con una base atípica.

## Más información

Informes de los relevamientos del 4-nov-2026 (pobreza regional, mora y carga comparadas) en
la conversación de esa fecha; resumen en `docs/pendientes-monitor.md`, ítems 11, 15 y 16.
