---
madr: 4
id: '0417'
estado: 'aceptado'
fecha: 2026-11-02
cinturon: 'transversal'
indice: 'ITCM'
indicadores: [emae_ia, emae_difusion]
archivos: ['scripts/indec_api.py', 'scripts/datos_gob.py', 'scripts/macro.py', 'scripts/descargar_series.py', 'web/src/lib/fichas.ts', 'tests/test_indec_api.py', 'tests/conftest.py', '.github/workflows/data-pipeline.yml']
relacionado: ['0124', '0256']
ambito: 'Fuente del EMAE (nivel general y 15 sectores) y del índice de salarios: la API del propio INDEC en lugar de la copia de datos.gob.ar'
origen: 'Juan, 2-nov-2026: «fijate la nueva api de indec a ver si nos sirve» y, visto el relevamiento, «cargalo y arrancá con EMAE y salarios».'
---

# ADR-0417 — EMAE y salarios desde la API del INDEC

## Contexto y planteo del problema

El INDEC abrió en 2026 su propia API, el Catálogo API-INDEC (`https://api.indec.gob.ar`, en
beta): 19 servicios en JSON, con filtros por columna, que piden una cuenta y un token. Hasta
ahora el EMAE y el índice de salarios llegaban al Monitor por la API de series de datos.gob.ar,
que es una copia. Medido el 2 de noviembre de 2026:

| Serie | API del INDEC | Copia de datos.gob.ar |
|---|---|---|
| EMAE (nivel y sectores) | agosto 2026 | julio 2026 |
| Índice de salarios | agosto 2026 | julio 2026 |

En los meses comunes las series son las mismas; las diferencias están todas en 2026 y son la
revisión que el INDEC publicó con agosto y que la copia no tiene (hasta 0,06 pp en la variación
interanual del EMAE de marzo). El IPC ya había dejado la copia por el mismo atraso (se completa
desde la planilla) y supermercados también (ADR-0256).

## Factores de decisión

- La card tiene que mostrar el último dato que publicó el INDEC, no el que replicó la copia.
- Los colectores no deberían cambiar: la serie es la misma, sólo cambia de dónde se lee.
- Un token vencido no puede degradar la card sin que nadie se entere.

## Opciones consideradas

1. Leer esas series de la API del INDEC, con la copia como respaldo si la API no responde.
2. Leerlas de las planillas Excel del INDEC, como el IPC y el IPI.
3. Seguir con la copia de datos.gob.ar.

## Decisión

Opción 1. `scripts/indec_api.py` responde los pedidos de 19 ids de datos.gob.ar (variación
interanual del EMAE, los 15 sectores, y salarios nivel general, total registrado y sector
público) desde la API del INDEC, con la misma forma y las mismas unidades: la variación del EMAE
viene en % y se pasa a fracción, y los salarios vienen como texto con coma decimal.
`datos_gob.get` deriva ahí esos pedidos, el mismo punto donde el IPC ya se completa desde la
planilla, así que `macro.py`, `descargar_series.py` y vida cotidiana no cambian.

- **Token rechazado** (401/403) o variable vacía en la corrida: `TokenRechazado`, sin volver a
  la copia. La card queda desactualizada y el mensaje no se parece a un error de red, así que
  `aviso_slack` lo avisa en la primera corrida y no en la tercera.
- **API caída por otra causa**: se lee la copia y queda en el log. La fuente de la card dice de
  cuál salió (`indec_api.via`).
- **Sin la variable** (local sin `.env`, pytest): ni se intenta.

El token es `INDEC_API_TOKEN`, en el `.env` y como secreto del repo, pasado al paso de
colectores. **Vence a los 6 meses** (el primero, el 1 de mayo de 2027), no a los 12 que dice la
ayuda del INDEC: se regenera desde «Gestionar la cuenta» en api.indec.gob.ar.

### Consecuencias

- Bien: `emae_ia` y `emae_difusion` llegan a agosto un mes antes; agosto da −1,74 % y 5 de 15
  sectores creciendo, contra −1,44 % y 7 de 15 de julio.
- Bien: los meses de 2026 toman la revisión vigente del INDEC.
- Mal: una credencial más que vence, y una API en beta. La copia queda como respaldo.
- Neutro: el índice de salarios no puntúa ni es card; sólo alimenta `indice_salarios_publico`
  (serie) y el salario real de vida cotidiana.

### Confirmación

`tests/test_indec_api.py`: unidades del EMAE, coma decimal de salarios, paginado, sectores
alineados por id y mapeados a los códigos A a O, vuelta a la copia si la API cae, y token
rechazado que no vuelve a la copia ni parece error de red. Cada una se probó rompiendo el código.

## Pros y contras de las opciones

### API del INDEC

- Bien: dato vigente, el mismo día que publica el INDEC; JSON estable, con signos convencionales.
- Mal: token que vence y servicio en beta.

### Planillas Excel del INDEC

- Bien: sin credencial.
- Mal: cada planilla cambia de forma sin aviso; es el camino frágil que el IPC y el IPI ya
  sufren (`indec_actividad.py`, `ipc_indec.py`).

### Copia de datos.gob.ar

- Mal: un mes de atraso y respuestas vacías o recortadas desde el 12-oct-2026 (`datos_gob.py`).

## Más información

Relevamiento del 2-nov-2026: la API también tiene IPC con todas sus aperturas, IPI
manufacturero y minero, precios mayoristas, costo de la construcción, canastas, EPH (mercado de
trabajo y pobreza), comercio exterior por rubro y uso económico, y población. Los próximos
candidatos son IPC, IPI y bienes de capital; ISAC, supermercados e informalidad no están.
