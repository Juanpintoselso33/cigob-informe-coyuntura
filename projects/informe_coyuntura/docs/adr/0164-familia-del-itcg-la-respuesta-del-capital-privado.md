# ADR-0164 — Familia del ITCG: la respuesta del capital privado

- **Estado**: Aceptado, **con resultado negativo publicado**
- **Fecha**: 2026-07-30
- **Ámbito**: panel y factor común del ITCG; `CAPITAL_PRIVADO_IDS` en
  `validacion_externa.py`, `FAMILIA`/`FACTOR` en `panel_validacion.py`
- **Relacionados**: ADR-0163 (el mismo trabajo para el ITVC), ADR-0161 (el
  factor común), ADR-0159 (el panel, y el caso del +0,97 espurio)

## Contexto

ADR-0163 dejó anotado el pendiente: **el ITCG era el único cinturón con una sola
estadística de su terreno** (el Merval en dólares), así que no podía tener factor
común y su promedio «convergente» era un número solo disfrazado de promedio.

## Decisión

**Concepto de la familia, fijado antes de medir**: qué hace el capital privado
con su propia plata frente al programa de transformación — cuánto vale lo que ya
está instalado en el país y cuánto capital de afuera decide entrar. No opiniones,
y no registros del propio Estado, que son los componentes del índice.

Entran tres subcuentas de la Cuenta Capital y Financiera Cambiaria del BCRA,
mensuales desde 2003: **inversión directa de no residentes**, **inversión de
cartera de no residentes** y **financiamiento externo a empresas** (préstamos
financieros, títulos de deuda y líneas de crédito).

### Lo que quedó afuera, y por qué

La regla es la de siempre: no compartir insumo con un componente de ningún
índice. Aplicada acá dejó afuera casi todo lo obvio, y conviene dejarlo escrito
para no volver a buscarlo:

| candidata | por qué no |
|---|---|
| formación de activos externos | sale del mismo balance cambiario que `presion_dolarizacion` (ITCM) |
| préstamos al sector privado | es `credito_privado` (ITCM) |
| ISAC / IPI y sus subclases | `ipi_manufacturero`, `despacho_cemento` |
| importaciones de bienes de capital | `apertura_comercial` divide por el intercambio total, que las incluye |
| **total** de la cuenta capital y financiera | equivale a la variación de reservas, y `reservas_bcra` es componente |
| EMBI / riesgo país | **decisión editorial previa**: salió del informe y no vuelve por la ventana |

### Dos decisiones de tratamiento

- **No se rebasean a 100.** Son flujos en millones de dólares que cruzan el cero;
  dividir por un promedio cercano a cero no significa nada. No hace falta: la
  correlación es invariante a la escala y el factor estandariza.
- **No se acumulan a 12 meses**, aunque el proyecto use esa transformación en
  otros lados (`saldo_comercial_12m`, `conflictividad_nacional`). Se probó y el
  resultado es la trampa que ADR-0159 ya había documentado con
  `indice_salarios_publico`: **acumulado a 12 meses el financiamiento externo da
  0,962 en niveles contra el ITCG y 0,038 mes a mes**. Un flujo acumulado queda
  casi monótono, y dos series monótonas correlacionan ~0,95 sin que eso signifique
  nada. Publicar ese 0,96 habría sido el mejor número de todo el informe y el más
  vacío.

## Resultado — negativo, y se publica

| | niveles | mes a mes |
|---|---|---|
| **factor de las 4** | 0,678 | −0,015 |
| Merval solo | **0,747** | 0,119 |
| financiamiento externo solo | 0,640 | **0,276** |
| inversión directa sola | −0,076 | 0,005 |
| inversión de cartera sola | 0,141 | −0,095 |

**El compuesto no le gana a la mejor estadística sola en ninguno de los dos
planos**, y se publica así. Es el mismo criterio con el que se publicó el caso
negativo del ITVC en ADR-0161 antes de resolverlo en ADR-0163: elegir el
subconjunto que diera mejor sería exactamente lo prohibido.

Lo que sí mejora: el ITCG pasa de **1 a 4** estadísticas de su terreno, así que
por primera vez su comparación convergente/discriminante es un promedio de
verdad y no un número solo.

**Hipótesis para el trabajo que sigue, no acción de ahora**: los flujos mensuales
de inversión directa y de cartera en Argentina están dominados por un puñado de
operaciones grandes y discretas, así que un mes cualquiera lo define una
transacción, no el estado de fondo. Eso los vuelve malos insumos para un factor
mensual. Si se confirma, la salida es buscar estadísticas de estado continuo, no
recortar el subconjunto hasta que dé bien.

## Consecuencias

- Los cuatro cinturones con paramétrica tienen ahora factor común: ITCM por su
  propio régimen de puntos de giro (ADR-0158), ITCP y ITVC validando, ITCG no.
- Queda declarado en la página del cinturón y en su ficha que el compuesto mide
  peor que el Merval solo.
