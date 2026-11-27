---
madr: 4
id: '0441'
estado: 'aceptado'
fecha: 2026-11-27
cinturon: 'transversal'
archivos: ['web/src/layouts/Layout.astro', '../../api/acceso.ts', '../../vercel.json']
supersede: ['0342', '0438']
ambito: 'Presentación · se saca el muro de acceso que pedía el mail'
origen: 'Juan, 27-nov-2026: «sacá el coso de mail definitivamente».'
---

# ADR-0441 — Se saca el muro de acceso

## Contexto y planteo del problema

Desde el 7-oct-2026 (ADR-0342) el Monitor pedía el mail antes de dejar leer, con una cookie para no volver a
pedirlo y una excepción para los agentes de IA (ADR-0438). Juan decidió sacarlo del todo.

## Factores de decisión

- Que el Monitor se lea sin ningún paso previo.
- Que los links de las difusiones de WhatsApp ya enviados sigan andando.

## Opciones consideradas

1. Sacar el muro y todo lo que lo sostenía.
2. Apagarlo con `PUBLIC_MURO=0` en Vercel y dejar el código.

## Decisión

**Opción 1.** Sale `MuroAcceso.astro`, el script de `<head>` de `Layout.astro`, `api/lector.ts` (recibía el mail),
`api/_acceso.ts` (la cookie `cigob_lector`) y las cabeceras de `vercel.json` que se la ponían a los agentes de IA.
`api/acceso.ts` queda sólo como redirección a la página, porque el `/r/` del bot arma los links de las difusiones
con esa ruta. Los mails ya guardados siguen en Neon, en la base del bot.

### Consecuencias

- Los eventos `muro_*` de GA4 dejan de llegar; el informe mensual de tráfico (ADR-0440) los muestra en cero.
- `scripts/archivo.py` sigue armando las fotos de meses viejos con `PUBLIC_MURO=0`, y el emisor sigue rechazando un
  archivo con el muro: esas fotos salen de commits que todavía lo tenían.

### Confirmación

`npm run build` sin `cg-muro` en `dist/`; `tests/test_archivo.py` sigue verificando que ninguna foto lo traiga.

## Pros y contras de las opciones

- **Opción 1.** A favor: no queda código muerto ni una cookie que nadie lee. En contra: volver a ponerlo es
  rehacerlo desde el historial de git.
- **Opción 2.** A favor: se revierte con una variable. En contra: deja código y funciones de API sin uso.

## Más información

ADR-0342 y ADR-0438 quedan superados.
