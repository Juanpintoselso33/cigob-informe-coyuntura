# Devolución a los aportes sobre gestión y política

**Para:** Marcos (cinturón de gestión) y Pablo (cinturón político)
**De:** equipo del Informe de Coyuntura · CIGOB
**Fecha:** 25 de julio de 2026

Gracias por los dos documentos. Los dos entraron al informe y los dos lo
mejoraron. Abajo va, punto por punto, qué se implementó, qué ya estaba resuelto
antes de que ustedes escribieran y qué queda pendiente.

Una aclaración que conviene hacer primero, porque afecta a varias observaciones:
**el cinturón de gestión se rehizo el 20 de julio**, después de las auditorías
del 17 que Marcos usó como base. Varios puntos del documento ya estaban
corregidos cuando llegó. No es un problema del aporte —la foto cambió entre
medio— pero vale la pena saberlo para no volver a trabajar sobre fichas viejas.

---

## Aporte sobre el cinturón de gestión (Marcos)

### Lo que se implementó

**La fuente oficial de desregulación. Fue el mejor aporte del documento y ya
está publicado.**

El indicador dejó de contar normas por cuenta propia sobre InfoLeg y pasa a
publicar la cifra del Ministerio de Desregulación y Transformación del Estado:
**689 normas de desregulación acumuladas desde el 10 de diciembre de 2023**.

Un detalle técnico que puede interesar: la serie mensual completa estaba dentro
de los propios informes, en el gráfico de la Figura 1, pero no se podía extraer
como texto porque el PDF trae las etiquetas convertidas a curvas. Se recuperó
midiendo las barras y calibrando contra las cifras de portada, y se validó
contra los titulares de diez informes distintos: el error máximo es de tres
normas. La serie va de **4 normas en diciembre de 2023 a 689 en junio de 2026**,
con el salto reconocible a partir de la Ley Bases.

**Sobre la meta de 300**: no se pudo usar como techo. En julio de 2025 ya se
habían superado (396), de modo que el indicador habría nacido clavado en 100 y
no se habría movido nunca más. La escala quedó en 100 / 300 / 600 / 1.200, y el
puntaje pasó de 72,0 a 73,3: cambió de dónde sale el número, no cuánto vale.

**Dos cosas quedaron declaradas en la ficha pública**, porque nos parece que el
lector tiene que saberlas: que es el Gobierno midiendo su propio programa, y que
el ministerio publica el conteo pero no publica ninguna meta, así que la vara
sigue siendo una convención nuestra. También que **el ministerio revisa su serie
hacia atrás de forma sustantiva**: el informe de junio de 2025 declaraba 212
normas donde el gráfico de abril de 2026 ubica más de 310.

### Lo que ya estaba resuelto antes del aporte

| observación | estado |
|---|---|
| Se cuentan normas como si fueran equivalentes | Corregido el 20-jul: se contaban menciones de la palabra "deroga" en cualquier parte del documento, y casi la mitad no derogaba nada. Ahora se lee sólo la parte dispositiva |
| El DNU 70/23 no se puede medir | La premisa era falsa y el error era nuestro: sí está indexado y siempre estuvo contado. Lo decía mal nuestra propia ficha, y el auditor la creyó — con razón |
| Dotación APN: ¿incluye empresas del Estado? | Resuelto el 20-jul: la card publica las tres cifras (APN sola, empresas, universo completo) y son casi idénticas |
| El FAL mide la adopción de algo que todavía no rige | Rediseñado el 20-jul en tres etapas (construcción 40 / vigencia 20 / adopción 40). Pasó de 0,4 a 40,2 |
| Privatizaciones: depende del juicio del analista | Parcialmente: se publica la norma que respalda la etapa de cada empresa. Sigue sin haber fuente en vivo |

### Lo que queda pendiente

**La ponderación del FAL (50/50 en lugar del 70/30 actual).** Es una decisión
editorial y está en la mesa. El argumento —instrumento y resultado deberían
pesar igual— es conceptual y no un ajuste para mover el número, así que pasa el
filtro que el proyecto se impuso para no recalibrar por conveniencia.

**Automatizar las privatizaciones vía InfoLeg.** La propuesta es correcta en su
diagnóstico pero nuestra lectura es que la automatización llega hasta la mitad:
la *detección* de las normas se puede automatizar, la *clasificación* en las
cuatro etapas no. El registro documenta un caso —Nucleoeléctrica— donde el
analista deliberadamente mantuvo una etapa más baja que la que la norma
habilitaba. Automatizar eso borraría un criterio que hoy está a la vista y se
puede discutir. Lo que sí se puede construir es un detector de novedades que
garantice que no se escape ninguna norma nueva.

**Confirmar si el denominario de la dotación APN incluye fuerzas armadas y de
seguridad.** Es la única parte del punto 2 que no cubre lo hecho el 20-jul.

---

## Aporte sobre el cinturón político (Pablo)

### Lo que se implementó

**El bloque del Poder Judicial ya está publicado.** El ITCP tiene desde hoy una
dimensión nueva, con el 15% del cinturón, y las seis dimensiones anteriores
cedieron proporcionalmente conservando su orden relativo.

El indicador que entró es **Tasa de Cobertura de Vacantes**, que fue el que se
eligió por la razón que el propio documento da: de los seis propuestos, es el
único que es un conteo y no un juicio, y por lo tanto el único que se puede
publicar sin resolver antes el protocolo de codificación.

**Resultado: el 69,95% de los cargos de juez habilitados tiene juez designado.**
De 955 cargos, 604 tienen titular, **282 funcionan con subrogante** y 69 están
sin cubrir. La serie reconstruida desde diciembre de 2023 muestra algo que
ningún valor puntual mostraría: la cobertura se erosionó de 72,8% a 64,1% en dos
años y medio —las renuncias siguieron y las designaciones se detuvieron casi por
completo, con un solo nombramiento en todo 2024— y se recuperó de golpe a 70,2%
cuando el Senado aprobó un conjunto de pliegos el 11 y 12 de junio.

**Sobre la fuente: el scraper del Consejo de la Magistratura no hizo falta para
este indicador.** El Ministerio de Justicia publica en el portal de datos
abiertos, en CSV estructurado, el padrón completo de magistrados con la marca de
cargo vacante, más los registros fechados de designaciones y renuncias. Eso da
directamente la magnitud que el indicador necesita, sin HTML y sin parser.

Esto no invalida el piloto: **sigue siendo el camino para los otros cinco
indicadores del bloque**, que sí necesitan datos de concursos y que el portal de
datos abiertos no cubre.

Un dato que puede servir para el análisis: **el padrón oficial vigente es del 5
de junio, o sea anterior al lote de designaciones**. La cifra que el Ministerio
publica hoy está desactualizada respecto de la realidad; nuestra serie la
corrige con los registros de designaciones, que sí están al día.

### Lo que queda pendiente, y por qué

**Los otros cinco indicadores judiciales y los tres del bloque económico están
todos bloqueados por lo mismo**, que es exactamente lo que el documento pone
como su recomendación número uno: el protocolo de codificación de contenido.

Clasificar un fallo como favorable o adverso, decidir qué causa es "sensible" o
leer un comunicado empresario como apoyo o rechazo son operaciones que, sin
reglas explícitas y sin doble codificación con chequeo de concordancia, dejan el
puntaje colgado del criterio de quien arme el informe ese mes. Para un índice
que se publica todos los meses y que pretende ser auditable, eso es
descalificante.

**Ese protocolo es el cuello de botella real del bloque**, y es trabajo
metodológico, no de scraping. Si hay interés en avanzar, es por ahí y no por la
infraestructura técnica, que está resuelta.

**Sobre el bloque económico**, vale una aclaración: la dimensión de sector
privado ya existe en el índice desde el 19 de julio, con un solo indicador —la
brecha entre la obra pública y la privada—. Que tenga uno solo está declarado
como limitación en su documentación: mide un canal de conflicto y es ciega a una
pelea con el agro, la energía o los bancos. Los tres indicadores propuestos
apuntan justo a ese hueco.

### La recomendación de infraestructura compartida

El documento propone construir una sola infraestructura de scraping de causas
para alimentar Bloqueo Cautelar y Judicialización desde ángulos distintos. Es
correcta y queda anotada. Con la salvedad de arriba: primero el protocolo,
después el scraping. Construir el scraper antes deja datos que no se pueden
puntuar.

---

## Resumen

| aporte | implementado | pendiente |
|---|---|---|
| Gestión (Marcos) | Fuente oficial de desregulación | Ponderación del FAL · detector de novedades de privatizaciones · denominador de dotación APN |
| Política (Pablo) | Dimensión del Poder Judicial + cobertura de vacantes | 5 indicadores judiciales + 3 económicos, todos detrás del protocolo de codificación |

Los dos aportes están citados como origen en la documentación de decisiones del
proyecto, con el detalle de qué se tomó, qué se descartó y por qué.
