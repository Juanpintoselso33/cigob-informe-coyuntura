---
madr: 4
id: '0108'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
archivos: ['validacion_externa.matriz_redundancia_itvc', '_EscalaIdentidad']
extiende: ['0085']
relacionado: ['0223', '0224', '0225', '0226', '0231', '0233']
ambito: 'ITVC · card pública "Consistencia interna" · `validacion_externa.matriz_redundancia_itvc` · `_EscalaIdentidad` (nuevo)'
origen: 'Auditoría de Vida Cotidiana, puntos 3.7 y 5 (prioridad media)'
---

# ADR-0108 — La redundancia interna se mide también en el ITVC

| **Extiende** | ADR-0085 (la matriz, generalizada a ITCM/ITCG/ITCP) |

## Contexto y planteo del problema

La auditoría pidió dos validaciones empíricas concretas:

> "Patentamiento de motos — aporta apenas 0,8% del ITVC y puede reflejar tanto
> confianza del consumidor como disponibilidad de crédito prendario […] Se
> sugiere una validación empírica simple: correlacionarlo con ICC para confirmar
> si aporta señal incremental o es en gran medida redundante."

Y lo mismo para `consumo_carne`. La medición que responde eso ya existía desde
ADR-0085 para los otros tres índices; faltaba el ITVC.

## Opciones consideradas

- **Usar la identidad como escala** (`_EscalaIdentidad`) — elegida: el ITVC no tiene bandas, sus componentes ya son índices base 100 = 4T-2023 y el número que se promedia es el índice mismo.
- **Aplicarle una escala de puntaje como a los otros tres** — descartada: esa escala no existe en este índice.

## Decisión

### Cómo entra un índice sin bandas

Los otros tres convierten un valor crudo en puntaje 0-100 y correlacionan ese
puntaje, porque es el número que se promedia. El ITVC no tiene bandas: sus
componentes **ya son índices base 100 = 4T-2023**, y el número que se promedia
es el índice mismo. La conversión correcta es entonces la **identidad**, no una
escala ausente.

`_EscalaIdentidad` mantiene el contrato de `parametrica.Escala` (`puntuable` y
`puntaje`) para no ramificar `matriz_redundancia`, que es genérica desde
ADR-0085.

La construcción de los índices se extrajo a `_indices_itvc_por_componente`, que
ahora comparten la reconstrucción de la serie y la matriz — mismo motivo que
`_valores_itcm_por_mes`: si cada una armara los suyos, con el tiempo la matriz
mediría una composición distinta de la publicada y nadie lo notaría.

### Lo que respondió

**La hipótesis de la auditoría no se confirma.**

| par | niveles | cambios mes a mes |
|---|---|---|
| `patentamiento_motos` ↔ `icc_utdt` | **+0,442** | +0,295 |
| `consumo_carne` ↔ `icc_utdt` | **+0,044** | −0,008 |

Ninguno se acerca al umbral de 0,7. Motos aporta señal propia frente al ICC, y
carne es directamente independiente de él.

**Pero motos sí acopla, con otro bloque.** Correlaciona −0,974 con
`mora_familias`, +0,773 con `endeudamiento_familiar` y +0,770 con
`brecha_salario_cbt`: no con confianza, sino con **poder adquisitivo**. Eso no
respalda la sospecha de redundancia con el ICC, pero sí respalda —desde el
dato— el punto 3.4 de la misma auditoría, que propone reubicar motos y carne
fuera de "Confianza y seguridad" porque miden consumo y poder de compra. La
decisión de taxonomía sigue siendo editorial; ahora tiene evidencia.

### La lectura que importa es la de diferencias

En niveles el ITVC muestra **12 pares sobre el umbral de 91**; en cambios mes a
mes, **ninguno**, con el |r| medio cayendo de 0,369 a 0,194. Es la lección de
ADR-0085 en su forma más nítida: lo que parecía redundancia era una época en
común. Los casos más extremos:

| par | niveles | diferencias |
|---|---|---|
| motos ↔ mora | −0,974 | **−0,339** |
| motos ↔ brecha salario | +0,770 | **+0,015** |
| carne ↔ tarifas | +0,728 | +0,197 |

**El único acoplamiento que sobrevive al destendenciado es
`brecha_salario_cbt` ↔ `endeudamiento_familiar`: +0,512.** Son componentes de
dimensiones distintas —Sostenibilidad de ingresos (22,75% efectivo) y
Vulnerabilidad financiera (5%)— y la auditoría no lo señaló. Es el par que
conviene seguir, no los de motos.

## Más información

### Limitaciones

Los componentes entran **winsorizados** al techo de ADR-0033, igual que en el
índice publicado. Un componente clavado en el techo pierde varianza, y sin
varianza la correlación queda subestimada. Hoy `endeudamiento_familiar` está en
el techo **19 de 31 meses**, de modo que sus correlaciones —incluida la única
que sobrevive— son un piso, no una medición limpia.

Esto conecta con el hallazgo 3.1 de la auditoría, todavía abierto: la saturación
de escala no sólo aplana la lectura pública, también degrada las mediciones de
robustez que se hacen sobre ella.
