---
madr: 4
id: '0347'
estado: 'aceptado'
fecha: 2026-10-07
cinturon: 'transversal'
archivos: ['scripts/mensual.py', 'web/src/layouts/Layout.astro']
relacionado: ['0342']
ambito: 'Publicación · el Monitor como informe mensual en informe.cigob.org y seguimiento diario interno aparte'
origen: 'Reunión del 6-oct-2026 (punto 8 de docs/261006_reunion_pendientes.md). Juan, 7-oct: arrancar ya, con la foto de septiembre.'
---

# ADR-0347 — El Monitor se publica como informe mensual

## Contexto y planteo del problema

El Monitor publicaba cada noche: `informe.cigob.org` mostraba lo que dejaba la
última corrida. La reunión del 6-oct-2026 decidió que la cara principal sea **el
informe del mes**, una foto fija, y que lo de cada noche pase a una URL interna.
Decidido entonces: la foto del mes es la última corrida nocturna del mes; se
publica un día fijo del mes siguiente (a definir); las fotos anteriores quedan
disponibles; la URL actual queda para el mensual; el muro (ADR-0342) va sobre el
mensual; el diario va en una URL larga, sin indexar.

## Factores de decisión

- Que lo que corrige el equipo (diseño, textos, cambios desde claude.ai) se vea
  en el mensual sin esperar un mes.
- Que los datos del mensual no se muevan entre una publicación y otra.
- Poder reconstruir cualquier mes publicado.

## Opciones consideradas

1. Rama `mensual` = código de `main` + los dos JSON del sitio congelados.
2. Rama `mensual` = el commit de la corrida tal cual (código y datos de ese día).
3. Un solo sitio con selector de mes.

## Decisión

**Opción 1.** El sitio lee sólo `web/src/data/informe.json` y `series.json`, así
que congelar esos dos archivos congela la foto entera.

- **Dos proyectos de Vercel.** `cigob-informe-coyuntura` (`informe.cigob.org`)
  publica desde la rama `mensual`. `cigob-seguimiento-a941210feb` publica `main`, con
  `PUBLIC_MURO=0` y `PUBLIC_SITIO=diario`, que agrega `noindex`; sin GA.
- **`scripts/mensual.py`** elige la foto: la última corrida del bot cuyo
  snapshot dice `period` = el mes. Se decide por el campo del snapshot y no por
  la fecha del commit: la corrida de las 00:30 del día 1 ya es del mes siguiente.
- **`.github/workflows/mensual.yml`** publica un mes nuevo (a mano, con la etiqueta
  `mensual-AAAA-MM`; un mes etiquetado no se pisa) y rearma la rama `mensual` en
  cada push a `main` y al terminar un cambio desde claude.ai.
- **Arranque (Juan, 7-oct):** ya, con la foto de septiembre (`mensual-2026-09`,
  corrida del 30-sep, commit `85f76d31`).

### Consecuencias

- `informe.cigob.org` muestra septiembre: con el Votómetro y sin la confianza en
  el Gobierno, porque así eran los datos ese día (ADR-0344 y ADR-0345 entran en el
  mensual de octubre).
- Los textos de metodología describen el método **vigente**; la foto de un mes
  viejo se calculó con el de entonces. Para leer el método de un mes, está la
  etiqueta.
- Un dato nuevo se verifica en el diario; `CLAUDE.md` lo dice en «Dos caras».
- El día fijo de publicación está pendiente: cuando se decida, va un `schedule`.

### Confirmación

Se construyó el código de hoy con la foto de septiembre: todas las páginas
cargan y la portada dice «Septiembre 2026». Después de cambiar la rama de
producción, se leyó en `informe.cigob.org` el mes y en el diario los datos del 7-oct.

## Pros y contras de las opciones

### Opción 1 — Código vivo, datos congelados

- Bien: las correcciones llegan al mensual al instante.
- Mal: el texto de metodología puede no coincidir con el método de un mes viejo.

### Opción 2 — El commit de ese día

- Bien: la foto es exacta, código incluido.
- Mal: el muro (7-oct) y cualquier corrección quedarían afuera hasta el mes siguiente.

### Opción 3 — Selector de mes

- Mal: más trabajo, y la reunión pidió dos URLs.

## Más información

- `docs/261006_reunion_pendientes.md`, punto 8.
- ADR-0342: el muro va sobre el mensual.
