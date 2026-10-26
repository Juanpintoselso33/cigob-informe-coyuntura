---
madr: 4
id: '0364'
estado: 'aceptado'
fecha: 2026-10-26
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [reduccion_estado]
archivos: ['scripts/itcg.py', 'scripts/procedencia_anclas.py', 'web/src/lib/fichas.ts', 'tests/test_itcg.py']
relacionado: ['0121', '0361']
ambito: 'Cinturón de gestión · ITCG · dimensión Reforma del Estado'
origen: 'Observación #6 de la auditoría externa del cinturón de Gestión (23-oct-2026) y decisión de Juan del 26-oct-2026 (opción B).'
---

# ADR-0364 — La dotación del Estado se mide contra la meta de 2026

## Contexto y planteo del problema

La dimensión Reforma del Estado daba 100/100. La auditoría externa
([[0361-respuesta-a-la-auditoria-del-cinturon-de-gestion]]) objetó que eso se lee
como reforma completa. Al revisar de dónde salían las metas apareció el problema
de fondo: `reduccion_estado` daba 100 desde −12 %, un corte calibrado con el
recorte que se estaba observando (convención circular, ver
[[0121-itcg-e-itcp-declaran-el-origen-de-sus-bandas]]). Hoy la dotación está en
−21,4 % contra diciembre de 2023.

## Factores de decisión

- La vara tiene que venir de afuera del dato que mide.
- No inventar una meta: sólo referencias con fuente.

## Opciones consideradas

- Dejar las metas y aclarar su origen en la tarjeta.
- **Usar la meta de recortar otro 10 % de la planta en 2026 (elegida).**
- La reforma de 1989-1999 (−69 %): mezcla privatizaciones con recortes y su
  fuente es una revista.
- Promedios de la OCDE: miden el gobierno general con provincias, no la
  Administración Pública Nacional.

## Decisión

El 100 de `reduccion_estado` pasa a **−25,7 %** contra diciembre de 2023.

- **La meta:** recortar otro 10 % de la planta durante 2026. La informó la prensa
  citando fuentes oficiales (Clarín, vía Cadena 3); el Gobierno no publicó un
  número y evitó confirmarlo. Ni el Presupuesto 2026 ni el acuerdo con el FMI
  (revisión de agosto de 2025) fijan una meta de planta.
- **La cuenta:** en diciembre de 2025 la dotación estaba 17,45 % por debajo de
  diciembre de 2023; 0,8255 × 0,9 = 0,743 → −25,7 %.
- **Las bandas:** conservan la forma anterior (−12/−8/−4/0) estirada a esa meta:
  ≤ −25,7 → 100 · −25,7 a −17,1 → 85 · −17,1 a −8,6 → 65 · −8,6 a 0 → 40 ·
  > 0 → 10.
- **La procedencia** pasa de `convencion` a `externa`, con la salvedad de que la
  fuente es periodística.
- **Gasto de funcionamiento** no cambia: no se encontró ninguna referencia
  externa, y queda declarado como convención.

### Consecuencias

- Con −21,4 % el indicador baja de 100 a 85 y la dimensión Reforma del Estado, de
  100 a cerca de 91. El índice de Gestión baja en consecuencia.
- Por ser método, el cambio llega a la edición mensual y al archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).
- Si el Gobierno publica una meta oficial, reemplaza a ésta.

### Confirmación

`tests/test_itcg.py` fija los nuevos cortes de banda de `reduccion_estado`.

## Pros y contras de las opciones

- Dejar las metas: no mueve el índice, pero sigue siendo circular.
- Meta de 2026: viene de afuera del dato y es la única referencia numérica del
  propio Gobierno; es una filtración de prensa, no un documento.
- Reforma de los noventa y OCDE: no comparables.

## Más información

Cadena 3, «El Gobierno nacional planea reducir un 10% del personal estatal para
2026». FMI, Country Report 25/219 (agosto de 2025).
