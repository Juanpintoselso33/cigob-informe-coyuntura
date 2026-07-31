---
madr: 4
id: '0155'
estado: 'aceptado'
fecha: 2026-07-30
cinturon: 'vida'
cerrado_por: ['0160']
ambito: 'validación externa del ITVC + matriz de validación cruzada'
---

# ADR-0155 — El ancla de validación del ITVC pasa a ser el consumo medido

- **Descarta**: la decisión 6 de ADR-0019 en lo que refiere al ancla del ITVC
  (ITVC ↔ ICC), y con ella la variante publicada «ITVC sin ICC»
- **Relacionados**: ADR-0031 (matriz cruzada), ADR-0154 (mismo cambio en el ITCM,
  con el criterio que se aplica acá), ADR-0108 (redundancia interna),
  ADR-0045 (no mover nada para que un número quede mejor)

## Contexto y planteo del problema

El editor observó que **el ITVC casi no se mueve** y de ahí salió que había que
revisar la validación externa. Las dos cosas resultaron ciertas y separadas.

## Opciones consideradas

- **El consumo medido como ancla de validación del ITVC** — elegida.
- **El ICC como ancla** — desplazado, pero explícitamente **no descartado**: queda como contraste discriminante. Mide si la percepción sigue a las condiciones, y el hallazgo publicable es que en estos años lo hizo flojo.

## Decisión

El ancla del ITVC pasa a ser el **consumo medido**: ventas en supermercados a
precios constantes, **serie desestacionalizada del INDEC**
(`455.1_VENTAS_PREADA_0_M_44_44`, vía datos.gob.ar), rebaseada al mismo 4T-2023
que usan los componentes.

| | niveles | diferencias |
|---|---|---|
| ICC (ancla anterior, sobre el ITVC sin ICC) | +0,337 | +0,106 |
| **consumo (ancla nueva, sobre el ITVC completo)** | **+0,596** | **+0,246** |

Mejor en las dos, **sin circularidad** —así que la comparación usa el índice que
efectivamente se publica— y el +0,246 en diferencias pasa a ser el segundo más
alto del proyecto después del líder contra el ITCM.

El ICC **no se descarta**: queda como contraste **discriminante** en la
conclusión. Es lo que en realidad es —mide si la percepción sigue a las
condiciones— y el hallazgo publicable es que en estos años lo hizo flojo. Un r
más bajo ahí no es una falla, es el resultado.

En la matriz cruzada el par propio del ITVC pasa a ser el consumo.

### Consecuencias

- Desaparece del tablero la variante «ITVC sin su componente de percepción»: la
  serie graficada es el ITVC completo.
- El ancla cubre **comercio registrado de supermercados**. No ve el comercio
  informal. Declarado en la ficha.
- El canal **mayorista/discounter correlaciona negativo** (−0,16), y sumarlo al
  ancla empeora el ajuste (+0,12 el combinado). La lectura probable es que
  comprar ahí es señal de ajuste y no de holgura, así que el canal se mueve
  contra las condiciones. **Se deja como hipótesis, no como conclusión**: no se
  midió más allá de la correlación.
- Una dependencia de red nueva (datos.gob.ar, ya usada por el resto del
  pipeline), y ninguna de más: el ICC ya se descargaba porque es componente.

## Más información

### 1. Cuánto se mueve, y por qué

Sobre la reconstrucción de 32 meses, contra los otros tres índices:

| índice | rango | desvío | \|Δ mes\| medio |
|---|---|---|---|
| **ITVC** | **8,3** | **2,43** | **1,15** |
| ITCM | 44,5 | 12,38 | 3,67 |
| ITCG | 70,2 | 16,64 | 3,33 |
| ITCP | 27,9 | 7,82 | 4,13 |

**No es que los insumos estén planos.** Los componentes recorren rangos enormes:
mora 87,1 puntos, alquiler 53,5, inseguridad 50,9, sentimiento 48,4, motos 47,0,
informalidad 43,2, brecha salarial 37,8. Si se movieran juntos el índice
oscilaría **37,6 puntos**; el rango real es 8,3, así que **se cancela el 78%**.

La prueba decisiva va en contra de lo intuitivo: **sacar componentes hace que el
índice se mueva MÁS.**

| | rango del ITVC | desvío |
|---|---|---|
| completo (16 componentes) | 8,3 | 2,43 |
| sin `mora_familias` | **14,4** | 4,10 |
| sin `informalidad` | 11,8 | 3,08 |
| sin `alquiler_real` | 10,5 | 2,76 |
| sin `pobreza_nowcast` | 9,8 | 2,87 |

Son contrapesos: la mora sola casi duplica el rango cuando se va. Es la matriz de
redundancia (ADR-0108, 17 pares altos en niveles con signos mezclados) vista del
otro lado — componentes fuertemente correlacionados en sentidos opuestos promedian
a casi constante.

Hay una segunda causa, estructural: el ITVC es el único de los cuatro que
**promedia índices base-100 directamente**. Los otros tres pasan cada componente
por bandas interpoladas a 0-100, y las bandas amplifican. La consecuencia visible:
la tensión publicada del cinturón recorrió **1,7 puntos de 10** en 32 meses,
contra 4,4 del ITCM.

**Esto queda como está.** Es una propiedad del diseño base-100 (ADR-0018/0024) y
tocar la pendiente de la tensión para que el número se vea mejor es exactamente
lo que prohíbe ADR-0045. Lo que sí falta —y se anota como pendiente editorial— es
publicar la **dispersión** de los componentes al lado del neto: hoy el tablero
dice «sin cambios» donde el dato dice «no cambió en neto, pero se recompuso
fuerte por dentro».

### 2. Lo que sí estaba mal era el ancla

**Corrección de un error propio, primero.** En el análisis dije que un índice
chato «no puede correlacionar fuerte con nada». Es falso: la correlación de
Pearson es invariante a escala, y se verificó —achatar el ITVC diez veces deja el
r idéntico en 0,337. La chatura no explica el r bajo.

Lo que lo explica es **qué se canceló**. Medido componente por componente contra
el ICC:

| componente | peso | r vs ICC |
|---|---|---|
| `brecha_salario_cbt` | 0,171 | **+0,519** |
| `mortalidad_pymes` | 0,040 | +0,461 |
| `ipc_alimentos` | 0,088 | +0,446 |
| `despacho_cemento` | 0,036 | +0,327 |
| `alquiler_real` | 0,050 | **−0,425** |
| `pobreza_nowcast` | 0,093 | −0,262 |
| `mora_familias` | 0,100 | −0,220 |
| `informalidad` | 0,092 | −0,214 |

Los que suben con la confianza son de poder de compra y actividad; los que bajan
son los de carencia, con **0,335 de peso combinado**. En estos años la confianza
subió mientras esas cuatro empeoraban. El agregado no podía dar mucho más que
0,34, y eso **no es un defecto del índice: es la anti-fase entre percepción y
condiciones materiales**, que el proyecto ya tenía documentada y estaba usando
igual como prueba de validez.

Sumado a eso, el ICC tenía un problema de diseño: **es un componente del ITVC**
(6,75%), y por eso había que publicar un «ITVC sin ICC» —un número que no es el
que se publica en el tablero— sólo para que la comparación no fuera circular.

### Trampa de método, para no repetirla

La primera medición dio el ancla con **signo negativo** (−0,514) y estuve a punto
de reportar como hallazgo grave que «el ITVC subió mientras el consumo se
derrumbaba en 2024». **Era un artefacto del tratamiento**: había desestacionalizado
la serie original con una media móvil de 12 meses, que la atrasa medio año y
fabrica la divergencia. Con la serie desestacionalizada que publica el organismo
ese mismo tramo da **+0,859**.

La regla que queda: **si hay que suavizar una serie para compararla, usar la
desestacionalizada de la fuente antes que una media móvil propia** — y si no
existe, medir el rezago que introduce el suavizado antes de interpretar el signo.
