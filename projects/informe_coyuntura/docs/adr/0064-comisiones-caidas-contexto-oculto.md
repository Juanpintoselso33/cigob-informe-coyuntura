---
madr: 4
id: '0064'
estado: 'aceptado'
fecha: 2026-07-15
cinturon: 'politica'
indicadores: [poder_legislativo]
parametros: ['INDICADORES_CONTEXTO']
archivos: ['publicar.py']
relacionado: ['0045', '0048', '0062']
ambito: 'Cinturón política · ITCP · dimensión `poder_legislativo` · `publicar.py` (oculto vía `INDICADORES_CONTEXTO`)'
---

# ADR-0064 — comisiones_caidas sale del ITCP a seguimiento interno (fuente ciega a las sanciones del Senado)

## Contexto y planteo del problema

ADR-0062 demostró que el dataset `movimientos-de-proyectos` de HCDN solo
registra la vida del expediente **en Diputados**: una sanción definitiva que
ocurre en el Senado nunca aparece como movimiento "SANCION". Ese hallazgo
corrigió `eficacia_legislativa` y dejó **flaggeado** a `comisiones_caidas`,
que usa la misma consulta (`q="SANCION"`) para decidir si un proyecto con
dictamen "llegó" o "cayó".

Decisión editorial del usuario: **sacarlo** ("comisiones sin sanción
SACAR"), en vez de repararlo. Además del defecto de fuente, el indicador
arrastraba dos debilidades ya documentadas:

- Su recalibración (ADR-0045, cortes 96/97/98/99 sobre un rango observado
  de 94,7–99,8%) discriminaba décimas de un valor estructuralmente pegado
  al techo — con el numerador además subcontando sanciones del Senado, parte
  de ese "97-99% caído" era artefacto de medición, no señal.
- Solapa conceptualmente con `eficacia_legislativa`, que desde
  ADR-0061/0062/0063 mide el embudo proyecto→ley con fuente correcta
  (leyes-sancionadas) y cohorte madura.

## Opciones consideradas

- Repararlo (sanción vía leyes-sancionadas, como eficacia)
- Dejarlo puntuando hasta la próxima revisión editorial

## Decisión

1. `comisiones_caidas` pasa a `itcp.INDICADORES_CONTEXTO` → deja de puntuar
   y `publicar.py` lo oculta del snapshot (`POLITICA_OCULTOS`), mismo patrón
   que `rotacion_gabinete`/`protestas_caba` (ADR-0048) y `movilizacion_cepa`
   (ADR-0052). Se sigue relevando y cacheando como seguimiento interno; su
   serie sigue en `output/series/politica.csv`; su banda queda en
   `BANDAS_ITCP` como referencia histórica.
2. El 0,20 de peso interno liberado en `poder_legislativo` se reparte
   parejo: `ratio_dnu` 0,20→0,25 · `eficacia_legislativa` 0,25→0,30 ·
   `veto_quorum` 0,15→0,20 · `derrotas_legislativas` 0,20→0,25. Eficacia
   sigue primera (la medida más abarcativa y, tras la corrección de hoy, la
   más sólida); ratio_dnu y derrotas conservan su paridad; veto_quorum sigue
   último por ser la medida más estrecha.
3. Sale de `ITCP_SERIES` en `validacion_externa.py` (la reconstrucción
   histórica no incluye contexto) y su ficha se retira de la web (patrón de
   los ocultos: sin ficha; labels y descripciones internas se conservan).

### Consecuencias

- El ITCP queda con **10 indicadores puntuables** y 4 de contexto oculto
  (`rotacion_gabinete`, `protestas_caba`, `movilizacion_cepa`,
  `comisiones_caidas`).
- `poder_legislativo` queda 25/30/20/25 (ratio_dnu/eficacia/veto_quorum/
  derrotas).
- El ITCP y su reconstrucción histórica se regeneran en la corrida scoped;
  el efecto directo es quitar un componente que aportaba puntajes medios
  (~55-60 interpolado) con 6% del índice.
- Pendiente declarado: mostrar el cambio al editor CIGOB en la próxima
  revisión editorial del cinturón (mismo compromiso que ADR-0052).

## Pros y contras de las opciones

### Repararlo (sanción vía leyes-sancionadas, como eficacia)

Viable técnicamente, pero descartada por decisión editorial: aun reparado,
mediría un embudo (dictamen→ley) fuertemente correlacionado con el que
`eficacia_legislativa` ya mide con mejor diseño (cohorte madura), y su
métrica reparada exigiría además re-derivar la maduración de dictámenes —
una segunda cohorte madura para una señal casi duplicada.

### Dejarlo puntuando hasta la próxima revisión editorial

Descartada: publicar un indicador cuyo numerador se sabe roto (mismo
defecto demostrado en ADR-0062) contradice la regla de no sentarse sobre
métricas sabidas defectuosas antes del lanzamiento (precedente ADR-0045).

## Más información

### Precedentes directos

ADR-0062 (documentó el defecto de la fuente y dejó este indicador flaggeado) · ADR-0048/0051/0052 (patrón de contexto oculto) · ADR-0045 (su recalibración, ahora entendida como compensación de un numerador roto)
