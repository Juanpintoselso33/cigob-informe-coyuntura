---
madr: 4
id: '0083'
estado: 'aceptado'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [presion_dolarizacion]
relacionado: ['0057', '0192']
ambito: 'Cinturón macro · ITCM · `presion_dolarizacion` · régimen abierto'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), observación 11 — y el stress test que **ADR-0057 dejó pedido**'
---

# ADR-0083 — La presión de dolarización pasa a ser el máximo de sus dos canales

| **Reemplaza** | La combinación 70/30 de **ADR-0057** |

## Contexto y planteo del problema

La auditoría pidió medir la sensibilidad del ponderador 70/30 con el que se
combinan los dos canales de la presión de dolarización en el régimen abierto:

- **formal** — compras netas de dólares de personas humanas vía MULC, relativas
  al M2 privado. Flujo efectivamente transaccionado.
- **informal** — brecha del dólar cripto contra el A3500. Proxy de precio.

**ADR-0057 había anticipado exactamente esta revisión.** Declaró que el 70/30
era *"juicio de calibración, no umbrales naturales"*, que debía *"someterse al
mismo stress test que el resto de las anclas"*, y dejó **pre-registrada** la
alternativa: el máximo de ambos canales, *"documentado como alternativa
razonable si la calibración 70/30 no valida bien en el próximo stress test"*.

Este ADR es ese test. El 70/30 no validó.

## Opciones consideradas

- **Máximo de los dos canales** — elegida: es lo que se quiere medir.
- **Promedio de los dos canales** — descartada: sólo describe bien los meses en que los dos canales coinciden.

## Decisión

```python
presion = max(presion_formal, presion_informal)
```

El indicador pasa a leer **"hay presión en algún lado"**, que es lo que quiere
medir, en vez de un promedio que sólo describe bien los meses en que los dos
canales coinciden.

Las constantes `PESO_PRESION_FORMAL` / `PESO_PRESION_INFORMAL` desaparecen.

### Consecuencias

- **ITCM 62,2 → 62,1.** Robustez 60,4-64,0 → 60,3-63,9.
- Sobre los 14 meses, el ITCM baja **0,28 puntos en promedio** y **0,63 en el
  peor mes** (sep-2025, el tramo de estrés preelectoral que el promedio
  suavizaba).
- Los **16 meses de régimen restringido no cambian**: ahí no hay canal informal
  y la presión ya era 100% formal.
- La correlación del ITCM reconstruido con el riesgo país mejora levemente,
  −0,767 → **−0,768**.
- Si falta el dólar cripto para algún mes de la ventana, el comportamiento
  sigue igual que antes: la presión se degrada a 100% formal.

## Más información

### Limitaciones

- **n = 14, un solo régimen.** No hay meses de régimen restringido con ambos
  canales, así que la regla se valida sólo en el mercado abierto. El régimen
  restringido no la usa, pero tampoco la pone a prueba.
- **El máximo es sistemáticamente más conservador**: por construcción nunca lee
  menos presión que cualquiera de los dos canales. Eso es una elección
  editorial —preferir el falso positivo al falso negativo en un indicador de
  tensión— y no sólo un resultado estadístico.
- El canal informal sigue siendo un **proxy de precio**, no de flujo: no capta
  efectivo fuera del sistema ni atesoramiento físico. La limitación de ADR-0057
  sigue vigente.
- La regla hereda del promedio anterior una propiedad incómoda: un canal con
  dato erróneamente alto arrastra el indicador entero, sin que el otro lo
  compense. Es el costo de no diluir.

### Lo que muestran los datos

Sobre los **14 meses** con ambos canales disponibles (abr-2025 a may-2026,
todos del **mismo régimen** — el abierto):

### Los canales son sustitutos, no complementos

Correlación entre ellos: **−0,605**. Se mueven en direcciones opuestas, y no por
un cambio de régimen: los catorce meses son del mismo.

El mecanismo se ve directo en la serie:

| mes | formal | informal | 70/30 leía | el máximo lee |
|---|---|---|---|---|
| jul-2025 | **76,2** | 0,0 | 53,3 | **76,2** |
| ago-2025 | **77,1** | 0,0 | 54,0 | **77,1** |
| sep-2025 | **90,8** | 9,4 | 66,4 | **90,8** |

Los ceros son **dato real, no faltante**: en jul y ago-2025 el dólar cripto
cotizó **por debajo** del oficial (brecha −1,69% y −0,76%). Con el mercado
abierto la demanda se va por el canal formal y la brecha cripto se desploma —
¿para qué pagar sobreprecio si se puede comprar oficial?

**Promediar sustitutos apaga la señal del canal activo.** En sep-2025 el canal
formal marcaba 90,8 de presión y el promedio ponderado publicaba 66,4.

### La validación externa lo confirma

Correlación con el riesgo país (positiva esperada: más presión, más riesgo):

| combinación | r |
|---|---|
| sólo informal | −0,420 |
| **70/30 (vigente)** | **+0,650** |
| 85/15 | +0,715 |
| sólo formal | +0,722 |
| **máximo (pre-registrada)** | **+0,824** |

El máximo valida mejor que cualquier promedio ponderado, **y mejor que usar
sólo el canal formal** — señal de que el informal aporta cuando es el que está
activo, pero diluye cuando no lo está.
