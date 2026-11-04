---
madr: 4
id: '0421'
estado: 'aceptado'
fecha: 2026-11-03
cinturon: 'macro'
indice: 'ITCM'
indicadores: [actividad_tributaria]
archivos: ['scripts/itcm.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
supersede: ['0368']
relacionado: ['0329', '0404', '0072', '0387']
ambito: 'ITCM · dimensión Cuentas fiscales · `actividad_tributaria`'
origen: 'Juan, 3-nov-2026: «sumémoslo de vuelta, esta vez en cuentas fiscales». Luis, revisión del mismo día: «su peso y una escala con cortes de la historia anterior al Gobierno lo calcula la IA».'
---

# ADR-0421 — La recaudación de IVA y cheque vuelve, en cuentas fiscales

## Contexto y planteo del problema

[[0368]] sacó `actividad_tributaria` (IVA-DGI + impuesto al cheque, % i.a. real) del
índice porque, dentro de actividad, repetía al EMAE. Se siguió calculando. El 3-nov-2026
Juan pidió que vuelva como lectura fiscal, en cuentas fiscales, y Luis delegó el peso y la
escala, con cortes de la historia anterior al Gobierno como el resto ([[0404]]).

## Factores de decisión

- El resultado primario sigue liderando la dimensión ([[0072]]).
- IVA y cheque son 30-62 % del agregado DGI que ya puntúa `recaudacion`: comparten
  materia prima, aunque la correlación entre las dos lecturas es baja (0,28 en 45 meses,
  porque `recaudacion` puntúa un nivel desestacionalizado).
- Cortes de la historia previa, no del mandato.

## Opciones consideradas

- **50 / 30 / 20 (resultado primario / recaudación / IVA + cheque) (elegida).**
- 50 / 25 / 25: trata a las dos lecturas de la base imponible igual, sin descontar lo que
  comparten.
- Sumar peso a la dimensión: cambiaría el reparto entre dimensiones, que nadie pidió.

## Decisión

Cuentas fiscales mantiene su 19,2 % del índice y reparte 50 % resultado primario, 30 %
recaudación y 20 % IVA + cheque (9,6 %, 5,76 % y 3,84 % del índice). La escala sigue a la
del crédito privado de [[0404]]: centro en 0 y cortes en uno y dos desvíos de dic-2017 a
nov-2023 (72 meses; desvío 10,7 pp, media 1,5 %), con los mismos puntajes de tramo
(10 · 25 · 45 · 65 · 85 · 100). Anclas: −21,4 → 10 · −16,05 → 25 · −5,35 → 45 ·
5,35 → 65 · 16,05 → 85 · 21,4 → 100.

### Consecuencias

- Con el 0,86 % de septiembre de 2026, el indicador puntúa en la zona de 65.
- El resultado primario baja de 12 % a 9,6 % del índice y la recaudación de 7,2 % a 5,76 %.
- Es método: llega a la edición mensual y al archivo.

### Confirmación

`tests/test_macro_actividad_tributaria.py` exige que puntúe en cuentas fiscales con estas
bandas; los tests de pesos corren con la composición nueva.

## Pros y contras de las opciones

- 50/30/20: descuenta el solapamiento con la recaudación; es una convención.
- 50/25/25: más simple, pero cuenta dos veces parte del mismo agregado.

## Más información

La historia empieza en dic-2017 porque antes no hay IPC nacional comparable para
deflactar ([[0329]]).
