---
madr: 4
id: '0139'
estado: 'aceptado'
fecha: 2026-07-26
cinturon: 'politica'
indicadores: [sector_privado]
corrige: ['0136']
relacionado: ['0170']
cerrado_por: ['0166', '0168']
ambito: 'cinturón político (ITCP), bloque judicial y `sector_privado`'
origen: 'el editor señaló que se estaba declarando «imposible» sin agotar la'
---

# ADR-0139 — Corrección: tres "imposibles" que no lo eran

- **Corrige**: ADR-0136 (apoyo público), ADR-0138 (éxito corporativo y velocidad)
  búsqueda. Tenía razón, y es la segunda vez que pasa lo mismo.

## Contexto y planteo del problema

### Lo que se había pasado por alto

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

## Opciones consideradas

- **Reabrir cada fuente con la consulta correcta** — elegida.
- **Mantener los tres veredictos negativos previos** — descartada: los tres «imposibles» no lo eran. El rechazo de ADR-0138 («no hay campo de partes ni de resultado») era falso; el motivo real era otro.

## Decisión

1. **Se revierten los veredictos de ADR-0136 y ADR-0138** en los términos de
   arriba. `velocidad_de_resolucion` y `apoyo_publico` pasan a **construibles**.
2. **`exito_corporativo` y `bloqueo_cautelar` siguen sin ir, pero por otra
   razón.** El rechazo de ADR-0138 («no hay campo de partes ni de resultado»)
   era falso. El motivo real es que la población no es la que el indicador
   supone: «Empresas» ante la CSJN son 7% de los ingresos y cuatro quintos de
   ellas son ART. La diferencia importa: un negativo por falta de campo se cae
   apenas alguien encuentra el campo; éste se sostiene con datos.
3. **No se incorpora todavía ninguno**, por la misma razón que ADR-0134/0135/0137:
   falta la decisión editorial de orientación y el ITCP está cerrado con
   auditoría 7/7.
4. Evidencia versionada en
   `data/politica/correccion_fuentes_judicial_empresario.json`.

## Más información

### Velocidad de resolución: era construible

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
Contencioso Administrativo, que es donde se litiga contra el Estado. El rango en
2025 va de **542 días** (Penal Especial) a **2.082 días** (juicios originarios,
cinco años y ocho meses, coherente con que tramitan en instancia única); en 2024
iba de 453 (Previsional) a 2.689.

**Limitaciones reales**, que sí corresponde declarar:

- La cadencia es anual con un informe de primer semestre —ya existe el de 2026,
  así que en la práctica es semestral—. Para un tablero mensual es lento, pero no
  más que otros indicadores del informe.
- Es la CSJN sola, no todo el fuero federal. Es defendible (es donde terminan las
  causas políticamente sensibles) pero hay que decirlo.
- **Usar mediana, no promedio.** La propia fuente advierte «marcada asimetría
  positiva entre la media y la mediana» en todas las secretarías: hay casos de
  larga duración que levantan el promedio por encima del valor central.

### Y hay serie histórica completa: los tableros publican un PNG renderizado

Los tableros no se pueden consultar por API. Pero **Tableau Public publica un
render estático de cada hoja**, con las etiquetas de datos visibles
(`public.tableau.com/static/images/Re/Resueltos2024/Resueltos/1.png`). De ahí
sale la serie 2014-2024, y el Anuario 2025 completa el último año.

**La lectura queda verificada aritméticamente**: los 12 años cierran exacto — el
saldo que la fuente enuncia por separado es igual a ingresos menos resueltos, sin
una sola discrepancia.

| año | 2014 | 2016 | 2018 | 2020 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| ingresos | 16.783 | 15.719 | 28.037 | 15.308 | 31.344 | 32.233 | 45.678 | 58.424 |
| resueltos | 23.803 | 13.272 | 7.278 | 11.090 | 20.427 | 16.889 | 19.056 | 26.524 |
| **tasa de resolución** | **141,8%** | 84,4% | 26,0% | 72,4% | 65,2% | 52,4% | **41,7%** | **45,4%** |

De 141,8% en 2014 —cuando la Corte descargaba atraso— a **45,4% en 2025**: hoy
resuelve menos de la mitad de lo que le entra. Rango ×5,5 sobre 12 años, muy por
encima del backfill mínimo a dic-2023 que pide el proyecto.

Salvedad honesta: el 26,0% de 2018 es atípico y lo explica un salto de ingresos
del +89,4% ese año, no un colapso de la producción; y los valores por encima de
100% (2014, 2015, 2019) son años de descarga de atraso.

### Apoyo público: era viable, con otra cámara

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

### Éxito corporativo y bloqueo cautelar: la premisa del rechazo era falsa

ADR-0138 los rechazó por «sin campo de partes ni de resultado». Eso era cierto
**de SAIJ**, no del universo disponible. El Anuario de la CSJN clasifica:

- **Presentantes en cuatro categorías**: Gobiernos/Organismos y Dependencias
  Públicas (ANSES 93,03%, después AFIP, Caja de Retiros de las FFAA, gobiernos
  provinciales), **Empresas** (ART 79,39%, manufacturas 3,31%, transporte
  terrestre de pasajeros 2,41%), otra de personas jurídicas, y personas físicas.
- **Tipos de resolución** que incluyen explícitamente **«Admite Medida Cautelar»
  y «Rechaza medida cautelar»** (con Nulidad suman 0,42% de los resueltos 2025).

### Se fue a buscar el cruce a Tableau, y el resultado cierra el punto

Los tableros están publicados con `allow_view_underlying=false` y
`allow_summary=false` —el CSJN deshabilitó la descarga de datos— y la sesión de
vizql es de un solo uso: se consume al cargar la página y todo reintento
devuelve HTTP 410. Lo que sí quedó legible es **la estructura del libro**, que
confirma qué datos existen: «Duraciones Totales», «Duración por Secretarías»,
«Recursos resueltos según presentante», «Subtipos de presentantes», «Recursos
admitidos según materia y tipo de recurso».

No hizo falta insistir, porque el PDF trae lo mismo en prosa **y alcanza para
decidir que Éxito Corporativo no va** — ahora por una razón de fondo y con
datos, no por falta de campos.

Presentantes de los casos ingresados en 2025:

| categoría | % |
|---|---|
| Gobiernos, Organismos y Dependencias Públicas | 59,12% (ANSES = 93,03% de la categoría) |
| Personas físicas | 24,16% |
| **Empresas** | **7,02%** (ART = 79,39% de la categoría) |
| Otras organizaciones | 0,30% |
| sin dato | 9,39% |

**El campo de partes existe; lo que no existe es la población que el indicador
supone.** «Empresas» ante la CSJN son 7% de los ingresos, y dentro de ese 7% casi
cuatro quintos son **Aseguradoras de Riesgos del Trabajo apelando fallos
laborales** (manufacturas 3,31%, transporte de pasajeros 2,41%). No son las
grandes compañías litigando contra el Estado. A eso se suma que la clasificación
es de **ingresos** (quién presenta), no de resultados por parte.

### Bloqueo cautelar: la consulta existe y está cerrada con CAPTCHA

En la CSJN, «Admite/Rechaza medida cautelar» suman con Nulidad el 0,42% de los
resueltos de 2025 —del orden de 110 casos—, y además la Corte no es donde se
frenan las políticas: eso ocurre en primera instancia y en Cámaras.

ADR-0138 afirmó que eso «no tiene censo público». **Es falso, y hacía falta
verificarlo.** El Sistema de Consulta Web del PJN (`scw.pjn.gov.ar`) permite
exactamente la consulta que el indicador necesita:

- búsqueda **por parte**, no sólo por número de expediente;
- selector de **jurisdicción** entre 29, incluida **CAF — Cámara Nacional de
  Apelaciones en lo Contencioso Administrativo Federal**;
- selector de **rol** de la parte entre 41, incluido **DEMANDADO**.

O sea: *«Estado Nacional como demandado en el fuero contencioso administrativo
federal»* es una consulta válida del sistema.

**Pero cada consulta está protegida por CAPTCHA.** Al enviar la búsqueda el
sistema responde «Se debe completar el campo verificador para poder realizar la
consulta». Ahí se detiene el trabajo: no se resuelven CAPTCHAs, y además es el
operador declarando de forma explícita que no admite consulta automatizada.

La distinción importa. El indicador **no está cerrado porque la fuente no
exista**, sino porque el PJN decidió no abrirla a consulta automática. Si
habilitara una API o publicara el datastore, se construye al día siguiente.
Queda además una vía no agotada: **pedido formal de acceso a la información
pública**, que no sirve para un indicador de actualización periódica pero sí
para una nota metodológica o un informe puntual.

### Consecuencias, y la regla que hay que respetar

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
