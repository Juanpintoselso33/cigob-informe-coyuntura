---
madr: 4
id: '0088'
estado: 'aceptado'
fecha: 2026-07-19
cinturon: 'politica'
indicadores: [sector_privado, brecha_obra_publica]
modifica: ['0036']
corregido_por: ['0095']
ambito: 'ITCP · dimensión `sector_privado` · indicador `brecha_obra_publica` · validación externa'
origen: 'Auditoría externa del cinturón político, prioridad 1'
---

# ADR-0088 — El ITCP incorpora una dimensión de sector privado

| **Modifica** | ADR-0036 (pesos entre dimensiones del ITCP) |

## Contexto y planteo del problema

La auditoría del cinturón político evaluó los 11 indicadores contra el objetivo
declarado —medir la dificultad que **legisladores, gobernadores y empresarios**
representan para ejecutar el plan de gobierno— y encontró un hueco:

> "De los tres actores mencionados explícitamente en el pedido, el tercero no
> tiene ningún indicador propio. El cinturón mide con bastante detalle al
> Congreso, de forma indirecta a los gobernadores y **no mide en absoluto al
> sector empresarial**. Esta es la recomendación de mayor prioridad de todo el
> documento."

Es correcto y se verifica en la estructura: las cinco dimensiones cubrían
Congreso (30%), gobernadores por proxy (25%), el propio oficialismo (20%), la
calle (15%) y el electorado (10%). Los empresarios, 0%.

## Opciones consideradas

_El ADR original no registró opciones alternativas._

## Más información

### Limitaciones

- **Es un solo canal de conflicto.** Mide la relación con el sector que depende
  de la obra pública. Sería ciego a una pelea con el agro, la energía o los
  bancos. La dimensión arranca con un único indicador y eso es una limitación
  real, no un diseño terminado.
- **La pregunta indaga por el cambio esperado, no por el nivel.** Un recorte
  sostenido termina normalizándose: cuando las empresas se acostumbran al
  presupuesto nuevo dejan de esperar caídas adicionales y la brecha vuelve a
  cero aunque la obra pública siga en un piso históricamente bajo. Es
  probablemente lo que explica el +0,2 actual frente al −29,8 de 2024, y por eso
  el contraste con Construya no es opcional.
- **Releva grandes empresas**; las pequeñas y regionales están subrepresentadas.

### El indicador elegido

**Brecha de expectativas entre constructoras de obra pública y de obra privada**
(INDEC, Encuesta Cualitativa de la Construcción, Cuadro 7.1), en promedio móvil
de 12 meses.

Cada mes el INDEC pregunta a las grandes empresas constructoras si esperan que
su actividad suba, no varíe o baje en el trimestre siguiente, **y publica las
respuestas por separado para obra pública y obra privada**. El saldo de cada
grupo es `%sube − %baja`; el indicador es la diferencia entre ambos saldos.

### Por qué la brecha y no el nivel

Las dos submuestras son el mismo sector: mismos costos de insumos, mismo
crédito, mismo ciclo macro. **Lo único que las distingue es quién les paga.** La
diferencia entre ambas aísla el componente que aporta el Estado y descarta el
ciclo económico general — es un grupo de control interno, no una corrección
estadística.

Que eso no sea una racionalización se comprueba en la serie de diez años:

| año | brecha | nivel de obra pública |
|---|---|---|
| 2019 | −13,2 | **−58,2** ← el peor nivel de la serie |
| 2023 | +1,2 | −8,8 |
| **2024** | **−29,8** ← el peor de la serie | −48,6 |
| 2025 | +1,2 | −1,4 |
| 2026 | +0,2 | −5,6 |

La brecha marca **2024** como el peor momento para las empresas que dependen del
Estado. El nivel marca **2019**, que fue la recesión de Macri y no un conflicto
entre el gobierno y sus contratistas. La brecha separa las dos cosas; el nivel
las confunde. Ése es el argumento entero.

### Bandas

`(+10, ∞) → 100 · (0, +10) → 85 · (−10, 0) → 65 · (−20, −10) → 40 · (−∞, −20) → 10`

Anclas en números redondos alrededor del **cero**, que es el valor con
significado propio: brecha nula = el Estado no es una fuente diferencial de
incertidumbre para quienes trabajan para él. **No se calibró contra el rango
observado**: el criterio de ADR-0045 sólo autoriza eso cuando el extremo es
matemáticamente inalcanzable, y acá no lo es (las lecturas mensuales ya tocaron
+44,8 y −39,9).

Contra la serie real, las bandas discriminan en todo el rango: 2024 cae en 10,
2019 en 44,5, 2021 en 99,7, hoy en **75,4**.

### Pesos

La dimensión entra con **15%** y las cinco existentes ceden proporcionalmente.
Es el primer cambio de pesos *entre* dimensiones desde ADR-0036, y el orden
relativo de las cinco originales se conserva intacto.

| dimensión | antes | ahora |
|---|---|---|
| poder legislativo | 30% | 25% |
| alianzas territoriales | 25% | 22% |
| cohesión interna | 20% | 18% |
| **sector privado** | — | **15%** |
| conflicto social | 15% | 12% |
| imagen y voto | 10% | 8% |

ITCP: 68,0 → **69,8** (tensión 3,0).

> **Corrección (ADR-0095, 20-jul-2026).** Lo que sigue valida el INDICADOR, y
> es correcto. Lo que este ADR no midió es el efecto de incorporarlo AL ÍNDICE:
> el ITCP ↔ EPU cayó de −0,599 a −0,372, toda la caída atribuible a este
> componente. La causa no es un defecto de la métrica sino que el indicador
> **cambia de signo según el gobierno** —correcto para las dos administraciones
> anteriores, invertido para la actual, porque el recorte de obra pública es su
> programa y no un síntoma—. Se decidió mantenerlo puntuando y publicar el
> hallazgo. Ver ADR-0095.

### Validación externa: percepción contra conducta

El indicador es una **encuesta**: mide lo que las empresas dicen esperar. Se
contrasta contra el **Índice Construya** (volumen de ventas de insumos de la
construcción de sus fabricantes líderes, mensual desde jun-2002), que mide lo
que efectivamente se vende.

| | r | n |
|---|---|---|
| niveles (ambas a 12m) | **+0,793** | 98 |
| primeras diferencias | **+0,467** | 97 |

El segundo número es el que importa. ADR-0085 dejó la lección de que dos series
que sólo suben correlacionan alto sin compartir información; acá la correlación
**sobrevive a quitar la tendencia común**. Las expectativas declaradas siguen a
la obra que efectivamente se hace: la lectura no es humor.

Nota metodológica: la brecha ya viene suavizada a 12 meses, así que Construya se
suaviza igual antes de comparar. Correlacionar una serie suavizada contra una
cruda mide en buena parte la diferencia de suavizado — hacerlo mal daba 0,257 en
vez de 0,793, y se detectó porque el número no coincidió con el del análisis
previo.

### Consecuencias de diseño

La card y la serie **comparten una sola implementación**:
`politica.brecha_obra_publica_serie()` devuelve la serie completa y la card toma
su último punto, así que `card == serie[-1]` por construcción — que es
exactamente lo que verifica el gate G3 y lo que violaron los dos bugs del día
anterior (ADR-0086 y ADR-0087) por tener el cálculo escrito dos veces.

`validacion_externa._serie_indicador()` lee de `output/series/*.csv` y no de
`series.json`: ese archivo lo escribe publicar.py, que en el pipeline corre
*después*, de modo que un indicador recién incorporado habría dado n=0 el primer
día.

### Candidatos descartados

Se relevaron ~15 organismos. Las consultas quedan registradas para que el
negativo sea auditable:

| candidato | por qué no |
|---|---|
| INDEC ETN — ICE industria | mide clima macro, no fricción con el Estado; sólo 17 puntos de serie |
| INDEC ETN Cuadro 4 | 119 puntos, pero la pregunta es demanda interna: coyuntura, no relación con el poder |
| Índice Construya | conducta real, pero demanda agregada — se usa como validación externa, no como puntuable |
| UCI (capacidad instalada) | ídem: conducta, pero no aísla al Estado |
| BCRA ECC-Empresas | pregunta a **bancos** sobre crédito a empresas, no a empresas |
| Vistage (confianza empresaria) | trimestral desde 2006, pero **sin archivo de serie**: cada PDF trae sólo su trimestre |
| AAICI "Monitor de la Inversión" | sin rastro posterior a 2019 |
| datos.produccion.gob.ar | `q=anuncios` → 0 resultados; `q=inversion` → 2, ambos con datos que terminan en 2018 y 2022 |
| Deloitte "Monitor de Inversiones" | vivo, pero metodológicamente es scraping de noticias: mide anuncios declarados, y el propio informe admite que la inversión medida por INDEC caía mientras los anuncios subían |
| RIGI | ya está en el ITCG; mide capital comprometido, pero su aprobación depende del propio gobierno |

Dos negativos de la primera pasada resultaron **mal fundados** y se corrigieron
antes de cerrar: Vistage (se había dado por inexistente y existe) y SRA (se
había afirmado un bloqueo por `robots.txt` que no es tal). Se dejan anotados
porque el punto de esta tabla es que sea refutable.
