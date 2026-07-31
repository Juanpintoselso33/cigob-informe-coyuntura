---
madr: 4
id: '0157'
estado: 'aceptado'
fecha: 2026-07-30
archivos: ['web/src/lib/fichas.ts']
ambito: 'capa de texto público (`web/src/lib/fichas.ts`) + guard nuevo'
---

# ADR-0157 — Guard de anclas de banda, y un mapeo público que estaba mal

- **Relacionados**: ADR-0156 (misma familia: texto público que caduca), el guard
  de pesos (`test_fichas_pesos.py`), ADR-0021 (puntaje interpolado)

## Contexto y planteo del problema

ADR-0156 cerró la deixis temporal y dejó declarado lo que NO cubría: **las anclas
de banda seguían sin guard**. El editor preguntó por qué. No había motivo, sólo
que no estaba hecho.

Es la misma clase de problema que los pesos, y con el mismo riesgo: este proyecto
recalibra anclas seguido —hay ADRs enteros dedicados a eso (0050, 0058/0059,
0061, 0063)— y el texto público que las publica se edita a mano.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

`tests/test_fichas_bandas.py` cruza contra el motor lo que cada ficha publica,
por los dos caminos que existen en el archivo:

1. el campo estructurado `anclas: { bandas: [{ banda: "≤ 1", puntaje: 100 }…] }`;
2. la frase «El puntaje del índice se asigna por bandas … → el más bajo.»

Verifica tres cosas: que los **puntajes** publicados sean los del motor, que los
**cortes** publicados sean sus umbrales reales, y que **todo indicador que puntúa
por bandas y tiene ficha publique las suyas** — porque son la mitad de la
explicación de por qué su puntaje es el que es.

Dos detalles de diseño:

- **el orden no importa**: varias fichas listan las bandas de peor a mejor y el
  motor las tiene al revés (`resultado_primario`,
  `costo_financiamiento_tesoro`). Exigir el mismo orden habría dado dos falsos
  positivos y la tentación de "arreglar" fichas que estaban bien;
- lleva **test de que el test mira algo**, contra el falso verde: si cambia el
  formato de `fichas.ts` y el parseo deja de encontrar bandas, los otros tres
  pasarían vacíos.

### Consecuencias

- 48 indicadores con bandas y ficha quedan cruzados contra el motor en cada
  corrida de tests.
- Los 5 sin ficha son los ocultos del snapshot, que por diseño no la tienen.
- **Lo que sigue sin guard**, y se declara: los pesos de dimensión citados en
  prosa («la dimensión pesa 25% del total»), que `test_fichas_pesos.py` excluye a
  propósito porque son otra afirmación. Es la tercera pieza de la familia.

## Más información

### El guard encontró un error público en su primera corrida

`gobernadores_alineamiento` no publicaba sus bandas, y en su lugar la ficha
afirmaba un mapeo **lineal** que el motor no usa:

> «La tensión crece cuando el apoyo se retira: 80% alineado → tensión 0 · 40% → 5
> · 0% → 10.»

El motor puntúa por bandas (>65 → 100 · 45-65 → 85 · 25-45 → 65 · 10-25 → 40 ·
≤10 → 10) con interpolación entre anclas (ADR-0021). De los tres puntos
publicados, **dos estaban mal**:

| gobernadores alineados | la ficha decía | el motor da |
|---|---|---|
| 80% | 0 | 0 ✓ |
| 40% | **5** | **3,0** |
| 0% | **10** | **9,0** |

El de 0% es el más informativo: el tramo más bajo puntúa **10 sobre 100**, no
cero, así que la tensión máxima de este indicador es 9 y no 10. La ficha
publicaba una escala que llegaba a un extremo que el indicador no puede alcanzar.

Corregido: la ficha ahora publica las bandas reales y describe el mapeo como lo
que es —por tramos, no lineal—, con el motivo del piso.
