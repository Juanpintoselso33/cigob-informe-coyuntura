---
madr: 4
id: '0122'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'macro'
indicadores: [ipc_total]
ambito: 'ITCM · ficha del índice · ficha de `ipc_total`'
origen: 'Auditoría de consistencia macro, sección IV.2 (prioridad media)'
---

# ADR-0122 — El riesgo sistémico del deflactor IPC, declarado en la metodología

| **Apoyado en** | ADR-0078 (el error del deflactor deja de tratarse como independiente) |

## Contexto y planteo del problema

La auditoría de macro cierra con un pendiente de prioridad media:

> "El IPC deflacta la recaudación, el crédito, el IDM y la tasa real del IdC — la
> ficha del IPC lo declara. […] implica que el índice tiene menos fuentes
> independientes de las que aparenta: un error del INDEC se propagaría a 5 de los
> 13 indicadores. Vale documentarlo como riesgo sistémico en la metodología
> general, no sólo en la ficha del IPC."

Al revisarlo aparecieron dos cosas.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

Se declara el riesgo sistémico en los dos lugares:

- **Ficha del índice ITCM** (la "metodología general" que pedía la auditoría):
  cerca del 24% del índice depende de que la inflación esté bien medida, con la
  aclaración de que el IdM usa el IPC pero es inmune. Y que el análisis de
  robustez ya lo contempla: sortea un único error de inflación por escenario y lo
  propaga a los que lo heredan (ADR-0078), en vez de tratar cada falla como
  independiente.
- **Ficha del `ipc_total`**: una limitación que dice, desde el otro lado, que su
  peso real en el índice supera al nominal porque además deflacta a otros tres.

### Consecuencias

- Sólo texto de fichas; cero cambios de cálculo. El mecanismo que este texto
  describe (error de deflactor correlacionado en el Monte Carlo) ya existía desde
  ADR-0078; lo que faltaba era decirlo en la presentación.
- El número publicado (24%) se verificó contra el código: los pesos efectivos de
  los cuatro expuestos, con el IdM excluido por la misma regla que usa
  `sensibilidad.py`.

Con esto se cierran los dos pendientes de prioridad media/baja que quedaban de la
auditoría de macro. Los otros dos —la ambigüedad direccional del ICIP y la
limitación ingresos-vs-resultado de la recaudación— ya estaban declarados en sus
fichas (se verificó); este era el único que faltaba de verdad.

## Más información

### 1. La ficha del IPC NO lo declaraba

La auditoría afirmaba que "la ficha del IPC lo declara". Hoy no es cierto: las
limitaciones del IPC hablan de rezago, cobertura regional y ruido de mes suelto,
pero no de que el IPC sea el deflactor de otros indicadores. Y la **metodología
general** (ficha del índice ITCM) tampoco. El pendiente era real y completo.

### 2. La auditoría contó de más: son 4 indicadores, no 5

La auditoría lista `idm` (desequilibrio monetario) entre los deflactados. Usa el
IPC, sí, pero **es inmune al error del deflactor**: compara M3 real contra M2
real, y un error proporcional de inflación se cancela en el cociente. Eso ya
estaba establecido en el propio proyecto —ADR-0078 lo excluye explícitamente de
`EXPOSICION_DEFLACTOR_ITCM`—, sólo que nunca se había llevado a la declaración
pública.

Los indicadores realmente expuestos son cuatro: `ipc_total`, `recaudacion`,
`credito_privado` e `idc`. Su peso efectivo suma **24%**, no el ~31% que daría
contar al IdM.
