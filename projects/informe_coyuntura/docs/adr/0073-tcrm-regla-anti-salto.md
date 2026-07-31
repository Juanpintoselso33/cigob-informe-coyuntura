---
madr: 4
id: '0073'
estado: 'rechazado'
nota_estado: '**Rechazado** (implementado y revertido el 18-jul-2026)'
fecha: 2026-07-18
cinturon: 'macro'
indicadores: [tcrm]
ambito: 'Cinturón macro · ITCM · dimensión Competitividad externa · `tcrm`'
origen: 'Auditoría de consistencia del cinturón macro (17-jul-2026), sección III · dimensión 5'
---

# ADR-0073 — Regla anti-salto para el TCRM: **RECHAZADA**

| **Precedentes** | ADR-0056 (regla del saldo comercial, cuya forma se copió) · ADR-0021 (puntaje interpolado) |
| **Revertido por** | Revisión adversarial externa del mismo día |

> **Este ADR documenta una decisión que se tomó y se deshizo.** Se conserva
> porque la observación que lo motivó es intuitiva y va a volver a plantearse;
> acá están los números que la contestan. La evidencia también está fijada en
> `tests/test_itcm_tcrm_sin_regla_salto.py`, ejecutable, para que no dependa de
> que alguien lea este documento.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Decisión

### Lo que se implementó

Un descuento interpolado hacia un piso de 55 puntos cuando el nivel alto se
alcanzaba por un salto, medido como el máximo de las variaciones mensuales de
una ventana móvil. La ventana se fijó primero en 3 meses y se extendió a 8 sobre
evidencia de traspaso a precios en Argentina (Frank 2017-2023: 6-8 meses;
Bertholet 2026: se estabiliza cerca del octavo). El umbral de 8% m/m se
contrastó contra el criterio estándar de los sistemas de alerta temprana de
crisis cambiarias (Kaminsky-Lizondo-Reinhart media+3σ, Edison media+2,5σ) y
resultó indiferente: sobre esta serie los cuatro umbrales detectan el mismo
único mes.

### Por qué se rechaza

### 1. La premisa no se sostiene: el índice ya resolvía bien el episodio

Es el argumento decisivo. Se reconstruyó el ITCM mes a mes **sin la regla**:

| mes | ITCM | competitividad | estabilidad monetaria |
|---|---|---|---|
| **dic-2023** | **26,2** | 100,0 | **21,0** |
| ene-2024 | 26,2 | 100,0 | 20,7 |
| abr-2024 | 33,6 | 71,2 | 31,5 |
| jun-2026 | 52,4 | 47,5 | 66,9 |

**Diciembre de 2023 es el mes más tenso de toda la serie reconstruida.** El
índice nunca leyó una mejora: la competitividad efectivamente saltó a 100, pero
la estabilidad monetaria se derrumbó a 21,0 y pesa más que aquélla (26% contra
11%), de modo que la agregación devolvió el peor registro del período.

Que dos dimensiones se muevan en sentidos opuestos ante una devaluación **no es
un defecto: es para lo que sirve tener dimensiones**. Una devaluación mejora
genuinamente la competitividad externa y destruye genuinamente la estabilidad
monetaria. La observación de la auditoría describe correctamente el
comportamiento de una dimensión aislada, y saca de ahí una conclusión sobre el
índice completo que el índice completo no comete.

### 2. Doble conteo con la dimensión monetaria

El indicador es el ITCRM del BCRA: un tipo de cambio **real**, ya deflactado por
precios relativos. Cuando la inflación se come el salto, el ITCRM cae por
construcción —de 124,9 a 97,0 en cuatro meses, como muestra la tabla de arriba—
y el puntaje cae con él. El índice **sí registra** la evaporación; el reclamo
legítimo era sobre el rezago con que la registra, no sobre que no lo hiciera.

Y el mecanismo por el que el ITCRM cae es la inflación, que ya puntúa con el 26%
del índice en estabilidad monetaria. La regla hacía que la **misma** inflación
descontara además la dimensión de competitividad. Medido:

| mes | ITCM sin la regla | con la regla |
|---|---|---|
| dic-2023 | 26,2 | **20,6** |
| ene-2024 | 26,2 | **20,6** |
| abr-2024 | 33,6 | 31,5 |

La regla le restaba 5,6 puntos al mes que ya era el más tenso del registro.

### 3. Nunca interpolaba: era un piso duro disfrazado

Con `frac = (salto − 8) / (25 − 8)` acotado a [0,1], el salto de dic-2023
(+50,1%) daba `frac = 2,48 → 1,0`, y el puntaje resultante era **55,0 exacto en
los siete meses**. La franja de interpolación útil (8%-25%) está vacía en la
muestra y es rara por construcción: los saltos cambiarios argentinos o son
chicos (<8%) o son grandes (>25%). El ADR se presentaba como "interpolada, sin
acantilado, calcando ADR-0056" y en los hechos replicaba la patología que
ADR-0056 había venido a curar.

### 4. Fallaba en el caso que debía premiar

Se había celebrado como virtud que la regla "se apaga sola" al octavo mes. Eso
era una propiedad del episodio dic-2023, no del mecanismo: se apagó porque el
salto se licuó y el nivel cayó por debajo del piso. En el caso opuesto —un salto
grande seguido de estabilización exitosa, con el TCRM sosteniéndose en 120— la
regla castigaría a 55 durante ocho meses y **saltaría discontinuamente a 100 en
el mes 9**: un escalón de 45 puntos sin que ocurra nada en la economía, y
justamente en el escenario que el índice debería premiar. El máximo sobre una
ventana no distingue "salto que se licuó" de "salto que se sostuvo", que es la
única distinción que importaría.

### 5. Introducía dependencia de trayectoria en un índice de estado

El ITCM declara medir el estado de tensión de un mes. Descontar el puntaje de
hoy por lo que pasó hasta ocho meses atrás incorpora un pronóstico ("esto va a
revertir") a una medida de estado, sin que el resto del sistema siga esa
convención.

## Más información

### Lo que pedía la auditoría

Que la banda superior del TCRM fuera condicional a la velocidad de la
depreciación. El argumento: las bandas miran sólo el nivel —por encima de 110
puntúan 100— así que **"una crisis cambiaria mejoraría el puntaje de
competitividad mientras destruye el de estabilidad"**. El caso concreto es real:

| mes | ITCRM | var. m/m | puntaje de competitividad |
|---|---|---|---|
| nov-2023 | 83,2 | — | 43,0 |
| **dic-2023** | **124,9** | **+50,1%** | **100,0** |
| ene-2024 | 132,8 | +6,3% | 100,0 |
| abr-2024 | 97,0 | −8,4% | 71,2 |

### Qué queda en pie

- **El TCRM se puntúa por su nivel y nada más.** Sin regla automática.
- **La observación 5 de la auditoría pasa a "verificada, no requiere cambio"**,
  con la evidencia de la sección 1 como respuesta.
- **La alternativa de fondo sigue abierta**, y es la única línea que este
  trabajo deja viva: KLR no puntúa el *nivel* del tipo de cambio real contra
  bandas fijas sino su **desvío respecto de la propia tendencia**, uno de los
  indicadores con mejor desempeño de su sistema de alerta temprana. Eso
  atendería el problema real —el rezago con que el nivel refleja el traspaso—
  con un solo mecanismo, sin constantes ad-hoc, sin doble conteo y sin
  dependencia de trayectoria explícita. Es un rediseño del indicador, no un
  ajuste, y queda como decisión editorial pendiente.
- **La regla del saldo comercial (ADR-0056) no se toca.** Ahí el ajuste corrige
  una ambigüedad genuina del indicador —un superávit puede venir de exportar más
  o de importar menos, y el saldo no lo distingue—, que es un caso distinto del
  de un indicador que ya se corrige solo.

### Lección de proceso

La observación de la auditoría era intuitiva y sonaba correcta, y se aceptó su
premisa sin verificarla. **La verificación costaba una consulta**: reconstruir el
ITCM de dic-2023 y mirar si el índice había leído una mejora. No la había leído.
Antes de construir una regla que corrige el comportamiento de un índice,
corresponde medir primero ese comportamiento.
