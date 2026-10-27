---
madr: 4
id: '0359'
estado: 'aceptado'
fecha: 2026-10-16
cinturon: 'transversal'
archivos: ['scripts/archivo.py', '.github/workflows/mensual.yml']
modifica: ['0347']
relacionado: ['0348', '0361', '0372', '0374', '0376', '0377', '0378', '0379', '0385', '0386', '0387', '0388', '0390', '0391']
ambito: 'Publicación · informe.cigob.org rehace el mes publicado con la metodología vigente'
origen: 'Juan, 16-oct-2026, tras el #75 de Luis: «el mensual también se tiene que cambiar, son cambios metodológicos»'
---

# ADR-0359 — El informe del mes se lee con la metodología vigente

## Contexto y planteo del problema

ADR-0347 armó informe.cigob.org con el código de `main` y los dos archivos de datos
(`informe.json`, `series.json`) **copiados tal cual** de la última corrida nocturna del
mes. El código nuevo llegaba, pero el cálculo no: los índices y sus dimensiones ya venían
hechos dentro de esos archivos.

El 16-oct-2026 el pedido #75 de Luis juntó la inversión con la actividad en el índice
macro. En el seguimiento diario el índice quedó en 61,7 con cinco dimensiones; en
informe.cigob.org siguió en 60,3 con seis, y Luis no vio su cambio. Mientras tanto la foto
de septiembre en `/archivo/2026-09/` (ADR-0348) ya se reconstruía con el método de hoy:
el mismo mes se leía con dos varas.

## Opciones consideradas

- **Rehacer el mes publicado con el Monitor de hoy, como el archivo** — elegida.
- **Copiar el snapshot del mes y re-correr sólo `publicar.py`** — descartada: los índices
  los arma también `generar_informe.py` y la serie de «Cómo va la película» sale de
  `validacion_externa.py`; correr una parte deja el mes a medio método.
- **Dejar el mes congelado (ADR-0347)** — descartada por Juan: un cambio de método tiene
  que verse en el informe que se difunde.

## Decisión

- `archivo.py` separa la reconstrucción (`_reconstruido`: datos de `main` cortados al fin
  del mes, `validacion_externa` + `generar_informe` + `publicar` con el reloj en ese mes)
  del empaquetado del archivo. `archivo.py datos AAAA-MM` deja sólo `informe.json` y
  `series.json` del mes en `web/src/data/`.
- `mensual.yml`, al componer la rama `mensual`, usa `archivo.py datos <mes vigente>` en
  lugar de `mensual.py congelar`, e instala las dependencias del proyecto.

### Consecuencias

- informe.cigob.org y `/archivo/<mes>` muestran el mismo mes con el mismo método.
- Un cambio de pesos, bandas o dimensiones llega a informe.cigob.org en el rearmado que
  dispara el push o el pedido, sin esperar al mes siguiente.
- Un mes ya publicado puede cambiar de número cuando cambia el método, y también si una
  fuente revisó un dato de ese mes (los datos son los de hoy cortados al mes). Es el mismo
  criterio que el archivo desde ADR-0348.
- El rearmado tarda un poco más (unos 20 s locales de reconstrucción más la instalación).

### Confirmación

Probado en local el 16-oct-2026: `archivo.py datos 2026-09` deja `period` 2026-09 y el
índice macro en 61,7 con cinco dimensiones. Se verifica en informe.cigob.org después del
push.

## Más información

- ADR-0347: el informe mensual y el seguimiento diario.
- ADR-0348: el archivo de meses, reconstruidos con el Monitor de hoy.
