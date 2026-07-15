# ADR-0067 — la mora de las familias sale del compuesto de endeudamiento y puntúa como indicador propio del ITVC

| | |
|---|---|
| **Estado** | Aceptado |
| **Ámbito** | Cinturón vida cotidiana · ITVC · dimensión Vulnerabilidad financiera · `endeudamiento_familiar` · `mora_familias` (nuevo) |
| **Fecha** | 2026-07-15 |
| **Precedentes directos** | ADR-0018 (I_EC original: deuda real × mora) · ADR-0033 (disciplina anti-doble-conteo del ITVC) |

## Contexto

Pedido editorial del usuario: "hay que poner la mora como un indicador solo
en la vida cotidiana". Hasta ahora la mora vivía **adentro** del componente
de endeudamiento (I_EC del doc 260702, ADR-0018):

```text
I_EC(t) = 100 × (Deuda_real_t / Deuda_real_4T23) × (Mora_4T23 / Mora_t)
```

El compuesto multiplicativo tenía una virtud (resolver la ambigüedad de
polaridad de la deuda: crecer con mora estable = acceso, crecer con mora
disparada = necesidad) y dos costos: (a) la mora — la señal social más dura
del cinturón — quedaba invisible como número propio; (b) el producto
penaliza con la **interacción** de ambos deterioros, no con su promedio, así
que un solo componente concentraba un castigo compuesto difícil de leer
(31,7 puntos, la dimensión entera en crítico, sin poder distinguir cuánto
era deuda y cuánto mora).

## Decisión

1. **`mora_familias` nuevo indicador**: % de la cartera de consumo de las
   familias (préstamos personales + tarjetas) en situación irregular,
   ponderado por el saldo de cada línea — la misma serie del anexo del
   Informe sobre Bancos que ya extraía `_anexo_bancos_familias()` (sin
   fuente nueva). Serie desde 2021-07 (contexto pre-mandato). En el ITVC
   puntúa por nivel B100 contra el 4T-2023, **invertido** (más mora = peor).
   La card se sintetiza desde la serie en `publicar.py` (sin colector
   propio; titular = último punto, invariante serie-titular por
   construcción — mismo patrón que la card de inseguridad/IVI).
2. **`endeudamiento_familiar` queda puro**: stock real de crédito de consumo
   (deflactado por IPC) contra el 4T-2023, sin el factor mora — mantenerlo
   la contaría dos veces (la disciplina de ADR-0033).
3. **Vulnerabilidad financiera reparte 50/50** entre ambos (antes
   endeudamiento 1,0). Provisorio, sujeto a revisión editorial CIGOB (mismo
   compromiso que ADR-0052/0064): la deuda mide acceso al financiamiento,
   la mora mide si esa deuda se paga.

## Efecto en la agregación (declarado)

El paso de producto a promedio ponderado **sube la dimensión** cuando ambos
componentes están deprimidos: el producto 100×R×M castiga la interacción;
el promedio (R+M)/2 no. La dimensión Vulnerabilidad deja de valer ~31,7 (el
compuesto) y pasa a valer el promedio de deuda-real-pura y mora-invertida.
No es maquillaje: es el mismo criterio lineal del resto del ITVC (todas las
demás dimensiones promedian componentes), y el deterioro de la mora queda
ahora VISIBLE como card propia en vez de enterrado en un factor. El flag de
dimensión crítica (ADR-0020) sigue evaluándose sobre el resultado.

## Opciones consideradas

### Mora como card visible sin puntuar (contexto)

Rechazada: viola la regla pareja de ADR-0051 ("ningún cinturón publica
cards de contexto" — lo visible puntúa).

### Mantener el compuesto Y agregar la mora como indicador

Rechazada: la mora contaría dos veces (dentro del I_EC y como indicador) —
exactamente el defecto que ADR-0033 eliminó entre brecha y alimentos.

### Repartir 65/35 u otro peso asimétrico

Descartado por ahora: sin un criterio externo que justifique la asimetría,
50/50 es el reparto menos arbitrario. Queda para la revisión editorial.

## Consecuencias

- El ITVC pasa de 13 a **14 indicadores puntuables**; Vulnerabilidad tiene
  ahora dos componentes con renormalización ante faltantes.
- El ITVC sube por el cambio de agregación (producto → promedio) — efecto
  metodológico documentado acá, no mejora de coyuntura.
- La ficha del endeudamiento pierde la "polaridad empírica" (ya no la
  necesita: cada señal tiene la suya) y la mora gana ficha propia.
- Pendiente declarado: mostrar el cambio al editor CIGOB en la próxima
  revisión editorial del cinturón, junto con el peso 50/50.
