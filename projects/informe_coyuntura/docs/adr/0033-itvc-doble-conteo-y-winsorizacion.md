---
madr: 4
id: '0033'
estado: 'aceptado'
fecha: 2026-07-04
cinturon: 'vida'
indicadores: [ipc_alimentos]
relacionado: ['0067', '0219', '0222', '0224']
cerrado_por: ['0214']
ambito: 'ITVC-B100: métrica de `ipc_alimentos` + tratamiento de outliers de componentes'
---

# ADR-0033 — ITVC: doble conteo salario/comida eliminado y winsorización asimétrica

| **Disparador** | Cierre del barrido vida 13/13: el editor pidió revisar las dimensiones ("me parece raro") |

## Contexto y planteo del problema

### Problema 1 — Un tercio del índice contaba dos veces lo mismo

La correlación entre la brecha salario/CBT (22,75% del ITVC, dimensión
Ingresos) y el poder de compra de alimentos (10%, dimensión Precios) era
**r = +0,985**: la CBT es la canasta alimentaria escalada por la inversa del
coeficiente de Engel — es mayormente precios de alimentos. Ambos indicadores
eran el ratio salario/comida con distinto nombre: **32,75% del índice era el
mismo número dos veces**. El mismo defecto que el ADR-0028 cazó en el IdC
(depósitos por dos vías).

### Problema 2 — Un boom puntual compraba compensación ilimitada

Motos patentadas marcaba **166,7** (+67% vs base): en la agregación lineal,
un solo componente eufórico compensa caídas de varios. El Handbook JRC de
índices compuestos lista el tratamiento de outliers como paso estándar previo
a la agregación.

## Opciones consideradas

- **`ipc_alimentos` puntúa el encarecimiento RELATIVO de la comida** (IPC alimentos contra IPC general, sin RIPTE) — elegida: responde la pregunta de precios pura.
- **La métrica anterior, con RIPTE** — descartada: compartía numerador y denominador con la brecha, que es el doble conteo que este ADR elimina.
- **Winsorización asimétrica, techo 140 y sin piso** — elegida frente a no winsorizar.

### Consecuencias

- ITVC 91,5 → **90,5** (tensión 6,7 → 6,9): −1,0 de honestidad metodológica
  (sin el eco de la brecha en Precios y sin el excedente del boom de motos).
- Vulnerabilidad crítica intacta (31,7).
- Queda abierta la **D10** (arquitectura de dimensiones, decisión CIGOB):
  "Prospectivas de empleo" no contiene medidas directas de empleo (IPI +
  cemento + subocupación; la informalidad vive en Ingresos), "Confianza y
  seguridad" mezcla ánimo/delito/consumo, y la brecha sola pesa 22,75%.
  Cambios de taxonomía y pesos exceden el mandato del barrido.

## Decisión

### Decisión

`ipc_alimentos` puntúa desde ahora el **encarecimiento RELATIVO de la
comida**: IPC alimentos contra IPC general (nivel, rebase 4T-2023), sin
RIPTE. Responde la pregunta de *precios* pura — ¿la comida sube más que el
resto? — que castiga la canasta de los hogares pobres aunque la inflación
general baje. Independencia verificada: la métrica nueva ya no comparte
numerador ni denominador con la brecha (el poder de compra del salario lo
mide ella sola, en Ingresos). Tarifas ya era independiente (r = −0,02).

Valor al cierre: **106,9** — la comida subió *menos* que el IPC general desde
el 4T-2023 (alivio relativo). Con la métrica vieja marcaba 106,3 de puro eco
de la brecha; ahora el parecido numérico es casualidad con significado propio.

### Decisión: winsorización ASIMÉTRICA — techo 140, sin piso

- **Techo 140** (base +40): el excedente de un boom no suma. Motos 166,7 → 140,
  con nota declarada en el modal (crudo visible).
- **Sin piso, deliberadamente**: la primera versión (piso 60) recortó el
  endeudamiento crítico de 31,7 → 60 y el ITVC saltó de 91,5 a 93,3 —
  exactamente el maquillaje que este informe no hace. Las crisis no se
  recortan: se señalizan (flag de dimensión crítica, ADR-0020) y arrastran
  el promedio como deben.

## Más información

### Dimensiones >100: correcto, no bug

Ingresos 105,9 y Confianza 102,1 quedan sobre 100 legítimamente: el B100 mide
mejora/deterioro vs el arranque del mandato, y esas dimensiones están mejor
que el 4T-2023. Lo anómalo era el 166,7 — resuelto con el techo.
