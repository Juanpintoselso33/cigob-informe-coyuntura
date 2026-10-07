---
madr: 4
id: '0342'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'transversal'
archivos: ['web/src/components/MuroAcceso.astro', 'web/src/layouts/Layout.astro', 'web/tools/emitir-artifact.mjs']
relacionado: ['0347']
ambito: 'Presentación · muro de acceso que pide el mail antes de dejar leer el Monitor'
origen: 'Reunión del 6-oct-2026 sobre el Monitor del Plan de Gobierno (punto 1 de docs/261006_reunion_pendientes.md). Juan cerró las decisiones el 7-oct-2026.'
---

# ADR-0342 — Un muro de acceso que pide el mail

## Contexto y planteo del problema

La fundación quiere saber quién lee el Monitor. La reunión del 6-oct-2026 pidió
un popup que pida el mail antes de dejar ver el contenido, con fecha el
13-oct-2026. El sitio es estático (Astro en Vercel, sin servidor propio) y los
datos se publican en HTML y JSON abiertos.

## Factores de decisión

- Llegar al 13-oct sin cambiar cómo se publica ni cómo entra un cambio pedido
  desde claude.ai.
- Que la portada siga funcionando como vidriera: se comparte, se indexa y es lo
  primero que ve quien llega desde una difusión.
- Que el muro no deje a nadie afuera por un error nuestro.
- Tener todos los contactos de la fundación en un solo lugar.

## Opciones consideradas

1. Muro que sólo tapa la pantalla, del lado del navegador.
2. Muro que esconde los datos en el servidor (middleware de Vercel).
3. Sin muro, con un formulario opcional para dejar el mail.

## Decisión

**Opción 1**, con cuatro reglas (Juan, 7-oct-2026):

1. **Dónde salta.** En la portada, el hero se lee libre y el muro aparece cuando
   la persona baja y el hero sale de la pantalla. En cinturones, fichas y
   metodología aparece al entrar.
2. **Qué tan cerrado.** Sólo tapa la pantalla: el contenido sigue en el HTML,
   los buscadores lo indexan igual y quien abra la consola lo ve. Es para juntar
   mails, no para proteger datos.
3. **Cómo se recuerda.** En el navegador (`localStorage`, clave
   `cigob-muro-v1`). Quien cambia de dispositivo o borra los datos lo deja de
   nuevo. Si el guardado falla —caída, red, freno—, la persona entra igual; sólo
   un mail que el servidor rechaza por mal escrito se corrige.
4. **Dónde se guardan los mails.** En Neon, la base del bot de WhatsApp
   (repo `cigob-bot`, tabla `lectores`, endpoint `POST /api/lector`), junto a
   los contactos de la difusión. Desde el 7-oct (Juan) los mails se guardan
   también para difusión; la política de privacidad del bot lo dice.

`PUBLIC_MURO=0` apaga el muro en el build. Lo usan el seguimiento diario interno
(el muro va sobre el informe mensual) y el informe en un solo archivo, cuyo
emisor aborta si encuentra el muro.

### Segunda vuelta (7-oct-2026, el mismo día)

Juan pidió el formato de los popups de diarios y newsletters:

- **Más grande y en dos paneles.** A la izquierda, un panel de marca con el logo
  de CiGob (los anillos, «CiGob» y «Ciencias para gobernar», como en el menú),
  el nombre del Monitor y lo que trae. A la derecha, el formulario. En celular
  se apila, con la marca arriba y compacta.
- **Mail obligatorio; nombre y teléfono optativos.** Van a `lectores.nombre` y
  `lectores.telefono`. Un dato vacío no borra el que ya estaba; uno nuevo pisa
  al anterior. El teléfono se guarda como se escribió, sin validar el formato,
  si tiene al menos seis dígitos.
- **Una cruz para cerrar, y Escape.** Cierran el muro por el resto de la visita
  (`sessionStorage`, clave `cigob-muro-cerrado`); en la próxima visita lo vuelve
  a pedir. Esto relaja la regla 3: cerrar con la cruz también deja leer, sin
  dejar el mail.

### Persistencia (7-oct-2026, tercera vuelta)

Investigación completa en `docs/261007_muro_persistencia_opciones.md` (38
opciones). El hallazgo: Safari borra a los 7 días sin visitas el `localStorage`
y las cookies escritas por JavaScript, así que en iPhone el muro volvía a
aparecer todos los meses. Juan eligió cuatro piezas:

1. **Cookie del servidor del propio sitio.** El popup manda el mail a
   `/api/lector` del Monitor (función de Vercel en `api/lector.ts`, raíz del
   repo), que lo reenvía al bot y responde con `cigob_lector`, 400 días. JS
   nunca la escribe. `api/acceso.ts` la renueva una vez por visita y la crea a
   quien sólo tenía el `localStorage` de antes.
2. **Link de difusión con token.** El `/r/<token>` del bot manda a
   `/api/acceso?t=<token>&next=…`; si el bot reconoce el token, se deja la
   cookie y se redirige a la página limpia. Vale en cualquier dispositivo,
   también en incógnito.
3. **«¿Ya te registraste? Con tu mail alcanza»** en el popup, y el aviso
   mínimo de la Ley 25.326 (responsable, finalidad, cómo pedir acceso o baja).
4. **Un solo dominio:** `cigob-informe-coyuntura.vercel.app` redirige a
   `informe.cigob.org` (las cookies son por dominio).

GA4: `muro_reconocido` con `via` = `cookie` (la cookie salvó a quien Safari le
borró el `localStorage`) o `difusion`. Queda para después el ingreso con Google.

### Consecuencias

- Buena: sale en días, sin tocar el deploy ni el conector, y la portada sigue
  abierta.
- Mala: cualquiera que sepa puede saltarlo, y quien cambia de navegador vuelve a
  ver el muro. Juan dejó pendiente (7-oct) mejorar la persistencia.

### Confirmación

Probado con el navegador contra el build: la portada no muestra el muro al
entrar y sí al salir del hero; un cinturón lo muestra al entrar; un mail mal
escrito se marca; uno válido deja entrar, queda en `lectores` y no se vuelve a
pedir al recargar ni en otra página.

## Pros y contras de las opciones

### Opción 1 — Tapa la pantalla

- Bien: no cambia la publicación; la portada sigue indexable.
- Mal: no protege los datos.

### Opción 2 — Esconde los datos en el servidor

- Bien: no se puede saltar.
- Mal: obliga a pasar el sitio a renderizado en servidor o middleware, y a que
  el conector de claude.ai y las fichas pasen por ahí; no llega al 13-oct.

### Opción 3 — Formulario opcional

- Bien: cero fricción.
- Mal: casi nadie lo completa; no responde a lo que pidió la reunión.

## Más información

- `docs/261006_reunion_pendientes.md`, punto 1 (decisiones) y punto 8 (informe
  mensual y seguimiento diario).
