# Reunión del 6-oct-2026: pendientes del Monitor del Plan de Gobierno

## 1. ✅ Muro de acceso al informe (vence el 13-oct-2026; publicado el 7-oct, ADR-0342)

Poner un muro delante del contenido del informe de coyuntura. La idea inicial es un
popup que pida el mail para dejar ver el contenido.

Decidido (Juan, 7-oct):

- **Dónde va**: en la portada, el hero con el score global se lee libre y el muro **salta al
  bajar y salir del hero**; cinturones, fichas y metodología lo muestran al entrar.
- **Qué tan cerrado**: **solo tapa la pantalla**. Los datos siguen en el HTML y el JSON
  públicos; alcanza para juntar mails y no cambia cómo se publica.
- **Cómo se recuerda**: **en el navegador**. Quien deja el mail no lo vuelve a dejar en
  ese navegador; si cambia de dispositivo o borra los datos, lo deja de nuevo.
- **Dónde se guardan los mails**: en **Neon, la base del bot de WhatsApp**, tabla
  `lectores`, junto a los contactos de la difusión.

Pendiente para después (Juan, 7-oct): **mejorar la persistencia**, que quien ya dejó el
mail no tenga que volver a dejarlo al cambiar de navegador o de dispositivo.

Persistencia: resuelta el 7-oct (ADR-0342, investigación en
`docs/261007_muro_persistencia_opciones.md`): cookie del propio sitio de 400 días, link de
difusión que deja entrar directo, «con tu mail alcanza» y un solo dominio.

**Pendiente, para que Juan lo mire después:**

- **Lo legal (Ley 25.326):** inscribir la base de lectores en el Registro Nacional de Bases de
  Datos, y resolver el consentimiento de la transferencia a EE.UU. (Neon y Vercel guardan ahí los
  datos), con consentimiento expreso o cláusulas contractuales.
- **Ingreso con Google (One Tap)**, la opción 21 de la investigación: un toque en Android y el mail
  verificado.
- **Marcar `muro_enviado` como evento clave en GA** (Administrar → Eventos → Eventos recientes →
  estrella). El 7-oct se mandó un evento de prueba desde la torre (`modo=prueba`, porque esta Mac
  bloquea Google Analytics en `/etc/hosts`); GA lo registró en tiempo real, pero la lista de eventos
  recientes tarda hasta 24 h en mostrarlo.
- **Probar de punta a punta el link de difusión** (`/r/` del bot → `/api/acceso` del Monitor)
  con la primera difusión real del Monitor; el tramo del Monitor ya se probó con un token real.

## 2. ✅ Cambios al Monitor desde claude.ai: conector, Proyecto y repo

Que el equipo pida cambios al Monitor conversando en claude.ai. **Cerrado el 7-oct**: el
conector de la landing (herramientas `monitor_*`) y el workflow `cambios-desde-claude.yml`,
que mergea solo, andan en producción (#54, #55 y #56 entraron por ahí). El Proyecto de
claude.ai del Monitor está armado y Luis ya lo usó.

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

## 3. ✅ Entregarle a Luis el listado de cambios del informe

Entregado por Juan (confirmado el 7-oct).

Luis lo pidió hace un tiempo y todavía no se entregó. Hay que armar el listado de cambios
del informe (qué cambió y desde cuándo) y mandárselo.

- Falta ubicar el pedido original: no aparece en el Slack de CIGOB de septiembre para acá.
  Puede haber sido por WhatsApp o en una reunión.
- De dónde sale el material: el historial de git de `main` y los ADR aceptados en el período.

## 4. Retomar el Votómetro hecho por nosotros: ver si es viable

**Fuera del Monitor** (Juan, 7-oct): es otro producto y se sigue aparte.

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

## 5. ✅ Monitor: sacar el Votómetro y sumar el ICG de Di Tella a vida cotidiana (publicado el 7-oct, ADR-0344 y ADR-0345)

Hecho en `96c88398`, con la corrida manual `e174aeb0`. El 7-oct el seguimiento diario ya
muestra «Confianza en el Gobierno» y no muestra el Votómetro.

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

**En pausa** (Juan, 7-oct).

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

## 7. ✅ Listado de fuentes a revisar, para buscarles alternativa (relevado el 10-oct)

**Hecho el 10-oct**: el barrido completo de los 67 indicadores, cruzado con 46 corridas
nocturnas en BigQuery y 33 logs de Actions, y las alternativas de cada fuente floja están en
`docs/pendientes-datos.md` §1 (que reemplaza la lista vencida del 30-jun). Lo que surgió:
en seis de las trece la fuente anda y lo que falla es el colector; y `desafios_legislativos`
no se actualiza desde CI desde el 31-jul (sólo con corridas manuales), justo antes de la
sesión del 15-oct por el DNU 70/2023. Falta decidir qué se arregla primero.

Lo que sigue es el planteo original del 6-oct.

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

## 8. ✅ Concretar el informe mensual (publicado el 7-oct con la foto de septiembre, ADR-0347)

El Monitor del Plan de Gobierno pasa a tener dos caras:

- **El informe del mes**: la foto fija del mes anterior. Es la versión principal.
- **El seguimiento diario**: en otro link, lo que hoy publica la corrida de cada noche.

Decidido (Juan, 6-oct):

- **La foto del mes es la última corrida nocturna del mes.**
- **Se publica un día fijo del mes siguiente**, todavía por definir.
- **Las fotos anteriores quedan disponibles**: cada mes con la suya. Todas las corridas ya
  quedan en git y en BigQuery (`corridas`, `origen = 'cron'`), así que las viejas se pueden
  reconstruir.
- **La URL actual (`cigob-informe-coyuntura.vercel.app`) queda para el mensual.**
- **El seguimiento diario pasa a una URL larga y difícil de adivinar** (de Vercel, GitHub
  o similar) y por ahora es **solo para uso interno**.

  Una URL difícil de adivinar no es privada: alguien la reenvía y queda abierta. Como
  mínimo, que no la indexen los buscadores (`noindex` y fuera del sitemap). Si tiene que
  ser privada de verdad, la protección de deploys de Vercel ya pide login en las URLs por
  deploy, aunque solo dejaría entrar a quienes estén en el equipo de Vercel.
- **El muro de acceso (punto 1) va sobre el mensual.**

Decidido (Juan, 7-oct): el mensual lleva **los datos y la lectura editorial del equipo**
(el lugar ya existe: `web/src/contenido/lectura-del-mes/<mes>.md`; sin texto, va la síntesis
automática). Comparación con el mes anterior y descargas, después.

Falta definir, **más adelante** (no es decisión de ahora): qué día del mes siguiente se publica.
