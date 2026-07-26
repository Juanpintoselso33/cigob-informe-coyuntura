# ADR-0139 — Corrección: tres "imposibles" que no lo eran

- **Estado**: Aceptado
- **Fecha**: 2026-07-26
- **Ámbito**: cinturón político (ITCP), bloque judicial y `sector_privado`
- **Corrige**: ADR-0136 (apoyo público), ADR-0138 (éxito corporativo y velocidad)
- **Origen**: el editor señaló que se estaba declarando «imposible» sin agotar la
  búsqueda. Tenía razón, y es la segunda vez que pasa lo mismo.

## Lo que se había pasado por alto

Tres omisiones concretas, todas evitables:

1. **El menú del sitio del CSJN, en la misma página que ya se había descargado,
   decía «Datos abiertos», y no se siguió el enlace.** Apunta a
   `datos.csjn.gov.ar` y a `/transparencia/datos-estadisticos`. ADR-0138 concluyó
   «no hay estadística de duración publicada» mirando esa página y contando que
   no tenía archivos descargables, sin abrir el enlace que sí los tenía.
2. **SRA se dio por «no evaluable» por `ConnectionError`.** El dominio cambió:
   `ruralarg.org.ar` está muerto, la Sociedad Rural está en `sra.ar` y responde
   perfectamente. Un error de conexión contra una URL adivinada se registró como
   si fuera una propiedad de la fuente.
3. **Se eligió ADEBA como «mejor caso» de cámara empresaria** porque tenía una
   categoría `comunicados`. Es el peor caso: es una asociación de bancos cuyo
   feed es un boletín regulatorio diario. **AEA**, la asociación empresaria de
   referencia, publica exclusivamente comunicados de postura.

## Velocidad de resolución: era construible

ADR-0138 dijo «estructuralmente imposible: hay una sola fecha, la de la
sentencia, y una duración necesita dos». La Oficina de Estadísticas de la CSJN
publica un **Anuario Estadístico** construido sobre el sistema de gestión
judicial Lex 100, con una sección titulada **«Duración de los casos resueltos»**
que define:

> «La duración total de cada caso resuelto ha sido calculada considerando la
> cantidad de días corridos entre **la fecha de presentación** del caso ante la
> CSJN y **la fecha del fallo** que puso fin a su tramitación.»

Exactamente las dos fechas que se habían declarado inexistentes.

| | 2024 | 2025 |
|---|---|---|
| casos resueltos | 19.056 | 26.524 |
| duración promedio | 599 días | 609 días |
| mediana | 385 días | 364 días |
| **admitidos — promedio** | **730 días** | **844 días** |
| admitidos — mediana | 511 días | 571 días |
| stock de pendientes | 26.622 | 31.900 |

La señal está en los **casos admitidos** —los resueltos sobre el fondo, no los
rechazados por inadmisibles—: de 730 a 844 días en un año, **+15,6%**. Y el
stock de pendientes casi se triplicó desde 2022 (10.917 → 31.900).

Hay además **duración por secretaría de radicación**, incluida la N°4
Contencioso Administrativo, que es donde se litiga contra el Estado.

**Limitaciones reales**, que sí corresponde declarar: la cadencia es anual con un
informe de primer semestre —ya existe el de 2026, así que en la práctica es
semestral—, y es la CSJN sola, no todo el fuero federal. Lo segundo es
defendible (es donde terminan las causas políticamente sensibles) pero hay que
decirlo. Los cortes finos por secretaría están en tableros de Tableau que
requieren sesión con JavaScript; los agregados están en el PDF y alcanzan.

## Apoyo público: era viable, con otra cámara

ADR-0136 lo rechazó porque «el destinatario cambia»: de tres críticas de ADEBA,
dos apuntaban a municipios y una al Congreso. El razonamiento era correcto **para
ADEBA** y se generalizó indebidamente.

**AEA publica 46 comunicados fechados entre el 21-mar-2020 y el 31-mar-2026**,
de 3 a 11 por año, cada uno con su PDF de texto completo. Son postura explícita y
apuntan al **Gobierno nacional**.

**La serie se valida sola por el quiebre de régimen**: el tono se invierte
exactamente en el cambio de gobierno.

| gestión anterior | desde nov-2023 |
|---|---|
| «AEA rechaza la intervención de Vicentin» | «AEA felicita al Presidente electo Javier Milei» |
| «Alerta empresaria por la intención del Gobierno de subir la presión fiscal» | «Una oportunidad histórica» |
| «Más impuestos = Menos inversiones y empleo» | «El Pacto de Mayo: un paso muy positivo» |
| «Señales Negativas» · «Otra señal negativa» | «Satisfacción de la AEA por el acuerdo con el FMI» |

Y **la codificación es fácil**: «Señales Negativas» contra «Un paso muy positivo»
no exige juicio sutil. La objeción sobre lenguaje corporativo diplomático no se
sostiene con esta fuente.

De la objeción anterior **sobrevive una parte**: el costo es recurrente, hay que
codificar mes a mes con doble codificación. Pero con 3 a 11 piezas por año es un
costo chico, no el trabajo permanente de dos personas que se describió.

## Éxito corporativo y bloqueo cautelar: la premisa del rechazo era falsa

ADR-0138 los rechazó por «sin campo de partes ni de resultado». Eso era cierto
**de SAIJ**, no del universo disponible. El Anuario de la CSJN clasifica:

- **Presentantes en cuatro categorías**: Gobiernos/Organismos y Dependencias
  Públicas (ANSES 93,03%, después AFIP, Caja de Retiros de las FFAA, gobiernos
  provinciales), **Empresas** (ART 79,39%, manufacturas 3,31%, transporte
  terrestre de pasajeros 2,41%), otra de personas jurídicas, y personas físicas.
- **Tipos de resolución** que incluyen explícitamente **«Admite Medida Cautelar»
  y «Rechaza medida cautelar»** (con Nulidad suman 0,42% de los resueltos 2025).

**No quedan establecidos como construibles**: la tabulación cruzada
(empresa × resultado, cautelar × año) no está en el PDF sino en los tableros de
Tableau con filtros, y extraerla requiere sesión con JavaScript. Eso es trabajo
pendiente, no un imposible. Y hay que ser honesto con la escala: 0,42% de los
resueltos son del orden de 110 casos al año — poco, pero es un **censo** del
tribunal, no la muestra curada de SAIJ.

## Decisión

1. **Se revierten los veredictos de ADR-0136 y ADR-0138** en los términos de
   arriba. `velocidad_de_resolucion` y `apoyo_publico` pasan a **construibles**;
   `exito_corporativo` y `bloqueo_cautelar` pasan de «imposibles» a **pendientes
   de extracción**.
2. **No se incorpora todavía ninguno**, por la misma razón que ADR-0134/0135/0137:
   falta la decisión editorial de orientación y el ITCP está cerrado con
   auditoría 7/7.
3. Evidencia versionada en
   `data/politica/correccion_fuentes_judicial_empresario.json`.

## Consecuencias, y la regla que hay que respetar

Es el **segundo** incidente del mismo tipo (el primero está en
`feedback_no_declarar_fuente_inexistente`, con tres casos). El patrón no es
«buscar poco»: en los dos ADR corregidos se probaron varias fuentes y se
documentaron los negativos. El patrón es **cerrar el punto por escrito antes de
haber agotado lo que ya se tenía a mano**:

- un enlace del menú de una página **ya descargada**, sin abrir;
- un `ConnectionError` contra una URL **adivinada**, tratado como propiedad de la
  fuente en vez de como fallo de la conjetura;
- un caso elegido como «el mejor» **sin verificar que lo fuera**, y una
  conclusión generalizada desde él a las otras siete cámaras.

Regla operativa que queda: **antes de escribir «no hay fuente» o «es imposible»,
agotar los enlaces del propio sitio ya descargado, y no dar por muerta una
organización por una URL que se inventó.** Un negativo publicado en un ADR cierra
el punto para el resto del proyecto — el costo de equivocarse es mucho mayor que
el de una consulta más.
