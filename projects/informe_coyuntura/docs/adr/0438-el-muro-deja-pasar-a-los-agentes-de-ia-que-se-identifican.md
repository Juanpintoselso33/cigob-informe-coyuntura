---
madr: 4
id: '0438'
estado: 'aceptado'
fecha: 2026-11-25
cinturon: 'transversal'
archivos: ['../../vercel.json', 'web/src/layouts/Layout.astro', 'web/src/components/MuroAcceso.astro', '../../api/_acceso.ts', '../../api/acceso.ts']
relacionado: ['0342']
ambito: 'Presentación · el muro de acceso no frena a los agentes de IA que se identifican'
origen: 'Juan, reunión del 20-nov-2026: «el muro tiene que dejar pasar a los agentes de IA». Investigado y aprobado el 25-nov-2026.'
---

# ADR-0438 — El muro deja pasar a los agentes de IA que se identifican

## Contexto y planteo del problema

El muro (ADR-0342) es una ventana que dibuja JavaScript; el contenido sigue en el HTML. Hay dos clases de
asistentes de IA:

- **Los que leen el HTML sin ejecutar JavaScript** (ChatGPT, Claude o Perplexity cuando abren un link o buscan,
  y los rastreadores): nunca ven el muro. Probado el 25-nov-2026 con sus user agents: todos reciben la página
  entera.
- **Los que manejan un navegador**: ven el muro, y con el muro abierto la página queda inerte, así que no la
  pueden leer hasta cerrarlo. Sólo dos se identifican: el navegador en la nube de ChatGPT, que firma cada
  pedido con Web Bot Auth (`Signature-Agent: "https://chatgpt.com"`); el de Google, cuyo user agent dice
  `Google-Agent`; Manus, que firma (`api.manus.im`) y se nombra (`Manus-User`), y Claude Cowork, que se presenta
  como `HeadlessChrome` y declara `navigator.webdriver`. Claude in Chrome, Comet, Grok, Dia, el uso de computadora
  de Claude y el navegador de la app de escritorio de ChatGPT usan un Chrome común y no se distinguen de una persona
  (privatrak.com, «We sent 23 AI agents to our website», oct-2026; natzir.com, «The State of AI Traffic
  Measurability», 2026).

## Opciones consideradas

1. Una regla de `vercel.json` que, ante esos agentes, responda con una cookie `cigob_lector=a`, y que el script de
   `<head>` también deje pasar a todo navegador con `navigator.webdriver`.
2. Middleware de Vercel que verifique la firma.
3. Nada: que cierren el muro con la cruz.

## Decisión

**Opción 1.** La regla mira el encabezado, sin verificar la firma: quien lo imite saltea el muro, y no importa,
porque el muro junta mails y no protege datos (ADR-0342). La verificación de Vercel (Bot Protection, BotID)
pide un plan pago, y un middleware correría en cada pedido de cada visitante.

La cookie llega con la propia página, así que el script de `<head>` la lee antes de pintar: `a` no ve el muro,
no renueva nada y se mide aparte en GA (`muro_reconocido` con `via=agente`). Dura un día; `api/acceso.ts` nunca
la convierte en `m`.

### Consecuencias

Los agentes de navegador que no se identifican siguen viendo el muro y pasan con la cruz, como cualquier
persona. Si otro agente empieza a firmar o a nombrarse en el user agent, se suma una regla igual.

### Confirmación

Con el muro prendido en local (25-nov-2026): con `a` no aparece, en la portada ni en un cinturón; sin cookie y
con `d` aparece; con `m` no. En producción, `curl` con `Signature-Agent: "https://chatgpt.com"` o con un user
agent `Google-Agent` recibe el `Set-Cookie`, y sin ellos no.
