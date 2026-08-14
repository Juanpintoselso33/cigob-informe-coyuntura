---
madr: 4
id: '0206'
estado: 'aceptado'
fecha: 2026-08-14
cinturon: 'vida'
archivos: ['scripts/publicar.py', 'scripts/generar_informe.py', 'tests/test_artefactos_coherentes.py']
relacionado: ['0060', '0178', '0205']
ambito: 'Coherencia entre el artefacto intermedio (schema público) y el snapshot que publica el sitio'
origen: 'Al sacar espíritu de época, generar_informe.py devolvió un global que no cuadraba; investigarlo destapó que los dos artefactos publicaban números distintos desde antes'
---

# ADR-0206 — Los dos artefactos publicados dicen lo mismo

## Contexto y planteo del problema

El informe publica **dos** cosas que un tercero puede leer:

| Artefacto | Lo escribe | Para qué |
|---|---|---|
| `output/informe.json` + `informe.md` | `generar_informe.py` | schema v1.0.0, declarado "para dev externo" |
| `web/src/data/informe.json` | `publicar.py` | el sitio y el archivo de BigQuery |

**Discrepaban, y en silencio.** Con la corrida de agosto de 2026:

| | vida cotidiana | score global |
|---|---:|---:|
| `output/informe.json` | 2,9 | 2,7 |
| `web/src/data/informe.json` | 6,9 | 3,5 |

Los otros tres cinturones coincidían exacto. El que se abría era vida
cotidiana, y la causa es estructural: **`generar_informe.py` no puede calcular
el ITVC.** Corre antes que `publicar.py` y sólo ve el caché del colector viejo
—3 indicadores y un score legacy—, mientras que el ITVC real se arma desde las
series persistidas y el colector nuevo, con 17 indicadores, y eso lo hace
`publicar.py`.

[[0060-generar-informe-recalcula-indices-desde-crudo]] estableció que
`generar_informe.py` recalcula los índices con el código vigente en vez de
confiar en el caché del colector. Registró tres: ITCM, ITCG e ITCP.
**Vida cotidiana quedó afuera**, y su `_recalcular_indice` devuelve el score
cacheado tal cual. La condición estaba escrita en la docstring de
`recomputar_vida_y_global` desde siempre —"el colector sigue emitiendo su score
legacy en el cache"— pero nadie cerró la consecuencia: el artefacto intermedio
publicaba ese número legacy y un global construido sobre él.

Cómo apareció: sacando espíritu de época ([[0205-espiritu-de-epoca-sale-del-tablero]]),
`generar_informe.py` devolvió 3,2 donde se esperaba 4,2. Hubo que frenar la
tarea e ir a `git show HEAD:output/informe.json` para descartar que fuera un
bug recién introducido. No lo era: ya estaba. **Ningún test miraba esto.**

## Factores de decisión

- Dos artefactos publicados del mismo mes no pueden decir números distintos.
- El camino de publicación es el código más delicado del repo; refactorizarlo
  de arrastre, dentro de otra tarea, es la forma de romper la portada.
- Lo que evita la reincidencia es un test, no un comentario.
- `publicar.py` no puede volver a escribir dentro del árbol durante los tests
  ([[0178-publicar-no-escribe-en-el-arbol-durante-los-tests]]).

## Opciones consideradas

- **Reconciliar el intermedio desde `publicar.py`, y guardarlo con un test** —
  elegida.
- **Mover la máquina del ITVC a un módulo compartido** y registrar vida
  cotidiana en `_INDICES_PARAMETRICOS` como los otros tres. Es el arreglo de
  fondo y queda pendiente: `_scoring_vida_itvc` arrastra `_itvc_indices`, el
  rebase por serie, los ajustes del analista, la robustez y la validación
  cruzada; son cientos de líneas entretejidas en un archivo de 2.200.
- **Que el intermedio deje de publicar `score` de vida y `score_global`.**
  Descartada: rompe el schema v1.0.0 que el propio archivo declara.
- **Dejarlo como estaba y documentarlo.** Descartada: son dos números públicos
  que se contradicen; documentar la contradicción no la saca de la web.

## Decisión

### 1. `publicar.py` reconcilia el intermedio al final

`_reconciliar_intermedio()` corre después de `recomputar_vida_y_global()` y le
devuelve a `output/informe.json` el `score` y el `estado` de cada cinturón y el
`score_global`, que son los que este script calcula de verdad. El `informe.md`
se **regenera** con `generar_informe.escribir_md()` sobre el dict ya corregido,
en vez de parchearle líneas al texto: el frontmatter lleva el global y es lo
primero que lee quien abre el archivo.

Imprime lo que cambió, para que la corrida deje rastro:

```text
[OK] intermedio reconciliado: vida_cotidiana 2.9→6.9 · global 3.2→4.2
```

### 2. Sólo cuando se publica de verdad

La reconciliación se saltea si está `CIGOB_SALIDA_WEB`. Con esa variable los
tests corren `publicar.py` fuera del árbol ([[0178-publicar-no-escribe-en-el-arbol-durante-los-tests]])
y escribir `output/` acá reintroduciría exactamente el defecto que aquel ADR
arregló: tests que se pisan el snapshot entre sí.

### 3. El arreglo de fondo queda pendiente, y dicho

Esto **no** es la solución: es la venda. Mientras el ITVC viva sólo dentro de
`publicar.py`, el intermedio va a seguir naciendo mal y corrigiéndose después.
El arreglo real es la opción descartada de arriba —módulo compartido, vida
cotidiana registrada en `_INDICES_PARAMETRICOS`— y se hace como tarea propia,
no de arrastre.

### 4. El guard que faltaba

`tests/test_artefactos_coherentes.py` compara los dos artefactos: mismo
conjunto de cinturones, mismo `score` por cinturón, mismo `score_global`, y que
el `.md` declare ese global en su frontmatter. Si alguien saca la
reconciliación, o si el arreglo de fondo se hace mal, falla acá.

### Consecuencias

- Los dos artefactos publicados coinciden.
- `output/informe.json` pasa a tener dos escritores, que es feo y está anotado
  como tal: es el costo explícito de no refactorizar el camino de publicación
  dentro de otra tarea.
- El archivo de BigQuery **no estaba afectado**: `bigquery_export.py` lee
  `web/src/data/informe.json`, o sea el lado correcto. Se verificó al
  encontrarlo.

### Confirmación

- `[OK] intermedio reconciliado: vida_cotidiana 2.9→6.9 · global 3.2→4.2` en la
  corrida del 2026-08-14.
- `tests/test_artefactos_coherentes.py` en verde, y la suite completa también.

## Pros y contras de las opciones

**Reconciliar desde publicar.py** (elegida)

- Bueno, porque los números públicos dejan de contradecirse hoy.
- Bueno, porque el test impide que la brecha se reabra en silencio.
- Malo, porque deja dos escritores sobre el mismo archivo.
- Malo, porque el intermedio sigue naciendo mal.

**Módulo compartido del ITVC**

- Bueno, porque arregla la causa: el intermedio nacería bien.
- Malo, porque toca el camino de publicación entero y no cabe dentro de otra
  tarea sin arriesgar la portada.

## Más información

- La brecha existía al menos desde que el ITVC pasó a calcularse en
  `publicar.py`; no se auditó hasta dónde llega hacia atrás en el histórico.
- `output/informe.json` está versionado, así que `git show <sha>:...` permite
  reconstruir qué decía cada corrida y, si hiciera falta, medir la brecha mes
  a mes.
