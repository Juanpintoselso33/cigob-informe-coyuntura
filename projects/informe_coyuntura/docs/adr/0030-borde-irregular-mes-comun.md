---
madr: 4
id: '0030'
estado: 'aceptado'
fecha: 2026-07-04
relacionado: ['0054', '0055']
ambito: 'Criterio de FAMILIA para todo indicador compuesto o deflactado cuyas fuentes publican con rezagos distintos (IdC, recaudación, IAI, ICIP — y los que se sumen)'
---

# ADR-0030 — Borde irregular: mes común puntuado + dato fresco provisorio

## Contexto y planteo del problema

Varias fuentes publican asincrónicamente (el "ragged edge" de la literatura de
nowcasting): el ICA sale ~2 semanas antes que el ISAC, la recaudación ~10 días
antes que el IPC que la deflacta. El barrido de macro (04-jul-2026) encontró
tres variantes del mismo defecto: titulares que mezclaban meses distintos sin
declararlo (IAI: ISAC de abril + BK de mayo etiquetado "mayo"; recaudación:
nominal de junio deflactado con IPC de mayo; IdC: stocks de junio con IPC de
mayo) y que además diferían del último punto de su serie.

## Factores de decisión

### Prácticas de referencia relevadas

- **Conference Board LEI**: los componentes no publicados se ESTIMAN con un
  modelo autorregresivo; el índice sale con datos reales+estimados y SE REVISA
  todos los meses al llegar los datos verdaderos (documentado en sus notas
  técnicas). Prioriza frescura al costo de revisiones permanentes.
- **Nowcasting (Giannone-Reichlin-Small, ECB, NY Fed)**: filtro de Kalman /
  factores dinámicos tratan el borde irregular como datos faltantes — misma
  familia: estimaciones modelo-dependientes que se revisan.
- **Panel balanceado**: truncar "a la fecha del componente menos oportuno" es
  el paso base incluso dentro de esos modelos, y lo que publican las oficinas
  estadísticas para índices oficiales.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Para un índice institucional de rendición de cuentas, las revisiones
retroactivas del valor publicado y los datos estimados por modelo son
inaceptables (mismos argumentos que descartaron X-13 en el ADR-0029). Criterio
de familia:

1. **El titular se calcula al último período COMÚN de todos los insumos**
   (panel balanceado) — y por construcción coincide con el último punto de la
   serie del modal.
2. **El insumo más fresco se muestra en el detalle como "provisorio, no
   puntúa"** — capta el valor informativo del enfoque LEI sin sus costos: el
   lector ve el dato nuevo, el índice no se contamina ni se revisa.
3. El mes común se declara en el detalle (`mes común: YYYY-MM`).

Aplicado a: IdC (ADR-0028), recaudación (ADR-0029), IAI e ICIP (este ADR).

### Consecuencias

- Los titulares pierden hasta un mes de frescura contra la alternativa de
  mezclar; a cambio, nunca se revisan y siempre igualan a su serie.
- Cualquier indicador compuesto nuevo debe nacer con este criterio.
- Si alguna vez se quisiera un ITCM "nowcast" (con imputación tipo LEI), sería
  un producto SEPARADO del índice publicado, nunca el mismo número.
