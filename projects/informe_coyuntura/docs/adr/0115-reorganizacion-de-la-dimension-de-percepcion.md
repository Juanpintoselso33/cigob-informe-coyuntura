---
madr: 4
id: '0115'
estado: 'aceptado'
fecha: 2026-07-20
cinturon: 'vida'
indicadores: [ingresos, percepcion, seguridad]
continua: ['0110']
ambito: 'ITVC · dimensiones `ingresos` · `percepcion` (nueva) · `seguridad` (nueva)'
origen: 'Auditoría de Vida Cotidiana, punto 3.4, opción (b)'
---

# ADR-0115 — La dimensión de percepción se parte en tres

| **Continúa** | ADR-0110, que había tomado la opción (a) |

## Contexto y planteo del problema

La auditoría dio dos caminos para una dimensión que mezclaba percepción,
seguridad y consumo bajo una sola etiqueta. ADR-0110 tomó el primero —renombrar,
sin tocar la estructura— y dejó anotado que **la evidencia respaldaba mejor al
segundo**: la matriz de redundancia (ADR-0108) mostró que `patentamiento_motos`
correlaciona −0,974 con la mora, +0,773 con el endeudamiento y +0,770 con el
salario, contra apenas +0,442 con el ICC. Acopla con poder de compra, no con
ánimo.

Decisión editorial del usuario: hacer la reorganización.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

### Consecuencias

- Los textos públicos que enumeraban las cinco dimensiones se actualizaron,
  incluido el de la validación externa, que hablaba del "componente de
  confianza" pesando 7,5% cuando el ICC pesa 6,8%.
- `DIM_DESCRIPCIONES` gana las dos claves nuevas y `ingresos` se reescribe para
  mencionar los termómetros de consumo que ahora contiene.
- El test de renormalización cambió de sujeto: al faltar carne y motos, la
  dimensión que reparte ya no es percepción sino ingresos — y vuelve a 90,5,
  que es el valor que tenía antes de recibirlos. Es la comprobación de que la
  renormalización no inventa peso.

## Más información

### La estructura nueva

| dimensión | peso | componentes |
|---|---|---|
| **Ingresos y consumo** | **37,25%** | brecha salario/canasta 61,07 · informalidad 32,89 · **carne 4,03** · **motos 2,01** |
| Presión de precios | 25% | tarifas 45 · alimentos 35 · alquiler 20 |
| Prospectivas de empleo | 15% | IPI 36 · ISAC 32 · subocupación 12 · líder 20 |
| Vulnerabilidad financiera | 10% | endeudamiento 50 · mora 50 |
| **Confianza y percepción** | **8,25%** | ICC 81,82 · sentimiento digital 18,18 |
| **Seguridad** | **4,5%** | victimización 100 |

De cinco dimensiones a seis. `ingresos` recibe los dos proxies de consumo y se
renombra para decirlo.

### El criterio: peso efectivo idéntico

Los pesos nominales no se eligieron: **se derivaron de conservar exactamente el
peso efectivo de cada indicador**. Cada dimensión nueva pesa lo que sumaban sus
componentes antes.

| indicador | peso efectivo antes | después |
|---|---|---|
| `icc_utdt` | 0,0675 | **0,0675** |
| `inseguridad` | 0,0450 | **0,0450** |
| `sentimiento_digital` | 0,0150 | **0,0150** |
| `consumo_carne` | 0,0150 | **0,0150** |
| `patentamiento_motos` | 0,0075 | **0,0075** |
| `brecha_salario_cbt` | 0,2275 | **0,2275** |
| `informalidad` | 0,1225 | **0,1225** |

Eso hace que la reorganización sea **estructural y no editorial**: cambia dónde
vive cada indicador y qué dice el tablero, no cuánto pesa. Aprovechar el cambio
de arquitectura para mover pesos habría sido mezclar dos decisiones distintas en
un mismo commit, y ADR-0045 prohíbe exactamente eso.

### El ITVC publicado se mueve 0,1 y no debería asustar

| | |
|---|---|
| ponderado exacto, estructura vieja | **94,7254** |
| ponderado exacto, estructura nueva | **94,7245** |
| publicado antes | 94,7 |
| publicado ahora | **94,8** |

La diferencia real es de **0,0009 puntos**: el residuo de redondear los pesos
internos a cuatro decimales. Los 0,1 del número publicado salen de otro lado:
el motor **redondea el puntaje de cada dimensión a un decimal antes de
agregar**, y seis dimensiones acumulan ese redondeo distinto que cinco.

No se corrigió el motor. Ese redondeo es una decisión de diseño que afecta a los
cuatro índices por igual, y tocarlo movería todos los números publicados por una
razón que no tiene que ver con esta reorganización.

### Limitación conocida: una dimensión de una sola pata

**`Seguridad` queda con un único indicador**, que es exactamente el defecto que
ADR-0076 corrigió en la dimensión de actividad —*"el 11% del índice cuelga de un
solo dato"*—. Acá pesa 4,5% en vez de 11%, así que la exposición es menor, pero
el riesgo de fuente única es el mismo.

Se acepta porque el camino (b) de la auditoría lo pedía explícitamente y porque
la alternativa —dejar la victimización mezclada con el ánimo— es el problema que
este ADR viene a resolver. **Sumarle una segunda medida es trabajo pendiente**:
percepción de inseguridad o delito por tipo serían candidatos naturales.
