---
madr: 4
id: '0151'
estado: 'aceptado'
fecha: 2026-07-29
cinturon: 'politica'
indicadores: [sector_privado]
corrige: ['0150']
ambito: 'cinturón político (ITCP), dimensión `sector_privado`'
---

# ADR-0151 — El corpus estaba truncado: `apoyo_empresario` se recodifica entero

- **Corrige**: ADR-0150 (que dejó el truncamiento anotado como pendiente menor)
- **Relacionados**: ADR-0131 (protocolo de codificación), ADR-0148 (descartado),
  ADR-0088 (dimensión `sector_privado`)

## Contexto y planteo del problema

ADR-0150 cerró el indicador dejando anotado un pendiente: «el texto de AEA sigue
cortado en 700 caracteres en origen, porque viene de extraer PDFs. En
comunicados que abren con un rodeo puede quedar afuera el pasaje que fija
posición». Se lo trató como una prolijidad pendiente. Al ir a arreglarlo resultó
ser más grande y con efecto sobre el número publicado.

### 1. El truncamiento no era sólo de AEA, y el de UIA estaba en el código

| cámara | tope | casos topeados |
|---|---|---|
| AEA | 700 caracteres | 36 de 46 |
| UIA | **1800 caracteres** | 37 de 57 |

Los dos son cortes duros: **36/36 y 37/37 de los casos topeados terminan a mitad
de palabra** (`«Debemos mantene»`, `«Cámara Naci»`). No es coincidencia de
longitud.

El de UIA estaba en `politica.py`, en `_uia_comunicado`: `_uia_cuerpo(r.text)[:1800]`.
O sea que no era un residuo del proceso ad-hoc que armó el corpus: **el detector
de novedades seguía produciendo textos truncados para toda codificación futura**.
Ya se sacó. El de AEA sí venía del proceso ad-hoc, que no dejó código.

### 2. Re-extracción completa: 103 de 103, 120.851 caracteres recuperados

- **UIA** (57): del HTML, sin tope.
- **AEA con PDF** (38): con `pymupdf`, normalizando la ligadura «ti» que la
  fuente mapea a **U+019F** — `pdfplumber` la entrega como `�` y `pymupdf` como
  `posiƟvas`. No es un problema de librería sino del `ToUnicode` de la subfuente;
  se resuelve normalizando, no cambiando de extractor.
- **AEA sin PDF** (8): el cuerpo está inline en `prensa.html`.

De los casos topeados faltaba una **mediana de 1.148 caracteres** y hasta 7.741.

**Control de no-regresión**: los casos que *no* estaban topeados salen idénticos
carácter por carácter al registro anterior. Eso es lo que autoriza a decir que se
recuperó texto en vez de haber traído otro texto.

### 3. Un caso de UIA no tiene cuerpo, y no es falla de extracción

`uia.org.ar/prensa/4244/` («Informe Especial», 05-jun-2026) devuelve 1.705
caracteres de los cuales ninguno es cuerpo: es el menú del sitio. La UIA no
publicó texto. Queda marcado `sin_cuerpo` y los dos codificadores lo trataron
igual, sin que ninguno tuviera que adivinar.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

### Consecuencias

- **Un tope de caracteres en un extractor que alimenta codificación humana es un
  sesgo silencioso, no un detalle de tamaño.** El texto truncado sigue siendo
  texto válido: ningún gate, ningún test y ninguna inspección de estructura lo
  ve. Lo detectó el pendiente anotado en un ADR, no la maquinaria de control.
- Es el **segundo defecto del mismo extractor** encontrado por la vía de
  codificar de nuevo (el primero, el menú de navegación, está en ADR-0150). La
  doble codificación ciega está funcionando como auditoría de datos además de
  como medida de confiabilidad.
- El registro versionado en `data/politica/apoyo_empresario_codificacion.json`
  reemplaza por completo al de ADR-0150, que se descarta entero.

## Decisión

### La segunda pasada, completa

Dos codificadores ciegos entre sí sobre el corpus con texto completo, el autor
del manual adjudica y no codifica (diseño de ADR-0150).

| eje | acuerdo | kappa |
|---|---|---|
| postura | 0,951 | **0,918** |
| destinatario | 0,942 | **0,910** |

**Un kappa más bajo que el anterior es el resultado correcto.** La pasada sobre
texto truncado había dado 1,000 y 0,955. No era mejor codificación: con textos
cortados hay menos material sobre el cual discrepar, y buena parte del corpus
caía en «neutro» por defecto. Un kappa que *sube* cuando empeora el insumo no
está midiendo confiabilidad. Conviene tenerlo presente antes de leer un kappa
alto como señal de calidad.

### 12 casos cambian con el texto completo

Casos donde **los dos codificadores coinciden entre sí** y difieren del registro
viejo: 4 de postura y 8 de destinatario. Los tres `neutro` → `critica` son del
mismo tipo: comunicados de AEA que enumeran controles de precios, cepo y presión
tributaria en pasajes que caían después del corte.

### Los 11 desacuerdos se adjudicaron con tres criterios, no caso por caso

1. **Texto mixto** que apoya una cosa y critica otra → manda la **postura
   dominante**, no `dudoso`.
2. **Crónica de reunión o evento** → el destinatario lo fija **el contenido del
   reclamo**, no con quién se reunió la cámara.
3. **Diagnóstico estructural** que no identifica una medida concreta → `neutro`.

### Efecto sobre el indicador

| | antes | ahora |
|---|---|---|
| comunicados en la ventana | 6 | 7 |
| apoyos / críticas | 1 / 5 | 2 / 5 |
| **saldo** | **−0,667** | **−0,429** |
| **puntaje** | **10,0** (piso) | **35,7** |
| variación 12m | −0,334 | −0,629 |

El indicador dejaba de estar en el piso de la escala. La variación a 12 meses se
hace **más negativa** porque la ventana de comparación de hace un año también se
recodificó y ahí aparecieron apoyos que el texto truncado no mostraba.

### Lo que NO cambió, y por qué importa

Al detectar el truncamiento se identificó `2024-12-17 — AEA recibió al ministro
Caputo` como una miscodificación segura: el texto se cortaba justo en «destacó
como muy p|ositivas las políticas orientadas a favorecer la competitividad del
sector privado», y eso parecía `apoyo` codificado como `neutro`.

**Los dos codificadores, leyendo el texto completo, lo dejaron en `neutro`**, y
con el mismo argumento cada uno: es la crónica de un almuerzo, y el manual
distingue crónica de comunicado de postura. El truncamiento era real; la
miscodificación deducida de él, no. Queda registrado porque el error es
instructivo: **encontrar el defecto de un insumo no autoriza a predecir qué
codificación produce** — eso lo decide el manual aplicado por quien codifica.

Salvedad honesta: el criterio 2 de adjudicación («manda el contenido, no la
crónica») tensiona con ese caso. No se lo revisó porque la adjudicación se
aplica **sólo a los desacuerdos**: revisar casos donde los dos ciegos
coincidieron es el autor del manual recodificando, que es exactamente lo que el
diseño de ADR-0150 vino a evitar. Queda anotado como el primer caso a mirar si
alguna vez se rehace la pasada.

### Lo que se corrigió en código

- `politica.py`, `_uia_comunicado`: se saca el tope de 1800 caracteres.
- `tests/test_politica_apoyo_empresario.py`: el test que exigía que las dos
  pasadas coincidieran **exactamente** en el conjunto computable se reemplaza.
  Esa igualdad era una propiedad del corpus truncado, no una garantía del
  método, y mantenerla presionaría a codificar para que el test pase. La
  garantía que sí corresponde —y que el test ahora verifica— es que **si las dos
  pasadas difieren en si un caso cuenta, el caso está marcado `adjudicado`**:
  nada entra al conteo por omisión.
