# Reunión del 6-oct-2026: pendientes del Monitor del Plan de Gobierno

## 1. Muro de acceso al informe (vence el 13-oct-2026)

Poner un muro delante del contenido del informe de coyuntura. La idea inicial es un
popup que pida el mail para dejar ver el contenido.

Falta definir:

- **Dónde va**: qué páginas o secciones quedan detrás del muro y cuáles siguen abiertas.
- **Cómo se recuerda el acceso**: que quien ya dejó el mail no tenga que volver a dejarlo.
- **Dónde se guardan los mails** que se juntan.
- **Qué tan cerrado**: un muro "blando" solo tapa la pantalla (los datos siguen en el
  JSON público); uno "duro" los esconde en el servidor.

## 2. Cambios al Monitor desde claude.ai: conector, Proyecto y repo

Que el equipo pida cambios al Monitor conversando en claude.ai. Esto ya está hecho y
probado: el conector de la landing (herramientas `monitor_*`) y el workflow
`cambios-desde-claude.yml`, que mergea solo. Quedó en pausa el 1-oct. Para cerrarlo falta:

- **Probarlo desde claude.ai** (por ejemplo, `monitor_ver_dato iai`). Si responde
  «GitHub respondió 404», el token de producción no llega al repo del informe: hay que
  crear un token fine-grained (Contents + Pull requests, lectura y escritura, en los dos
  repos) y cargarlo en Vercel.
- **Armar el Proyecto de claude.ai** para el Monitor, aparte del de la landing, con sus
  instrucciones: consultar el dato antes de opinar sobre un número, después
  buscar → leer → proponer el cambio, y `monitor_ver_cambios` para saber si ya salió.
  Desde el 6-oct todo se publica solo, sin esperar aprobación.
- **Avisarle a Luis** y al equipo cómo se usa.
- ✅ **Que un merge con algo roto avise en el momento.** Ya está hecho: `dd85d9f4`
  (`scripts/aviso_cambio_claude.py`), en `main`. Avisa en `#monitor-alertas` cuando:
  - pruebas, tipos o build en rojo;
  - el deploy de Vercel que sigue al merge sale con ERROR, o la página de producción no
    carga;
  - el cambio dispara `data-pipeline.yml` y esa corrida falla;
  - el cambio toca algo sensible aunque pase todo: cálculo, bandas o config de un índice,
    o borra o renombra una card;
  - cambia mucho de golpe: más de 5 archivos o 300 líneas en un solo pedido.

  Cada aviso dice quién lo pidió, qué cambió, qué falló y el link al PR. Lo que pase
  después del merge va en el hilo del primer aviso. Un cambio de texto que pasa todo no avisa.

## 3. Entregarle a Luis el listado de cambios del informe

Luis lo pidió hace un tiempo y todavía no se entregó. Hay que armar el listado de cambios
del informe (qué cambió y desde cuándo) y mandárselo.

- Falta ubicar el pedido original: no aparece en el Slack de CIGOB de septiembre para acá.
  Puede haber sido por WhatsApp o en una reunión.
- De dónde sale el material: el historial de git de `main` y los ADR aceptados en el período.

## 4. Retomar el Votómetro hecho por nosotros: ver si es viable

Retomar el Votómetro armado por nosotros y ver si se puede sostener.

Cómo está hoy: el Votómetro se publica en ediciones mensuales en la web de CiGob, que se
suben desde un archivo de Drive con el conector de la landing. El informe lee la edición
más reciente con `politica.py` y de ahí sale el indicador `votometro_ventaja_lla`
(«Ventaja LLA−PJ», en puntos porcentuales) del cinturón político.

Para la viabilidad hay que mirar de dónde saldrían los datos, cada cuánto se actualizarían,
quién lo mantiene y qué pasa con la serie histórica y el indicador si cambia la fuente.

Qué tiene que tener el Votómetro propio:

- **Buscador de encuestas**: juntar las encuestas que se publican (consultora, fecha,
  muestra, método, resultados) en un solo lugar donde se puedan buscar y filtrar.
- **Qué actores relevantes están sonando, sin encuestas**: medir la presencia de figuras
  políticas por otro lado (menciones en medios, búsquedas, redes) y definir cómo se hace,
  con qué fuentes y qué tan seguido.
- **Explorar una parte con apuestas**: mercados de predicción (Polymarket, Kalshi o
  similares) sobre elecciones argentinas. Ver si hay mercados con volumen suficiente y
  qué dice la ley local.

## 5. Monitor: sacar el Votómetro y sumar el ICG de Di Tella a vida cotidiana

- **Sacar el Votómetro de todos los cinturones.** Hoy aparece solo en Política: es la
  card `votometro_ventaja_lla` y puntúa en el ITCP, dentro de la dimensión
  «imagen y voto». Hay que ver cómo queda esa dimensión sin él, sacarlo de las series
  y de las fichas, y escribir el ADR. La guarda de fichas (ADR-0220) lo exige.
- **Agregar el Índice de Confianza en el Gobierno (ICG) de la UTDT a vida cotidiana**,
  como card que puntúa en el ITVC. La regla es que, si no puntúa, no es card. La serie
  ya se descarga (`icg_utdt` en `descargar_series.py`), pero hoy solo se usa como
  referencia externa para validar el ITCP y el ITVC, no como card. Si entra al ITVC
  deja de servir para validarlo, porque se estaría comparando el índice consigo mismo:
  hay que sacarlo de esa validación. Antes de fijar el tope de demora, medir hasta qué
  mes llega la serie.

## 6. Sesiones caídas: el dato de las que llegan al recinto

Comentario de la reunión: en «Sesiones caídas por falta de quórum» (`veto_quorum`,
Política) tendría que estar el dato de las sesiones que van al recinto.

Cómo está hoy: sale del índice oficial de sesiones de Diputados y de las versiones
taquigráficas. Cuenta las reuniones de los últimos 12 meses que quedaron en minoría. Al
6-oct da 1 de 10 (10 %, verde), con la última reunión el 9-sep. No muestra cuáles fueron
ni el detalle de cada una, y no incluye al Senado.

Falta precisar qué se pide. Puede ser mostrar, para cada sesión convocada al recinto, si
hubo quórum, con cuántos presentes y quién la pidió. O cambiar qué se cuenta: solo las
sesiones convocadas al recinto, o sumar al Senado. Lo primero cambia la ficha; lo segundo
cambia el indicador y necesita un ADR.

## 7. Listado de fuentes a revisar, para buscarles alternativa

Armar la lista de las fuentes flojas (carga manual, datos atrasados, que se caen) y
buscarle a cada una una alternativa.

Punto de partida: un primer barrido del snapshot del 6-oct. De 67 indicadores publicados,
60 son automáticos, 5 semiautomáticos y 2 manuales. Estos diez son candidatos:

| Indicador | Cinturón | Cómo se obtiene | Atrasado | Dato al | Fuente |
|---|---|---|---|---|---|
| `votometro_ventaja_lla` | Política | automático | sí | 2026-07-22 | Votómetro CIGOB (se saca, punto 5) |
| `apoyo_empresario` | Política | semiautomático | sí | 2026-08-01 | Comunicados de la UIA |
| `adhesion_reformas_provincial` | Política | automático | sí | 2026-10-05 | MAGyP, adhesiones y leyes provinciales |
| `desafios_legislativos` | Política | semiautomático | sí | 2026-09-29 | Actas de Diputados y Senado + InfoLeg |
| `velocidad_resolucion` | Política | manual | no | 2025-12-31 | Anuario de la CSJN |
| `cobertura_judicial` | Política | semiautomático | sí | 2026-09-01 | Padrón de magistrados, Min. de Justicia |
| `fal_modernizacion_laboral` | Gestión | semiautomático | no | 2026-10-06 | InfoLeg |
| `privatizaciones` | Gestión | manual | no | 2026-09-08 | Boletín Oficial y CNV |
| `concesiones_infraestructura` | Gestión | automático | sí | 2026-10-05 | CONTRAT.AR + Boletín Oficial |
| `protocolo_antipiquetes` | Gestión | semiautomático | no | 2025-12-31 | Diagnóstico Político |

Falta completar:

- Vida cotidiana y Macro: este barrido no los cubre, porque guardan sus indicadores con
  otra estructura en el snapshot.
- Las fuentes que caen seguido aunque hoy se vean frescas: SAIJ, que bloquea a los
  runners, Google Trends y lo que use cache seguido en los logs del nocturno.
- `docs/pendientes-datos.md` tiene una lista parecida pero está vencida (30-jun):
  actualizarla en vez de armar otra.

## 8. Concretar el informe mensual

El Monitor del Plan de Gobierno pasa a tener dos caras:

- **El informe del mes**: la foto fija del mes anterior. Es la versión principal.
- **El seguimiento diario**: en otro link, lo que hoy publica la corrida de cada noche.

Falta definir:

- **Qué corrida es la foto del mes**: la última del nocturno de cada mes, o una fecha de
  corte fija. Todas las corridas ya quedan en git y en BigQuery (tabla `corridas`,
  filtrando `origen = 'cron'`), así que una foto se puede reconstruir aunque llegue tarde.
- **Cómo se publica**: una página por mes con su propia URL, para que la foto vieja siga
  disponible, o una sola página que se reemplaza. Y cuál de los dos queda en la URL actual.
- **Qué lleva el mensual además de los datos**: texto de análisis, comparación con el mes
  anterior, el PDF o el informe en un solo archivo (`emitir-artifact.mjs`).
- **Cómo se cruza con el muro de acceso (punto 1)**: cuál de las dos caras queda detrás
  del mail.
