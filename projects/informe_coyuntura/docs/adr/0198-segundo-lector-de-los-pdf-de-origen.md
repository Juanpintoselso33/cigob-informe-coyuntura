---
madr: 4
id: '0198'
estado: 'aceptado'
fecha: 2026-08-12
cinturon: 'transversal'
parametros: ['MODELO', 'UBICACION', 'TOLERANCIA']
archivos: ['scripts/verificacion_pdf.py', 'tests/test_verificacion_pdf.py', '.gitignore']
relacionado: ['0180', '0196']
ambito: 'Control de plausibilidad de los indicadores que se leen de un PDF — no alimenta el snapshot ni la web'
origen: 'Al revisar qué otras cosas se podían usar de BigQuery, el hueco que quedaba no era de modelos sino de lectura: un parser de regex devuelve el número de al lado sin fallar'
---

# ADR-0198 — Un segundo lector para los PDF de origen, en modo sombra

## Contexto y planteo del problema

Varios indicadores salen de un PDF que se parsea con expresiones regulares sobre
el texto que aplana pdfplumber. Ese diseño tiene un modo de falla propio: cuando
la fuente mueve una columna, **el parser no falla, devuelve el número de al
lado**. El valor es plausible, entra al índice y no lo detiene nada.

Lo que hay hoy no cubre eso:

- `gate_calidad.py` valida estructura, frescura y card-contra-serie. Un dígito
  mal leído pasa las tres.
- Los tests de reconciliación comparan el snapshot consigo mismo.
- `bq_ml.py` (ADR-0196) detecta anomalías estadísticas, o sea valores que no
  pegan con la historia de su serie. Un error de columna que cae dentro del
  rango histórico —justamente el caso peligroso— no se ve ahí.

Ninguno mira lo único que importa: **si el número es el que decía el documento**.

`consumo_carnes.py` ya se defiende sola exigiendo que los componentes sumen el
total publicado, pero eso es artesanal, indicador por indicador, y sólo existe
donde hay una identidad aritmética que verificar.

## Factores de decisión

- El verificador no puede volverse un riesgo: si rompe la corrida cuando Vertex
  está caído, cambia un problema improbable por uno seguro.
- No sabemos la tasa de falsas alarmas sobre datos reales, y un verificador que
  grita seguido se termina ignorando.
- El costo tiene que ser conocido antes, no descubierto en la factura.
- La elección del modelo tiene que salir de una medición, no de una impresión.

## Opciones consideradas

- **A. Segundo lector con un modelo, en modo sombra, como herramienta interna.**
- **B. Extender el patrón de `consumo_carnes`**: chequeos aritméticos escritos a
  mano, indicador por indicador.
- **C. Nada**, y confiar en que un error de parseo se note por otra vía.
- **D. Segundo lector que FALLE la corrida** ante una discrepancia.

## Decisión

**Opción A.** `scripts/verificacion_pdf.py` baja los mismos PDF que el pipeline,
los lee con `gemini-3.6-flash` y compara contra lo que sacó el parser. Es el
patrón que en la industria se llama *LLM challenge*: dos extracciones
independientes, y la discrepancia es la señal. El parser sigue siendo la fuente
del dato; el modelo no vota, sólo avisa que las dos lecturas no coinciden.

**Modo sombra**: registra y **siempre sale por 0**. Sin credenciales, con Vertex
caído o con un timeout, se omite el caso y sigue. Se decide con un mes de
historial si pasa a fallar de verdad.

**Sólo cuando el documento cambia**: se guarda la huella del texto extraído y se
saltea la consulta si no cambió. Es lo que mantiene el costo en centavos.

### El modelo se eligió midiendo

Benchmark del 2026-08-12 sobre tres documentos reales (SAGYP, CICCRA de 41
páginas y la planilla SDDS del BCRA), 3 corridas por modelo, contra la verdad
leída a mano — SAGYP además cierra por suma: 47,28 + 47,24 + 19,93 = 114,45.

| modelo | correctos | errados | consistente |
|---|---|---|---|
| **gemini-3.6-flash** | **27/27** | 0 | sí |
| gemini-3.5-flash | 27/27 | 0 | sí |
| gemini-2.5-flash | 24/27 | 3 | sí |
| gemini-2.5-flash-lite | 15/27 (12 nulos) | 0 | sí |
| gemini-2.5-pro (vía Vertex) | 22/27 | 5 | **NO** |

`gemini-2.5-flash` lee `aviar = 51,21`, que es el valor de carne **vacuna del
año anterior** en el mismo gráfico aplanado: agarra la columna de al lado, con
seguridad y las tres veces. Es exactamente la falla que este ADR quiere cubrir,
cometida por el verificador.

Dos hallazgos laterales que quedan registrados porque cambian decisiones:

1. **El harness cambia el resultado.** `gemini-2.5-pro` sacó 27/27 llamado desde
   `AI.GENERATE` de BigQuery y 22/27 —inconsistente— llamado directo a Vertex,
   con el mismo id de modelo y el mismo prompt. Si esto se reescribe para llamar
   de otra forma, hay que volver a medir, no heredar la tabla de arriba.
2. **La región decide el menú.** Los endpoints regionales, incluido
   `southamerica-east1` donde vive el dataset, sólo ofrecen la familia 2.5 —
   que se da de baja no antes del 2026-10-16. La generación actual sólo aparece
   con `location='global'`. Por eso se llama a Vertex directo desde el colector
   y no por BigQuery: así no hace falta tabla intermedia ni conexión, y
   `informe_coyuntura` se queda donde manda ADR-0180.

### El costo, medido

Tokens reales de `usage_metadata`, no estimados. La relación medida es de **2,09
caracteres por token** —las tablas de números tokenizan mucho peor que la
prosa—, contra los 3,7 de prosa castellana que se habían supuesto al principio:
la primera estimación se quedaba 76% corta.

Con un techo de 353.000 tokens/mes: **US$ 0,57 por mes, US$ 6,81 al año.**

### Consecuencias

- Aparece un control que no existía: que el número publicado sea el que decía el
  documento.
- El modelo queda en una constante. Las bajas de modelo son frecuentes y esta
  familia ya tiene fecha.
- `output/verificacion_pdf/` se ignora en git, igual que `output/bq_ml/`: es
  opinión sobre un dato, no el dato, y se regenera solo.
- No corre en el pipeline nocturno todavía. Se invoca a mano mientras dure el
  modo sombra.

### Confirmación

- `tests/test_verificacion_pdf.py` (10 tests), ninguno llama al modelo: fija qué
  cuenta como discrepancia, que una abstención del modelo no sea una acusación,
  la tolerancia por redondeo, el ahorro por huella, y —los dos que más
  importan— que sin credenciales y con el modelo caído la corrida salga por 0.
- Primera corrida real, 2026-08-12: 9 campos verificados en 3 documentos, **0
  discrepancias**. Segunda corrida: 0 consultas, todo reusado por huella.

## Pros y contras de las opciones

- **A. Segundo lector en modo sombra.** Bueno: cubre el hueco, cuesta centavos,
  no puede romper nada y se apaga solo si falla. Malo: introduce dependencia de
  un servicio externo y de un modelo con fecha de baja.
- **B. Chequeos aritméticos a mano.** Bueno: sin dependencias, determinístico,
  gratis. Malo: sólo funciona donde hay una identidad que verificar. CICCRA
  publica un número suelto en prosa: no hay suma que cierre.
- **C. Nada.** Bueno: costo cero. Malo: deja en pie el modo de falla más
  peligroso del pipeline, que es el que produce un número creíble y equivocado.
- **D. Que falle la corrida.** Bueno: imposible de ignorar. Malo: sin conocer la
  tasa de falsas alarmas, convierte al verificador en la causa más probable de
  una publicación frenada. Es la opción a la que se puede pasar después, con el
  historial del modo sombra como evidencia.

## Más información

- ADR-0196 — los modelos internos de BigQuery ML; mismo criterio de "herramienta
  interna que no toca el snapshot", y el detector de anomalías que este ADR
  complementa por el lado que aquél no ve.
- ADR-0180 — el dataset en `southamerica-east1` y por qué no se mueve.
