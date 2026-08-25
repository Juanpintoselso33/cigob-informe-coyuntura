---
madr: 4
id: '0256'
estado: 'aceptado'
fecha: 2026-08-25
cinturon: 'vida'
indicadores: [consumo_supermercados]
archivos: ['scripts/vida_cotidiana/collectors/indec_supermercados.py', 'scripts/descargar_series.py', 'scripts/vida_cotidiana/main.py', 'config.py', 'web/src/lib/fichas.ts', 'tests/test_consumo_supermercados.py']
relacionado: ['0243', '0225', '0155']
ambito: 'Cinturón vida cotidiana · ITCIS · `consumo_supermercados` · de qué fuente sale la serie y con qué rezago'
origen: 'Pendiente declarado al cerrar la remediación de la auditoría, 25-ago-2026: el INDEC publicó junio el 21-ago y la card seguía en mayo'
---

# ADR-0256 — La serie sale del INDEC, no de su espejo

## Contexto y planteo del problema

`consumo_supermercados` bajaba la serie `455.1_VENTAS_PREADA_0_M_44_44` de la
API de series de tiempo de datos.gob.ar. Esa API **no es la fuente**: es un
espejo de una planilla que publica el INDEC, y le llega con atraso propio.

El 25 de agosto de 2026 la web mostraba **mayo de 2026**. El INDEC había
publicado junio el **21 de agosto**, cuatro días antes. El espejo todavía no lo
tenía, y tampoco lo tenía el CSV de origen del catálogo
(`ventas-totales-supermercados-2.csv`), que termina en el mismo mes: los 26
indicadores del dataset 455.1 se cortan en mayo.

Encadenar los dos rezagos dejaba la card **un mes entero por detrás de lo
publicado**, y el tope de frescura del gate estaba calibrado sobre esa suma
—140 días— así que nada avisaba. El indicador no estaba roto: estaba viejo, y
el gate lo tenía autorizado a estarlo.

ADR-0243 ya había dejado escrito el pendiente al cerrar el rótulo de la base:
«el INDEC publicó junio de 2026 el 21 de agosto y la API de series todavía no
lo refleja».

## Factores de decisión

- **Frescura**: cuánto tarda el número en llegar a la web desde que existe.
- **Trazabilidad**: la card debería poder señalar la publicación que la
  respalda, no una copia de ella.
- **Fragilidad**: `indec.gob.ar` es un sitio hostil a la automatización
  —contesta 200 con la misma cáscara HTML para cualquier ruta inexistente—, y
  la API es estable y versionada.
- **Que el error sea visible**: cualquier camino nuevo tiene que fallar
  ruidosamente, no devolver un número plausible.

## Opciones consideradas

1. **Dejarlo como está** y esperar al espejo.
2. **Leer el informe técnico en PDF** del INDEC.
3. **Leer la planilla de serie histórica del INDEC**, con el espejo como
   contraste.

## Decisión

Se toma la **opción 3**: la serie sale de
`https://www.indec.gob.ar/ftp/cuadros/economia/serie_supermercados.xlsx`,
**Cuadro 1**, columna *Serie desestacionalizada*. El espejo de datos.gob.ar
queda como **contraste**, no como fuente.

La opción 2 se descartó porque la URL del informe lleva un hash rotativo
(`super_08_262444C24851.pdf`) y porque leer un número de un PDF de prensa es
peor que leerlo de la planilla de la que ese PDF sale. El hash, además, resultó
ser **descubrible** —la vista parcial `/Nivel3/Tema/3/1` lo publica—, pero la
planilla tiene URL estable y no hace falta descubrir nada cada mes.

### Consecuencias

- La card pasa de **mayo-2026 (83,2)** a **junio-2026 (82,1)**. No es una
  corrección: es el mes que faltaba. El valor de mayo además se revisó a 83,0
  en la misma publicación, porque el ajuste estacional se recalcula al agregar
  un mes.
- El tope de rezago baja de **140 a 130 días**, y por primera vez sale de una
  medición: sobre las **14 publicaciones** del calendario del INDEC entre
  julio-2025 y agosto-2026, el mes M sale entre **48 y 57 días** después de
  terminado (mediana 53) y las publicaciones se separan entre 23 y 34 días.
  Como `fecha_dato` es el día 1 del mes de referencia, el último punto nace con
  78-86 días y llega como mucho a **116** la víspera de la publicación
  siguiente. Un mes salteado lo llevaría a ~146, que es lo que el tope agarra.
- **No hay respaldo al espejo.** Si el INDEC no entrega la planilla, el
  colector levanta y la card mantiene su último valor marcada como
  desactualizada, que es el comportamiento de siempre. Un respaldo que leyera
  el espejo podría hacer **retroceder** la card de junio a mayo, que es peor
  que no actualizarla.

### Confirmación

`tests/test_consumo_supermercados.py`. Cada guarda nueva se verificó
rompiéndola: seis mutaciones, seis fallas, cada una en su propio test.

## Pros y contras de las opciones

### 1 · Dejarlo como está

- Bueno: cero trabajo, fuente estable.
- Malo: la web muestra un mes viejo teniendo el nuevo disponible, y el gate lo
  autoriza. No hay fecha en la que esto se arregle solo.

### 2 · El informe técnico en PDF

- Bueno: es lo primero que publica el INDEC.
- Malo: URL con hash rotativo; leer cifras de un PDF de prensa; el PDF trae el
  último mes y no la serie, que es lo que el componente necesita para rebasear.

### 3 · La planilla de serie histórica *(elegida)*

- Bueno: es la fuente; URL estable sin hash; trae la serie entera, así que las
  revisiones del ajuste estacional entran solas; el título declara la base
  (ADR-0243 se conserva) **y** el período que cubre.
- Malo: hay que parsear una planilla con encabezados combinados, y el sitio del
  INDEC contesta 200 para rutas que no existen.

## Más información

Las tres formas en que este camino podía romperse en silencio, y lo que se hizo
con cada una:

- **La cáscara de 37 KB.** `indec.gob.ar` devuelve 200 con la misma página HTML
  para cualquier ruta inexistente, así que `raise_for_status()` no distingue el
  archivo de la nada. El contenido se verifica por la **firma del zip** antes de
  abrirlo, y el mensaje de error dice dónde se vuelve a descubrir la URL.
- **La columna de al lado.** El Cuadro 1 trae tres series pegadas —original,
  desestacionalizada y tendencia-ciclo— bajo encabezados combinados. Leer la
  equivocada daría un índice de ventas perfectamente plausible. La columna se
  busca **por su encabezado** y no por su posición; y como eso sólo cubre que
  la columna desaparezca, el **contraste contra el espejo** cubre el resto:
  compara variaciones mes a mes sobre la superposición, y está calibrado con
  datos reales —la columna correcta diverge 0,041 pp de mediana, «serie
  original» 4,92 y «tendencia-ciclo» 0,84, contra un tope de 0,30—. Compara
  variaciones y no niveles a propósito: si el INDEC rebasea el índice, los
  niveles se corren enteros y las variaciones no.
- **La lectura truncada.** El título del cuadro declara el período que cubre
  («Enero 2017 – junio 2026»). Es una segunda afirmación de la fuente,
  independiente de las filas: si el parser se comiera las últimas, el número
  seguiría siendo plausible. El último mes leído tiene que coincidir con el
  declarado.

Y una nota sobre el sitio, para no volver a perder el tiempo: las páginas
`Nivel3`/`Nivel4` de `indec.gob.ar` son una cáscara que rellena JavaScript, así
que bajar el HTML no muestra ningún enlace. El contenido real está en las rutas
parciales `/Nivel3/Tema/<a>/<b>` y `/Nivel4/Tema/<a>/<b>/<c>` —el identificador
lo trae el propio `<input id="VistaCarga">` de la cáscara— y ahí sí aparecen los
archivos. Supermercados es `/Nivel4/Tema/3/1/34`. El calendario de publicaciones
responde igual, por día: `/Calendario/FiltrosCalendario/dia/AAAA-MM-DD/1`, que es
de donde salieron las 14 fechas con que se midió el rezago.
