---
madr: 4
id: '0439'
estado: 'aceptado'
fecha: 2026-11-26
cinturon: 'transversal'
archivos: ['../../vercel.json', 'web/astro.config.mjs', 'web/src/layouts/Layout.astro', 'web/public/robots.txt', 'scripts/aviso_slack.py', 'scripts/aviso_informe.py', 'scripts/aviso_cambio_claude.py']
relacionado: ['0342', '0347', '0440', '0442']
ambito: 'Presentación · monitor.cigob.org es la única dirección del Monitor; informe.cigob.org redirige'
origen: 'Juan, 26-nov-2026, al revisar el tráfico y el SEO: «1 seguro, es monitor la pagina».'
---

# ADR-0439 — monitor.cigob.org es la única dirección del Monitor

## Contexto y planteo del problema

Desde noviembre de 2026 el Monitor se difunde como monitor.cigob.org, pero informe.cigob.org seguía sirviendo el
mismo sitio con un 200 y ninguna página declaraba cuál era la principal. Google eligió informe.cigob.org (Search
Console, inspección del 26-nov-2026), así que aparecía con la dirección que no se difunde y repartía la señal
entre dos copias. El sitemap, el robots.txt, las URLs de Open Graph y los avisos de Slack también nombraban
informe.cigob.org.

## Factores de decisión

- Un solo nombre para la gente y para los buscadores.
- Que los links viejos a informe.cigob.org sigan andando.
- No tocar el armado de la rama `mensual` (ADR-0347).

## Opciones consideradas

1. Redirección 301 de informe.cigob.org a monitor.cigob.org en `vercel.json`, más canonical en cada página y
   `site` de Astro en monitor.cigob.org.
2. Sólo el canonical, dejando los dos dominios con 200.
3. Nada.

## Decisión

**Opción 1.** Para Google la redirección y el canonical son señales fuertes y el sitemap es débil; el canonical
solo deja dos copias que se pueden seguir enlazando por separado. La regla vive en `vercel.json`, que la rama
`mensual` hereda de `main`, y mira el host, así que no afecta al seguimiento diario. La de
`cigob-informe-coyuntura.vercel.app` pasa a ir directo a monitor.cigob.org, sin doble salto.

### Consecuencias

- La cookie del muro (`cigob_lector`, ADR-0342) es del host: quien la tenía en informe.cigob.org vuelve a ver
  el muro una vez en monitor.cigob.org. Eran 9 lectores al 26-nov-2026; el link de difusión del bot ya iba a
  monitor.cigob.org.
- El archivo de verificación de Search Console (`google9458216d8c787831.html`, ADR-0180) queda afuera de la
  redirección: si redirigiera, la propiedad informe.cigob.org perdería la verificación y su historial.
- Search Console tiene que sumar monitor.cigob.org como propiedad y recibir su sitemap. El historial de
  informe.cigob.org queda en la propiedad vieja.
- Los textos que todavía dicen «informe.cigob.org» (comentarios, ADRs viejos, el conector de la landing)
  siguen funcionando por la redirección.

### Confirmación

En producción: `curl -I https://informe.cigob.org/macro/` responde 308 a `https://monitor.cigob.org/macro/`, y
`https://monitor.cigob.org/` trae `<link rel="canonical" href="https://monitor.cigob.org/">` y un sitemap con
URLs de monitor.cigob.org.

## Pros y contras de las opciones

- **Opción 1.** A favor: una sola dirección y ninguna copia. En contra: el muro se reconoce de nuevo una vez.
- **Opción 2.** A favor: nada que redirigir. En contra: Google puede ignorar el canonical, y los links siguen
  partidos entre dos dominios.
- **Opción 3.** En contra: el sitio sigue apareciendo con la dirección que no se difunde.

## Más información

Investigación de SEO del 26-nov-2026 (recomendación 1). Tráfico de los 30 días anteriores: 125 usuarios en
informe.cigob.org y 69 en monitor.cigob.org.
