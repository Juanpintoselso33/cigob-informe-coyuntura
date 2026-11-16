---
madr: 4
id: '0432'
estado: 'aceptado'
fecha: 2026-11-16
cinturon: 'politica'
indice: 'ITCP'
indicadores: [eficacia_legislativa, votos_sobre_bancas]
archivos: ['scripts/hcdn_buscador.py', 'scripts/politica.py', 'scripts/descargar_series.py', 'tests/test_hcdn_buscador.py', 'web/src/lib/fichas.ts']
relacionado: ['0061', '0062', '0063', '0431', '0434', '0436']
ambito: 'Fuente de respaldo de `eficacia_legislativa` y `votos_sobre_bancas` mientras el CKAN de Diputados esté caído'
origen: 'Juan, 16-nov-2026: «a y b» (ventana de 45 días y migración al buscador nuevo).'
---

# ADR-0432 — Si el portal de datos de Diputados no responde, eficacia y votos sobre bancas se leen del buscador de proyectos

## Contexto y planteo del problema

`datos.hcdn.gob.ar` (CKAN) no responde desde el 4-nov-2026 ([[0431]]). La Cámara publica
los mismos expedientes en el buscador nuevo de `www.hcdn.gob.ar/proyectos/buscador/`, que
tiene una API JSON: proyectos con expediente, autor, fecha de publicación en el Trámite
Parlamentario, número de ley, dictámenes (cámara, número y año de Orden del Día, fecha) y
movimientos con fecha. La clave `pap-NNNNNN` del buscador es el `PROYECTO_ID` `HCDNNNNNNN`
del CKAN. Al 16-nov sus datos llegan al 5-nov.

Tiene dos diferencias con el CKAN:

- **No separa los mensajes del Ejecutivo que traen un proyecto de ley de los avisos.** Todos
  son «MENSAJE». El CKAN distinguía «MENSAJE Y PROYECTO DE LEY» ([[0062]]).
- **No trae la numeración del Senado** (`CD-NN/AA`), con la que `votos_sobre_bancas` cruza
  las votaciones del Senado.

## Factores de decisión

- Mismo número que el CKAN donde los dos se puedan comparar.
- No cambiar retroactivamente puntos ya publicados.
- Lo que el buscador no sabe queda pendiente, no se adivina.

## Opciones consideradas

- **El CKAN primero y, si no responde, el buscador, con la regla de título (elegida).**
- Reemplazar el CKAN del todo: perdería la numeración del Senado y la regla de 14 meses de
  la serie que no coincide (ver abajo).
- Separar proyectos y avisos por las comisiones a las que se giran: los avisos de DNU
  también se giran, a la Bicameral de Trámite Legislativo; no separa.

## Decisión

`scripts/hcdn_buscador.py` lee el buscador con pausa entre pedidos (corta con 429).

- **Proyecto de ley del Ejecutivo:** sigla PE o JGM, ingresado por Diputados, con fecha de
  publicación, y cuyo título **no** empieza con «Comunica…», «(Se) remite…» o «Solicita…» (los
  avisos de DNU y decretos delegados, los informes y los pedidos de acuerdo). Se valida con
  la auditoría de cohorte del 8-sep-2026: salen los mismos 14 proyectos y ninguno de más. La
  fecha de publicación pasa por las mismas rectificaciones del Trámite Parlamentario
  (`_fecha_publicacion_proyecto`).
- **Sanción definitiva:** el último movimiento con fecha que dice «… Y SANCION» (no «MEDIA
  SANCION») de los proyectos con número de ley. Un proyecto con número de ley y sin esa
  fecha hace fallar el cálculo, como en el CKAN.
- **Card de eficacia:** misma cohorte madura ([[0061]]). Con el buscador da 27,3 % (3 de
  11), igual que la card del CKAN del 4-nov.
- **Serie de eficacia:** coincide punto por punto con la del CKAN de enero a noviembre de
  2026. Antes le faltan uno a tres mensajes por cohorte, así que los meses anteriores a
  enero de 2026 se conservan como los publicó el CKAN (`EFICACIA_BUSCADOR_DESDE`). Las
  cohortes nuevas son de proyectos publicados desde 2025, que coinciden.
- **Votos sobre bancas:** para cada Orden del Día de Diputados que hace falta, el buscador
  da sus proyectos y dictámenes; un proyecto es del Ejecutivo si su autor es «PODER
  EJECUTIVO», también si entró por el Senado. Las votaciones del Senado que necesitan la
  numeración `CD` quedan pendientes (`origen_pe` sigue en None) en vez de darse por no
  ejecutivas.

### Consecuencias

- Votos sobre bancas: la votación del 21-oct-2026 de la ley de inviolabilidad de la
  propiedad privada (O.D. 448, proyecto del Ejecutivo que entró por el Senado) se resuelve
  y entra al promedio: la card pasa de 141,5 (dos votaciones de agosto) a 124 diputados a
  favor, por debajo de la mayoría absoluta de 129. La O.D. 85 (tratado de patentes, agosto)
  sigue sin dictamen en el buscador y queda pendiente.
- Si el buscador tampoco responde desde los runners, la ventana de [[0431]] sigue cubriendo
  hasta el 19-dic y el refresco se hace desde una IP argentina.

### Confirmación

`tests/test_hcdn_buscador.py`.

## Pros y contras de las opciones

- Elegida: el mismo número donde se puede comparar y nada adivinado; la regla de título
  depende de cómo redacta la Cámara.
- Reemplazo total: más simple, pero cambia la historia publicada.
- Comisiones: no separa.

## Más información

Validación del 16-nov-2026: 1.258 mensajes PE y JGM desde 2021; la serie de eficacia
reconstruida con el buscador coincide con `output/series/politica.csv` en los 11 meses de
enero a noviembre de 2026.
