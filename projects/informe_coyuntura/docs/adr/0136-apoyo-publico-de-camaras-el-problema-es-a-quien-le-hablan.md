---
madr: 4
id: '0136'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [sector_privado]
corregido_por: ['0139']
ambito: 'cinturón político (ITCP), dimensión `sector_privado`'
---

# ADR-0136 — Apoyo público de las cámaras: el problema es a quién le hablan

- **Relacionados**: ADR-0131 (protocolo), ADR-0088 (`sector_privado`),
  ADR-0091 y ADR-0068 (contar lo que no es), ADR-0134 y ADR-0135

> **⚠️ CORREGIDO POR ADR-0139.** El veredicto de este ADR («no se construye») **es
> incorrecto**. El razonamiento del destinatario era válido para ADEBA y se
> generalizó mal: ADEBA es una asociación de bancos cuyo feed es un boletín
> regulatorio, y elegirla como «mejor caso» fue un error no verificado. **AEA
> publica 46 comunicados fechados (2020-2026) que son postura explícita al
> Gobierno nacional**, y la serie se valida por el quiebre de régimen. Además,
> SRA no era inalcanzable: cambió de dominio a `sra.ar`. Leer ADR-0139.

## Contexto y planteo del problema

El aporte externo propone **Apoyo Público**: medir si las cámaras empresarias
respaldan o critican públicamente al Gobierno. ADR-0131 lo listó como pendiente
con fuente «RSS de cámaras empresarias» y lo que faltaba era «scraper + esquema
de postura». Se relevaron ocho cámaras: UIA, CAC, CAME, AEA, ADEBA, SRA, AmCham
y COPAL.

### El RSS no sirve, y era la fuente que proponía el aporte

El feed de ADEBA trae 21 items y **los 21 son «Síntesis normativa MBA»**: un
boletín regulatorio automático diario. Ni un solo comunicado institucional
aparece en el feed. Un colector basado en RSS mediría el boletín.

Lo mismo en otra forma en las demás: CAC publica agenda institucional (visitas,
webinars, firmas de paritarias) y CAME, servicios al socio (escalas de convenio,
rondas de negocios). El volumen existe; la señal es una fracción chica.

### La postura sí es codificable — más de lo esperado

En la categoría `comunicados` de ADEBA, que está separada de «noticias», los
títulos son explícitos:

- «ADEBA **CONSIDERA POSITIVAS** LAS MEDIDAS ANUNCIADAS POR EL GOBIERNO»
- «ADEBA **expresa su apoyo** a la iniciativa de la Jefatura de Gabinete…»
- «Bancos **advierten sobre el impacto negativo** de los cambios en las SGR…»

No es el lenguaje diplomático indescifrable que cabía temer. Un esquema de tres
posturas (apoyo / crítica / neutro) es aplicable.

### Pero el destinatario cambia, y eso hunde el indicador

De los tres ejemplos de crítica encontrados, **dos apuntan a municipios**
(«tasas municipales exorbitantes», «ingresos brutos y altas tasas municipales»)
y **uno al Congreso** («cambios en las SGR aprobados en el Congreso»). **Ninguno
al Poder Ejecutivo nacional.**

Un indicador de «apoyo público al Gobierno» que cuente comunicados críticos sin
codificar **a quién critican** mide otra cosa. Es la misma clase de error de
ADR-0091 (`veto_quorum` contaba sesiones «fracasadas» que eran informativas) y
ADR-0068 (el «fondo de cese laboral» era el régimen de la construcción): la
consulta trae documentos, los documentos no son el fenómeno.

Peor: en el caso de las tasas municipales, la cámara critica a los municipios
**alineándose con el Gobierno nacional**. Codificado como «crítica» a secas, ese
comunicado movería el indicador en el sentido exactamente contrario al real.

### Y el volumen es fino

La categoría `comunicados` de ADEBA tiene dos páginas de paginación —del orden
de 24 a 48 piezas en toda su historia—, de las cuales una parte es ruido
(«ADEBA lamenta el fallecimiento del Papa Francisco», «los bancos adhieren al
asueto del 24 y 31 de diciembre», bienvenidas a nuevos bancos socios) y otra
apunta a destinatarios que no son el Ejecutivo nacional. Quedan unas pocas por
año, en la cámara que resultó ser el mejor caso de las ocho.

## Opciones consideradas

- **No construir el indicador tal como está propuesto** — elegida, y no por falta de fuente: la fuente existe, es scrapeable y la postura es codificable.
- **Codificar sólo la postura** — insuficiente: sin codificar el destinatario, el indicador cuenta críticas a intendentes como si fueran críticas al Gobierno. El esquema mínimo es de dos ejes.

## Decisión

**No se construye el indicador tal como está propuesto.** No por falta de
fuente: la fuente existe, es scrapeable y la postura es codificable. Por tres
razones acumuladas:

1. **Hay que codificar el destinatario, no sólo la postura.** Sin eso el
   indicador cuenta críticas a intendentes como si fueran críticas al Gobierno.
   Si el punto se retoma, el esquema mínimo es de dos ejes: postura
   (apoyo/crítica/neutro) **y** destinatario (Ejecutivo nacional / Congreso /
   provincias y municipios / externo).
2. **El volumen no lo sostiene.** Unas pocas piezas útiles por cámara por año.
3. **El costo es recurrente, no de arranque.** A diferencia del veto de
   constitucionalidad (ADR-0131), donde la codificación es una pasada sobre un
   universo cerrado, acá habría que reclasificar **todos los meses**, con doble
   codificación y kappa ≥ 0,70. Es trabajo permanente de dos personas.

### Consecuencias

- La dimensión `sector_privado` sigue con `brecha_obra_publica` como único
  indicador (ADR-0088).
- Queda pendiente y explícito que **SRA y AmCham no se pudieron evaluar** por
  fallas de conexión y de TLS. Si el punto se retoma, empezar por ahí: son dos
  de las cámaras más políticamente vocales y podrían cambiar el diagnóstico de
  volumen.
- Relevamiento versionado en `data/politica/apoyo_camaras_relevamiento.json`,
  con las ocho cámaras, sus secciones reales y los ejemplos de cada categoría,
  para que el negativo sea auditable.

## Más información

### Nota de método, primero

El primer intento **adivinó rutas** (`/novedades/`, `/feed/`) y devolvió 404 en
casi todas. Eso no es evidencia de que no haya fuente. Leyendo las home
aparecieron las secciones reales en **cinco de ocho** cámaras. Queda anotado
porque es exactamente el error registrado en `feedback_no_declarar_fuente_inexistente`:
un negativo obtenido por adivinar URLs se documenta como hecho y cierra el punto.

SRA (ConnectionError) y AmCham (SSLError) no se pudieron evaluar. Se dice, no se
las da por inexistentes.
