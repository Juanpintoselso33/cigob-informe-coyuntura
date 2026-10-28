---
madr: 4
id: '0402'
estado: 'aceptado'
fecha: 2026-10-28
cinturon: 'politica'
indice: 'ITCP'
indicadores: [alineamiento_senadores_prov]
parametros: ['ANCLAS_ITCP["alineamiento_senadores_prov"]', 'BANDAS_ITCP["alineamiento_senadores_prov"]']
archivos: ['scripts/itcp.py', 'scripts/procedencia_anclas.py', 'scripts/sensibilidad.py', 'tests/test_itcp.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts']
modifica: ['0038']
relacionado: ['0038', '0400', '0401']
ambito: 'ITCP · dimensión Alianzas territoriales · anclas del alineamiento de senadores por provincia'
origen: 'Auditoría del cinturón político del 28-oct-2026; decisión de Juan del mismo día.'
---

# ADR-0402 — El alineamiento de senadores se compara con la historia

## Contexto y planteo del problema

Las anclas 40/50/60/70 de [[0038]] se calibraron con la serie del propio mandato
(feb-2024 a jun-2026): toman como normal lo que hace este Senado. Medido igual —con los
senadores de otros bloques frente al oficialismo de cada gobierno, ventana de 90 días,
promedio entre provincias— en las actas del portal desde 2012, los tres gobiernos
anteriores dan: Fernández de Kirchner 2012-2015 73,5; Macri 2015-2019 78,1 con
Cambiemos (81,9 con el bloque PRO solo); Fernández 2019-2023 81,4. Juntos, 134 meses:
mediana 77, media 77,7, desvío 11,3. El mandato actual promedia unos 58: casi dos
desvíos por debajo. Con las anclas de [[0038]], un 70 —todavía por debajo de la mediana
de la historia— ya daba el puntaje máximo.

## Factores de decisión

- El ancla superior no puede salir del período que se mide.
- Una sola historia previa no alcanza para fijar cuatro cortes: el piso y el medio
  tienen lectura propia.

## Opciones consideradas

- **Anclas mixtas: dos conceptuales y una de historia (elegida).**
- Media y desvíos de la historia en las cuatro anclas.
- Umbrales del Senado (tercio, mitad, dos tercios) según las bancas propias.
- Mantener [[0038]].

## Decisión

Anclas en `ANCLAS_ITCP["alineamiento_senadores_prov"]`, interpoladas en línea recta:
**25 → 10** (coincide un cuarto o menos de los votos ajenos) · **50 → 65** (coincide la
mitad) · **77 → 100** (la mediana de los tres gobiernos anteriores). `BANDAS_ITCP` repite
los cortes 25/50/77 con el puntaje de su ancla inferior, para el color y la ficha. El
motor del ITCP pasa a leer `ANCLAS_ITCP` (`calcular_itcp`, y `sensibilidad.py` para la
robustez), igual que el ITCM con `ANCLAS_ITCM`.

### Consecuencias

- Con el valor de hoy (56,5, el mismo que antes de [[0400]]), el puntaje pasa de 68,0 a
  73,4: el 50 → 65 es más generoso que el 55 → 65 de antes y el techo se aleja. Pesa
  6,1 % del ITCP: unos +0,3 puntos.
- Serie recalculada en memoria (con los pases de [[0400]]), feb-2024 a oct-2026: los meses
  en el piso bajan de 4 a 1 (ago-2025, 16,7) y los meses en 100 de 7 a 4 (feb-2024,
  dic-2024, ene-2025 y may-2026). Los meses de fines de 2025, cuando el oficialismo
  quedó más solo, suben (sep-2025 de 10 a 24,7; nov-2025 de 39,4 a 52,5): con 25 → 10
  sólo un cuarto de coincidencia o menos es el piso.
- La procedencia pasa de convención a historia larga: la circularidad del ITCP baja
  (techo a 0,09, junto con [[0401]]).
- La historia usa el bloque del portal en esos períodos (los pases no están corregidos
  como en el mandato actual); va en la ficha.

### Confirmación

`tests/test_itcp.py` fija las tres anclas, que la tabla repita sus cortes y el puntaje de
valores intermedios; `tests/test_fichas_bandas.py` cruza la ficha con el motor;
`tests/test_procedencia_anclas.py`, el techo de circularidad.

## Pros y contras de las opciones

- Mixtas: el techo es la historia y el piso tiene lectura propia; el medio (50 → 65) es
  una convención declarada.
- Media y desvíos: todo historia, pero con una desviación de 11 puntos el piso caería
  cerca de 55 y la mitad del mandato quedaría en 10.
- Umbrales del Senado: miden mayorías de la cámara, no coincidencia de votos ajenos, y
  se mueven con las bancas propias.
- [[0038]]: el techo lo fija el propio gobierno medido.

## Más información

Análisis del 28-oct-2026 con las actas del Senado de 2012 a 2026.
