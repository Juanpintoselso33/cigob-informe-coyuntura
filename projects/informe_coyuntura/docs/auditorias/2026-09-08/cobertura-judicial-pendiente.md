# Cobertura judicial: corrección integrada y límites pendientes

**Estado actual:** tarjeta e historia locales usan 705/955 = 73,82%. Se
contrastó el motor integrado con los tres archivos oficiales. El registro de
80 ajustes y cinco bajas distingue la foto original de la corregida. El
traslado de Fraga sigue pendiente: podría reducir el numerador a 704 (73,72%).
No se certifican juras ni exhaustividad de fallecimientos.

El cotejo adicional localizó la [Resolución CAF 705/24 del Consejo](https://pjn-documento-api.pjn.gov.ar/api/documento/adjunto/200289),
sobre contratación de inmueble para San Justo. Es un antecedente de 2024 y no
acredita habilitación al 8-sep-2026 ni salida de Fraga de Civil 104. No se
modifica el numerador por ese documento; subsiste la salvedad indicada.
[Cálculo integrado](cotejo-judicial-integrado.json) · [ADR-0298](../../adr/0298-cobertura-concilia-movimientos-netos-y-bajas.md).

## Corroboración nueva: mapa del Consejo al 4 de septiembre

El [mapa oficial de concursos](https://mc.consejomagistratura.gov.ar/mapadeconcursos/),
consultado el 8-sep, declara actualización 4-sep-2026 y todavía rotula
«Justicia Federal de San Justo - no habilitada». Su exportación de concursos
remitidos identifica el concurso 381, un cargo de la Cámara no habilitada,
a nombre de Andrés Guillermo Fraga y sin fecha de designación cargada.
El concurso 447 corresponde al juzgado federal de primera instancia N° 1,
también no habilitado; no confundirlo con la Cámara de destino de Fraga.

El corte antecede al Decreto 918/2026 (7-sep, publicado 8-sep), de modo que
la fecha vacía no contradice la designación ni demuestra falta de jura.
Corrobora el estado de habilitación hasta el 4-sep y justifica no añadir
el destino al universo fijo sin una habilitación posterior acreditada.
No prueba cuándo deja Civil 104: se mantiene la salvedad de un eventual
cargo menos en el numerador, sin convertirla en una baja confirmada.

Los archivos tienen 78, 279 y 69 filas según exportación. Son concursos,
ternas y etapas; no constituyen un padrón de ocupación ni permiten sustituir
el denominador 955 sumando sus filas o las cifras de portada. La página
incluso contiene jurisdicciones expresamente no habilitadas.
[Evidencia con fuentes y filas relevantes](cotejo-san-justo-consejo.json).
No cambia ningún dato del monitor por esta corroboración.

## Guía judicial: Civil 104

La [guía oficial del Consejo](https://consejomagistratura.gov.ar/guiajudicial/), consultada el 8-sep-2026, identifica Civil 104 con el ID público 690. Su botón Integrantes consulta por POST `integrantes.php` y devuelve Andrés Guillermo Fraga como juez y Gabriel Angel Tamborenea como secretario. [Respuesta acotada y hash](cotejo-guia-civil104.json).

Ni la guía ni esa respuesta declaran fecha de actualización. Es evidencia adicional de que la guía todavía lo lista en el cargo de origen; no acredita su permanencia efectiva al cierre del día frente al decreto recién publicado. No se convierte el nombramiento en destino no habilitado en una baja automática del origen. Se conserva 705/955 estimado y la salvedad de un posible movimiento pendiente de fecha efectiva. No se certifican juras ni un stock exhaustivo con este directorio.

## Hallazgo inicial y secuencia de investigación

Los apartados siguientes conservan el estado de cada etapa de investigación;
las referencias a una integración pendiente quedan superadas por el estado
actual indicado arriba.

El cotejo original del 8 de septiembre encontró un defecto pendiente de
corrección, no una mejora metodológica opcional. Los tres archivos del
Ministerio de Justicia reproducen la tarjeta, pero los movimientos están
publicados al **13 de julio**; no acreditan una cobertura observada al 8 de
septiembre. Véase [evidencia de archivos y cortes](cotejo-judicial-original-pendiente.json).

El padrón del 5 de junio contiene 955 cargos habilitados: 610 no vacantes y
345 vacantes. La reconstrucción agrega 60 designaciones de junio y resta
cinco renuncias con efecto en julio/agosto: 665/955 = 69,63%. Esta réplica
aritmética no incluye los movimientos publicados después del corte del CSV.

El cruce de identidad con el padrón encuentra **diez de esas 60 personas ya
titulares de cargos habilitados**. El archivo de evidencia enumera norma,
cargo previo y nuevo, sin conservar DNI. No corresponde contar esos diez
movimientos como diez incorporaciones netas sin conciliar las vacantes que
dejan: la renovación de noviembre no es el único caso que requiere revisión.

El [Boletín Oficial del 22 de julio](https://otslist.boletinoficial.gob.ar/ots/download/fe68a6b232a4e5e2dd66e4ecc9ceffd1357a0e5be3a2fe2f3fd3a97ff1ef92e1/0/)
publica nuevos nombramientos ausentes del archivo. La búsqueda directa del BO
para el 14 de julio–8 de septiembre recuperó 173 avisos de Primera Sección
en dos páginas (100 y 73 URLs únicas, sin superposición), de los cuales 70
están titulados JUSTICIA / Decreto. Se están leyendo y conciliando sus efectos;
el número de normas no equivale al de vacantes cubiertas.

Existe además una diferencia que el conteo de designaciones debe resolver:
el [Decreto 367/2026](https://www.boletinoficial.gob.ar/detalleAviso/primera/342088/20260519)
renueva por cinco años la permanencia de Carlos Mahiques desde noviembre.
No agrega una persona a un cargo vacío. Hoy queda fuera por su fecha futura,
pero el algoritmo actual lo sumaría al llegar noviembre. También deben
revisarse nombramientos de personas ya titulares de otro cargo, renuncias,
remociones y cambios de universo antes de certificar el stock reconstruido.

Pendiente: conciliar los actos posteriores y la continuidad de titulares,
corregir el tratamiento de la cobertura temporal, recalcular tarjeta e
historia y actualizar sus fichas y contrastes. No se ha sustituido el 69,63%
por una suma parcial de normas.

## Lectura completa del universo posterior

Las 70 normas quedaron leídas y [clasificadas con sus URLs](cotejo-judicial-normas-posteriores.json):
65 designaciones, tres renovaciones, una renuncia y una norma de conjueces.
Once de las 65 designaciones corresponden a titulares ya presentes en el
padrón. Las renovaciones son los decretos 615, 645 y 853/2026; conservan
titulares, y el 646/2026 nombra conjueces sin cubrir cargos titulares.

La conciliación también debe controlar el universo: el juzgado de Hurlingham
figura como no habilitado en el padrón de junio, aunque el Decreto 589/2026
designe una jueza. No corresponde sumar esa designación al numerador de los
955 cargos habilitados sin verificar habilitación y denominador. Tampoco se
pueden omitir remociones por el solo hecho de que no sean renuncias por decreto.

Se recuperaron 49 detalles por HTTP y 21 mediante lectura textual web del
original, incluidos 19 en la edición completa del 22 de julio. Los timeouts
locales no se interpretaron como inexistencia de las normas. No quedan
lecturas pendientes dentro de estos 70 decretos; queda conciliar sus efectos
con el stock y completar los eventos de otros órganos.

## Primera corrección del cálculo — ADR-0297

El filtro compartido de movimientos excluye Corte Suprema y las siete
renovaciones corroboradas de 2024–2026. Se agregaron cinco pruebas específicas
y pasó el control de coherencia de fichas: 14 pruebas en total. El primer
intento no recolectó el test nuevo por una ruta de importación ausente;
se corrigió antes de la corrida exitosa.

La reconstrucción integral todavía no se regeneró: falta conciliar el resto
de los movimientos. No se debe interpretar el filtro parcial como validación
de la tarjeta actual. Los cinco casos de prueba comprueban únicamente las
exclusiones de universo y continuidad, no la exhaustividad del stock.

## Bajas de otros órganos y error en el ancla

La consulta directa del archivo del Consejo devolvió 64 notas con «Jurado»
desde diciembre de 2023. Documenta las remociones de Poderti (18-dic-2025)
y López (18-ago-2026); el rechazo de destitución de Díaz Lacava el 2-sep-2026
no es una baja. La búsqueda «fallecimiento» en ese archivo sólo encontró dos
notas sobre docentes: no es un registro exhaustivo de bajas de jueces.

La Acordada CSJN 8/2026, considerando III, confirma el fallecimiento de Ana
Silvia Guzzardi el 18-mar-2026. Sin embargo, el CSV de junio todavía la
registra como titular no vacante. Por tanto, además de reconstruir movimientos,
debe corregirse el ancla: la foto original dice 610, pero esta baja omitida
reduce a 609 los cargos no vacantes del mismo universo, antes de incorporar
otros movimientos. No equivale aún al stock completo certificado.

Se creó el registro complementario `data/politica/cobertura_judicial_bajas.json`
y un conciliador que distingue baja ya incorporada de baja omitida en el
padrón. Cinco pruebas nuevas cubren doble descuento, fechas, republicación,
preservación de la fuente y rechazo de suspensiones; junto con el filtro de
universo, aprobaron diez pruebas. El cotejo con las filas originales detecta
exactamente una corrección del ancla: Guzzardi. La integración al colector y
el recálculo global continúan pendientes de la conciliación completa.

## Registro neto y primera reconstrucción

Se creó `data/politica/cobertura_judicial_movimientos.json` con 80 ajustes:
las 70 normas posteriores y los diez cambios de cargo identificados en junio.
La conciliación reemplaza efectos por norma y tipo, por lo que un suplemento
no vuelve a sumarse cuando aparece en un CSV nuevo. Las normas con varios
movimientos no desagregados se rechazan en lugar de adivinar su efecto.

El registro de bajas incorpora además Montesi (21-ago-2024) y Seró
(9-ene-2025), con procedencia diferenciada: dos medios contemporáneos para el
primero; resolución del Consejo y corroboración periodística de la fecha
diaria para el segundo. Es un registro complementario, no un censo certificado
de todos los fallecimientos.

El [cálculo preliminar](reconstruccion-judicial-preliminar.json) obtiene 659
titulares en junio, 672 en julio, 668 en agosto y 705 al 8 de septiembre, sobre
el universo fijo de 955: **73,82% en el último corte**. Está pendiente de
integración y revisión, y no sustituye todavía la tarjeta. Mantiene límites
explícitos sobre juras, habilitaciones y exhaustividad de bajas. El caso de
destino fuera del universo conserva pendiente la verificación del cargo de
origen; no se certifica el stock físico en ejercicio.

Las 16 pruebas específicas pasan: exclusiones de universo, corrección del
ancla, bajas, continuidad de titulares, ausencia de duplicación al actualizar
el CSV, eventos futuros y fin de serie en el corte revisado.

El orden del día del Consejo de agosto corrobora vacantes de origen ya conciliadas; no se duplican bajas. [Nuevo cotejo y contraste periodístico](judicial-contraste-vacantes.md). No resuelve el stock completo ni Fraga.
