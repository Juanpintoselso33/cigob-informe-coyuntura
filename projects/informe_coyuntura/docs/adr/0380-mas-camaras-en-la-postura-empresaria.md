---
madr: 4
id: '0380'
estado: 'aceptado'
nota_estado: 'La adjudicación de los 20 desacuerdos de la clasificación la hizo un agente de IA y está pendiente de revisión por una persona.'
fecha: 2026-10-27
cinturon: 'politica'
indice: 'ITCP'
indicadores: [apoyo_comercio, apoyo_empresario]
archivos: ['scripts/politica.py', 'scripts/itcp.py', 'scripts/descargar_series.py', 'scripts/procedencia_anclas.py', 'scripts/publicar.py', 'data/politica/apoyo_camaras_codificacion.json', 'data/politica/apoyo_camaras_relevamiento.json', 'web/src/lib/datos.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/fichas.ts']
relacionado: ['0088', '0131', '0136', '0150', '0310', '0334', '0335', '0372']
ambito: 'Cinturón político · ITCP · dimensión Sector privado'
origen: 'Reunión del 26-oct-2026: sumar otras cámaras además de la UIA si tienen posturas oficiales; criterio de Luis Babino de 4 comunicados con postura en 12 meses.'
---

# ADR-0380 — Más cámaras en la postura empresaria: entra el comercio

## Contexto y planteo del problema

[[0372-la-brecha-de-obra-publica-sale-del-indice-politico]] dejó la dimensión de
sector privado con un solo componente: la postura pública de la UIA. En la
reunión del 26-oct-2026 se acordó sumar otras cámaras si tienen posturas
oficiales (CAC y CAME en el comercio; SRA, CRA, FAA y Coninagro en el campo;
CESSI y Argencon en tecnología), con el método de la UIA —dos lectores a ciegas
más adjudicación; uno solo está descartado— y, si no aparecía nada, dejar todo
como estaba. El criterio de entrada de Luis es un mínimo de 4 comunicados con
postura por entidad en 12 meses.

El relevamiento de julio ([[0136-apoyo-publico-de-camaras-el-problema-es-a-quien-le-hablan]])
había descartado a la CAC y a CAME mirando la portada de sus sitios: «agenda
institucional» y «servicios al socio». Era un error de método que el propio
relevamiento ya advertía (no leer las secciones reales): las dos tienen una
sección de comunicados de prensa con archivo completo, y la CAC se pronuncia
sobre medidas del Gobierno desde diciembre de 2023.

## Factores de decisión

- El criterio de Luis se aplica a lo que alimenta el saldo: comunicados con
  postura (apoyo o crítica) dirigidos al Ejecutivo nacional (regla de conteo de
  [[0131-protocolo-de-codificacion-para-el-bloque-judicial]]; el error de ADEBA fue contar críticas a
  otros destinatarios).
- Un corpus incompleto no se mide ([[0310-apoyo-empresario-vuelve-con-el-corpus-cerrado]]).
- Las bandas se fijan antes de ver la serie ([[0150-apoyo-empresario-entra-al-itcp]]).
- Un criterio de entrada que alguna vez se aplicó a una cámara se aplica igual a
  la otra, y su reingreso tiene que ser de una línea ([[0334-aea-sale-del-perimetro-y-el-rotulo-dice-uia]]).

## Opciones consideradas

- **Un indicador nuevo, `apoyo_comercio`, con la CAC sola; CAME clasificada
  fuera del cálculo (elegida).**
- Un compuesto del comercio con CAC y CAME juntas.
- Análisis de sentimiento de lo dicho por referentes en la prensa.
- No cambiar el índice.

## Decisión

**Cumplen el mínimo, en la ventana de la card (oct-2025 a oct-2026)** — conteo
de comunicados con postura dirigidos al Ejecutivo nacional:

| Cámara | 2024 | 2025 | 2026 (al 27-oct) | últimos 12 meses | Entra |
|---|---|---|---|---|---|
| CAC | 11 | 6 | 4 | 4 | sí |
| CAME | 15 (+2 en dic-2023) | 9 | 1 | 2 | no |
| Coninagro, SRA, CRA | sin clasificar | | | | no (corpus) |
| FAA, CESSI, Argencon | | | | 0 | no |

(Con el conteo amplio —cualquier destinatario— cumplen CAC, 16, y CAME, 5; el
estricto es el que decide porque es el que puntúa.) La tabla completa por
cámara, con URL, volumen por año y por mes, está en
`data/politica/apoyo_camaras_relevamiento.json`.

1. **Clasificación.** 212 comunicados (74 de la CAC, 138 de CAME) desde el
   10-dic-2023, con las mismas reglas v2 de la UIA, dos lectores ciegos entre sí
   (agentes de IA de dos modelos distintos) y adjudicación de los 20
   desacuerdos con los tres criterios generales ya escritos. Concordancia
   (kappa): postura 0,903 y destinatario 0,918 sobre los 212; por cámara, CAC
   0,915 y 0,906, CAME 0,886 y 0,924. Los 282 informes estadísticos periódicos
   propios de las dos cámaras (consumo, venta ilegal, ventas minoristas pyme,
   paritarias…) se archivan sin clasificar por una regla de título escrita antes
   de clasificar, y quedan listados en el registro para poder auditarlos.
2. **Indicador.** `apoyo_comercio` = mismo saldo de 12 meses, mismo mínimo de
   tres comunicados, mismas bandas y mismo corpus cerrado que `apoyo_empresario`
   (una sola implementación del cálculo, `_apoyo_saldo_serie`). Registro y detector
   propios: `apoyo_camaras_codificacion.json` y `apoyo_camaras_novedades.json`.
   Los comunicados nuevos de la CAC se avisan como pendientes y cortan la serie.
3. **Dimensión.** Sector privado = 0,5 `apoyo_empresario` + 0,5 `apoyo_comercio`:
   cada sector es un voto, no cada comunicado. La tarjeta de la UIA pasa a
   llamarse «Postura pública de la industria»; la nueva, «Postura pública del
   comercio».
4. **CAME queda clasificada fuera del cálculo**, como AEA en la industria:
   `APOYO_COMERCIO_CAMARAS = ("CAC",)`; nombrar a CAME ahí la repone en el
   cálculo y en el detector. Con CAME el saldo del último mes sería +0,667
   (5 apoyos y 1 crítica) en vez de +1,0 (4 de 4); el puntaje es 100 en ambos.
5. **Campo y tecnología no entran.** CESSI, Argencon y FAA no tienen comunicados de
   postura (o no tienen sección de prensa). Coninagro, SRA y CRA sí parecen tener
   volumen, pero hoy no se puede cerrar un corpus completo desde dic-2023 (el sitio
   de la SRA empieza en enero de 2025, la CRA no pagina su listado) o falta
   clasificarlo (Coninagro): quedan como candidatas para la próxima tanda.

### Consecuencias

- Con el snapshot del 27-oct-2026: `apoyo_comercio` = +1,0 sobre 4 comunicados,
  puntaje 100; la UIA sigue en 40,0. Sector privado 40,0 → 70,0, ITCP 71,6 →
  75,8, tensión política 2,8 → 2,4 y puntaje global 4,0 → 3,9 (aprox.).
- **El saldo del comercio no puede bajar fácilmente**: la CAC apoyó al Ejecutivo
  en 21 de 21 comunicados dirigidos a él y dirige sus 12 críticas a provincias,
  Congreso, Justicia y organismos internacionales. Con 4 pronunciamientos en la
  ventana, una crítica lo bajaría a +0,6. La ficha lo dice.
- La serie del comercio arranca en febrero de 2024 (el primer mes con tres
  comunicados en la ventana) y llega a octubre de 2026: 32 puntos, **todos en
  +1,0**. No es un error de cálculo, es lo que la cámara dijo.
- Por ser método, llega a la edición mensual y al archivo ([[0359-el-mensual-se-lee-con-el-metodo-vigente]]).
- Fichas y descripciones nombran la composición; los textos de la dimensión
  dejan de decir que la UIA es el único componente.

### Confirmación

`tests/test_politica_apoyo_comercio.py` (sin red): perímetro y criterio de
entrada, kappa recalculado del registro, regla de informes estadísticos, textos
no repetidos, card = último punto de la serie, bandas iguales a las de la
industria, dimensión 50/50, rótulos, fuente publicada, detector (pendientes,
informes estadísticos, inventario, cámara fuera del perímetro, reingreso) y los
extractores de listado de CAC y CAME.

## Pros y contras de las opciones

- **CAC sola (elegida)**: aplica el criterio de Luis tal cual y el reingreso de
  CAME es una línea; pero el comercio queda con una voz y un saldo en el máximo.
- **CAC + CAME en un compuesto**: más observaciones y una serie más viva (varía
  entre 0,0 y +0,9), pero mete en el cálculo a una cámara que en el último año
  casi no se pronunció sobre el Ejecutivo y cambia el criterio caso por caso.
- **Sentimiento de prensa**: no hizo falta, hay comunicados oficiales; mezcla
  además lo que dicen los dirigentes con lo que firma la cámara.
- **No cambiar**: la dimensión seguiría con una sola cámara teniendo otra con
  archivo y volumen.

## Más información

- **La primera descarga de CAME estaba mal y la vieron los lectores.** Emparejé por
  posición enlaces y títulos de la página, y la barra lateral trae enlaces
  propios: a unos veinte títulos les tocó el cuerpo de otra nota. Los dos
  lectores avisaron por separado («el título no corresponde al texto»). Se
  corrigió el extractor (cada tarjeta se lee entera), se volvió a bajar todo
  CAME y se reclasificó **completo** con dos lectores nuevos; los 74 de la CAC no
  cambiaron y conservan su pasada. Es el mismo hallazgo de [[0151-el-corpus-estaba-truncado-y-la-codificacion-se-rehace]]: lo encontró la lectura, no un gate.
- **Límites declarados.** (1) Los lectores son agentes de IA de la misma
  familia: el kappa prueba que el manual es unívoco, no que dos personas
  coincidirían. (2) La adjudicación de los 20 desacuerdos la hizo otro agente de
  IA: **está pendiente de revisión por una persona** (Luis o Juan); cada caso
  lleva su motivo en el registro. (3) Hay 3 comunicados «dudosos» que no
  cuentan (dos de CAME de dic-2023 y uno de la CAC). (4) La regla de informes
  estadísticos mira el título; una frase de postura dentro de un informe no
  entra. (5) La guarda de cámara muda ([[0332-una-camara-que-calla-no-dispara-nada]]) no se
  extendió a la CAC: un silencio largo de la cámara no avisa todavía.
- Pendiente de la reunión: campo y tecnología. Próxima tanda: clasificar Coninagro
  (archivo completo, ~50 candidatos) y recuperar el archivo 2024 de la SRA.
