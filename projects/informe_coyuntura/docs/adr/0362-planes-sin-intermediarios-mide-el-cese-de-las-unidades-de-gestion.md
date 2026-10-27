---
madr: 4
id: '0362'
estado: 'aceptado'
fecha: 2026-10-24
cinturon: 'gestion'
indice: 'ITCG'
indicadores: [asistencia_directa]
archivos: ['scripts/gestion.py', 'scripts/descargar_series.py', 'scripts/itcg.py', 'scripts/procedencia_anclas.py', 'data/gestion/manuales.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts', 'tests/test_asistencia_directa.py']
relacionado: ['0015', '0189', '0361', '0371']
ambito: 'Cinturón de gestión · ITCG · dimensión reforma social y orden'
origen: 'Observación #11 de la auditoría externa del cinturón de Gestión (23-oct-2026) y decisión de Juan del 24-oct-2026 (opción a).'
---

# ADR-0362 — «Planes sin intermediarios» mide el cese de las unidades de gestión

## Contexto y planteo del problema

`asistencia_directa` pesa 40 % de la dimensión de reforma social y orden, 4 %
del índice de gestión. Medía la TDPS: qué porcentaje del devengado de los
programas sucesores del Potenciar Trabajo se clasifica como ayudas a personas
(partida 5.1.4). Esa tasa ya era **98,3 %** en 2023, así que el indicador le
daba 100 al gobierno por algo que estaba hecho antes del mandato
([[0189-si-no-puntua-no-se-muestra]] ya lo dejaba como calibración pendiente).

La auditoría externa ([[0361-respuesta-a-la-auditoria-del-cinturon-de-gestion]])
lo señaló: la intermediación del Potenciar Trabajo no estaba en quién cobraba,
sino en las **unidades de gestión**. Eran los municipios, cooperativas y
organizaciones que certificaban la contraprestación y manejaban la lista.

## Factores de decisión

- Un indicador tiene que medir lo que su nombre dice.
- Lo que cambió con este gobierno tiene que poder verse; lo que ya estaba, no
  tiene que sumar.
- Sólo datos publicados y verificables.

## Opciones consideradas

- Mantener la TDPS (puntúa 100 sobre un tramo ya andado).
- Medir el porcentaje de las transferencias de Desarrollo Social que va a
  organizaciones (4,4 % → 1,4 % → 3,3 %). Lo que queda ahí son casi todo
  comedores, no planes, y la serie vuelve a subir.
- Sacar el indicador del índice: ya se hizo una vez y se revirtió con el
  argumento de que una promesa cumplida tiene que contar
  ([[0189-si-no-puntua-no-se-muestra]]).
- **Medir el hito del cese de las unidades de gestión (elegida).**

## Decisión

El indicador pasa a llamarse «Planes sin intermediarios». Vale **100 desde el
10 de abril de 2024** y **0 antes**.

- **La norma:** el artículo 6 de la Resolución 84/2024 del Ministerio de Capital
  Humano dispuso «el cese de las actividades de las Unidades de Gestión y de las
  Unidades de Certificación» del Potenciar Trabajo. Los considerandos lo
  justifican para implementar los programas nuevos «de manera directa y
  transparente, eliminando la intermediación». Verificado en el Boletín Oficial,
  aviso 305588.
- **La serie:** se reconstruye desde diciembre de 2023, evaluada al cierre de
  cada mes. Abril de 2024 ya vale 100.
- **Las bandas** no cambian. Con un valor binario se usan sus extremos: 100
  puntúa 100 y 0 puntúa 10.
- **La TDPS** queda como contexto en el detalle de la tarjeta, sin puntuar.

### Consecuencias

- El valor de hoy y el puntaje de hoy no cambian (100).
- La serie histórica del índice de gestión sí cambia. De diciembre de 2023 a
  marzo de 2024, este indicador pasa de alrededor de 98 (puntaje 100) a 0
  (puntaje 10). Medido en la corrida del 24-oct: diciembre de 2023 baja de
  18,7 a 12,7 y enero a marzo de 2024, 1,8 puntos cada mes. Desde abril de
  2024 no cambia nada. La evolución muestra una mejora que antes no se veía.
- Por ser método, el cambio se ve también en la edición mensual y en el archivo
  ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).

### Confirmación

`tests/test_asistencia_directa.py`:
- la fecha exacta del cese;
- la serie con marzo en 0 y abril en 100;
- que la tarjeta no dependa de la API de Presupuesto Abierto y coincida con el
  último punto de la serie (G3).

## Pros y contras de las opciones

- TDPS: automática y mensual, pero no mide la intermediación.
- Transferencias a organizaciones: se mueve, pero mide comedores.
- Sacarla: honesto con la falta de recorrido, pero deja sin medir una promesa
  cumplida.
- Hito: mide exactamente el cambio que hizo este gobierno. Es grueso (0 o 100)
  y no detecta solo una vuelta atrás; eso queda declarado como limitación.

## Más información

[[0015-tdps-presupuesto-abierto]] creó la TDPS.
