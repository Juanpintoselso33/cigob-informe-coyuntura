---
madr: 4
id: '0418'
estado: 'aceptado'
fecha: 2026-11-02
cinturon: 'transversal'
indice: 'ITVC'
indicadores: [ipc_alimentos, brecha_salario_cbt]
archivos: ['scripts/indec_api.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'web/src/lib/fichas.ts', 'tests/test_indec_api.py']
relacionado: ['0417', '0291', '0275', '0413']
ambito: 'Todo lo del INDEC que llegaba atrasado por la copia de datos.gob.ar y que su API tiene igual: IPC (nivel, núcleo, regulados, alimentos, vivienda) y canastas básicas'
origen: 'Juan, 2-nov-2026, después de ADR-0417: «pasá todo retrasado, todo lo que haya».'
---

# ADR-0418 — IPC y canastas desde la API del INDEC

## Contexto y planteo del problema

ADR-0417 pasó el EMAE y los salarios a la API del INDEC. El 2 de noviembre de 2026 se
inventariaron las 79 series de datos.gob.ar que usa el Monitor: 48 son del INDEC. Para cada una
se comparó la copia con la API en todos los meses comunes.

## Factores de decisión

- Pasa sólo lo que la API publica **igual** (misma serie, mismo valor) y **antes** que la copia.
- Lo que no es igual no pasa aunque la API llegue antes: cambiaría lo que mide el indicador.

## Opciones consideradas

1. Pasar a la API las series que son iguales y más frescas.
2. Pasar todo lo que la API tenga parecido.

## Decisión

Opción 1. Pasan siete series, todas iguales a la copia y un mes más frescas (septiembre contra
agosto): IPC nacional nivel general, núcleo, regulados, alimentos y bebidas, y vivienda (base
dic-2016), y CBA y CBT por adulto equivalente de GBA. Van por el mismo mecanismo de ADR-0417.

Quedan como están, cada una por un motivo medido:

| Serie | Motivo |
|---|---|
| Exportaciones e importaciones totales (`74.3_IET`, `74.3_IIT`) | La suma de la API no da el total oficial: deja afuera las celdas ocultas por secreto estadístico y difiere hasta 2 % (agosto 2026: 8.865,9 contra 8.882,6 M USD). Los meses nuevos ya salen del cuadro oficial del ICA (ADR-0275). Bienes de capital sí coincide, pero ya se completa igual. |
| EPH: empleo, desocupación, subocupación demandante | Llegan al mismo trimestre que la copia, y la API redondea a un decimal (la copia trae más). |
| Pobreza (`64.2`) | Mismo semestre que la copia. |
| Tasa de empleo informal de la API | Otra definición que la de `informalidad` (ADR-0413). |
| IPC-GBA alquiler y nivel general (`104.1`, `103.1`) | La tarjeta ya sale de la planilla oficial (ADR-0291); la copia del alquiler, además, no coincide con el INDEC. |
| IPI, ISAC | Ya salen de las planillas, al día. |
| Autoservicios, centros de compras, pasajeros, cuenta corriente, términos del intercambio | No están en la API. |

### Consecuencias

- Bien: `ipc_alimentos` (alimentos contra general) avanza un mes. El general ya llegaba a
  septiembre por la planilla, pero alimentos no, y el cociente sólo se calcula con los dos del
  mismo mes.
- Neutro: `brecha_salario_cbt` toma la CBT de la API, pero se alinea por mes común con el RIPTE,
  así que avanza cuando avanza el salario.
- Bien: núcleo, regulados y vivienda (gráficos y vida cotidiana) también llegan a septiembre.

### Confirmación

`tests/test_indec_api.py::test_ipc_y_canastas_apuntan_a_la_apertura_correcta` fija a qué
apertura de la API corresponde cada id. La comparación contra la copia dio diferencias máximas de
4×10⁻⁴ (IPC general, abril de 2019, redondeo) y de 2×10⁻⁵ (CBA).

## Pros y contras de las opciones

### Sólo lo igual y más fresco

- Bien: ningún indicador cambia de definición.
- Mal: quedan series atrasadas que la API no tiene.

### Todo lo parecido

- Mal: los totales de comercio y la informalidad medirían otra cosa sin que el rótulo cambie.

## Más información

Relevamiento de lo que se había descartado por falta de dato en los ADR: casi toda la falta de
datos del Monitor es de organismos que no son el INDEC. De la API, ningún ADR descartó canasta de
crianza, precios mayoristas, costo de la construcción, IPI minero, exportaciones por destino ni
proyecciones de población: nunca se evaluaron.
