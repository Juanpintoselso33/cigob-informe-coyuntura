---
madr: 4
id: '0327'
estado: 'aceptado'
fecha: 2026-09-16
cinturon: 'vida'
indicadores: [inseguridad, tasa_homicidios, tasa_robos]
archivos: ['scripts/vida_cotidiana/collectors/snic.py', 'scripts/descargar_series.py', 'scripts/itvc.py', 'scripts/validacion_externa.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'config.py', 'data/vida/snic_serie.json', 'tests/test_itvc_anclas_snic.py', 'web/src/lib/fichas.ts', 'web/src/lib/formulas.ts']
supersede: ['0324', '0325']
relacionado: ['0028', '0032', '0108', '0115']
ambito: 'ITCIS · dimensión de seguridad · homicidios y robos del SNIC pasan de contraste a indicador propio'
origen: 'Juan, 16-sep-2026: revierte ADR-0324/0325 — "los dos tienen que ser indicadores que puntúen, con su card y su peso"'
---

# ADR-0327 — Homicidios y robos del SNIC entran a puntuar en la dimensión de seguridad

## Contexto y planteo del problema

ADR-0324/0325 (15-sep-2026) restituyeron el desglose de delitos del SNIC por
NOMBRE en `tipos_principales`, pero lo dejaron como contraste dentro de la
ficha de `inseguridad`: homicidios y robos se bajan del CSV oficial y no
puntúan. El argumento explícito de esa decisión fue que "el SNIC es anual, no
puede puntuar en un tablero mensual".

Ese argumento es falso, y está medido contra el propio snapshot vigente al
16-sep-2026:

| indicador | cinturón | rezago del dato |
|---|---|---|
| `velocidad_resolucion` | política | 244 días |
| `iaf_transferencias` | política | 244 días |
| `protocolo_antipiquetes` | gestión | 244 días |
| `informalidad` | impacto social | 243 días |
| `subocupacion_demandante` | impacto social | 243 días |

Cinco indicadores puntúan hoy con 243-244 días de rezago del dato. El rezago
se **declara y se gestiona** con `MAX_DIAS` en `config.py` (ADR pendiente de
cita: ver el bloque "G2" de ese archivo), no descalifica a una fuente de
integrar un índice.

Además, el CSV oficial (`snic-pais.csv`) trae una columna `tasa_hechos` —la
tasa cada 100.000 habitantes YA CALCULADA por la fuente— con series completas
de **26 años (2000-2025)** para Homicidios dolosos y para Robos (excluye los
agravados por el resultado de lesiones y/o muertes). No hace falta reconstruir
una tasa con población propia: sería duplicar un cálculo que la fuente ya
publica y que es el que se cita en cualquier lectura pública de seguridad.

## Factores de decisión

- El rezago anual no descalifica (tabla de arriba): se gestiona con
  `MAX_DIAS`, igual que las otras cinco fuentes anuales/trimestrales del
  snapshot.
- La `tasa_hechos` del SNIC es un dato de 26 años, con pico y mínimo propios:
  no hace falta inventar un ancla externa ni una convención — el ancla sale de
  la propia serie (ADR-0327 no depende de referencias regionales/históricas
  traídas de afuera, a diferencia de lo que este mismo encargo consideró al
  principio y luego se descartó por innecesario).
- Homicidios y robos son señales de **calidad distinta** y no se pueden
  promediar entre sí sin perder información: el homicidio casi no tiene
  subregistro (hay un cuerpo); el robo depende de que la víctima denuncie.
  Entran como DOS componentes separados de la dimensión, no como un
  compuesto.
- El IVI (`inseguridad`, ADR-0032) y el SNIC son **complementarios, no
  redundantes**: el IVI es mensual y capta delito denunciado y no denunciado
  (cifra negra) pero no distingue TIPO de delito; el SNIC es anual, capta sólo
  lo denunciado, pero por tipo específico.
- Robos tiene una limitación de calidad propia, declarada y no resuelta: la
  tasa cae 22,4% de 2024 a 2025 (1.002,8 → 778,1) sin evento conocido que lo
  explique, mientras Hurtos cae en proporción similar (−17,4%) y Robos
  agravados por el resultado de lesiones/muertes SUBE 45,5% el mismo año — un
  patrón inconsistente con una baja real y pareja del delito violento, y
  compatible con reporte incompleto de alguna jurisdicción. No se pudo
  confirmar ni descartar contra ningún informe metodológico público del SNIC.

## Opciones consideradas

1. Dos indicadores nuevos (`tasa_homicidios`, `tasa_robos`), cada uno con su
   card, ficha y peso propio dentro de la dimensión de seguridad.
2. Un único indicador compuesto (promedio de las dos tasas).
3. Sólo homicidios como indicador nuevo, robos se queda de contraste.
4. Mantener la decisión de ADR-0324/0325 (ninguno puntúa).

## Decisión

**Opción 1.** Entran `tasa_homicidios` y `tasa_robos`, cada uno con su card,
ficha (ADR-0220) y peso propio, sin promediarse entre sí. La dimensión de
seguridad pasa de un componente a tres:

```
alta_proporcional(alta_proporcional({"inseguridad": 1.0}, "tasa_homicidios", 0.30),
                  "tasa_robos", 0.15)
→ inseguridad 0,595 · tasa_homicidios 0,255 · tasa_robos 0,150
```

El IVI conserva la mayoría (59,5%) por ser mensual y más fresco. Homicidios
pesa más que robos (25,5% contra 15%) porque es la medida sin subregistro del
desglose, y porque robos tiene la limitación de calidad de 2025 declarada
arriba. El peso NOMINAL de la dimensión (4,5%) no se toca — sigue siendo una
alta, no una recalibración.

Se descartó la Opción 2 porque promediar homicidios (sin subregistro) con
robos (con subregistro y una limitación de calidad propia) diluye la señal
limpia del primero con el ruido del segundo — el mismo problema que evitó
separar `consumo_carne_vacuna` de `consumo_carnes_otras` en ADR-0322. Se
descartó la Opción 3 porque los datos ya estaban: robos tiene la misma serie
de 26 años con `tasa_hechos` que homicidios, así que dejarlo afuera hubiera
sido arbitrario y no una limitación de la fuente. Se descarta la Opción 4
—mantener ADR-0324/0325— porque su argumento de fondo (el SNIC no puede
puntuar por ser anual) es falso y está medido en la tabla de arriba.

### Ancla

**CORRECCIÓN (16-sep-2026, revisión adversarial post-merge, mismo día).** La
versión original de este ADR rebaseaba contra el propio 2023 (mismo mecanismo
que ya usa `inseguridad`: una serie anual del SNIC resuelve sola al año 2023
porque la ventana BASE_MESES=oct/nov/dic-2023 sólo tiene un punto poblado,
diciembre) y afirmaba que "2023 cae cerca de la mediana de los 26 años de
homicidios (4,32 contra mediana ~5,7)". **Esa afirmación es falsa**: medido,
4,32 está en el **percentil 11** de la serie 2000-2025 (25% por debajo de la
mediana), no cerca de ella. El espejo también fallaba: 985,1 (el 2023 de
robos) cae en el **percentil 69**, sesgando el semáforo hacia el verde antes
de mirar un solo dato adicional.

Consecuencia medida sobre los 26 años con el ancla original: **19 de 26 años
de homicidios caían en rojo, 2 naranja, 2 amarillo y sólo 3 verde** (13 de los
26 saturados en el extremo 0 ó 10 de la escala de tensión) — un semáforo que
pinta rojo tres de cada cuatro años no discrimina nada. En robos, el sesgo
era el opuesto: **15 de 26 años daban verde**.

**Se corrige anclando contra la MEDIANA de los 26 años** (5,76 para
homicidios, 925,1 para robos) en vez de un año puntual — sea cual sea ese
año. Es el mismo principio que ya usa `idc` (anclas en desvíos respecto de la
propia distribución, ADR-0028) y evita depender de qué año particular
resultó "representativo" a ojo. Con la mediana como ancla, el reparto de los
26 años queda:

| color | homicidios | robos |
|---|---|---|
| rojo | 6 | 1 |
| naranja | 3 | 7 |
| amarillo | 5 | 10 |
| verde | 12 | 8 |

Homicidios sigue con mayoría verde porque la serie tiene una tendencia
sostenida a la baja desde 2017 —un hecho real de la serie, no un artefacto
del ancla—, pero ya no hay 13 años saturados en un extremo: el semáforo
vuelve a discriminar entre años. `tests/test_itvc_anclas_snic.py` fija este
reparto para que una futura recalibración no lo desande en silencio.

### Verificación de la premisa (antes de escribir código)

Medido contra el snapshot del 16-sep-2026 (ver tabla de rezagos arriba) y
contra `snic-pais.csv` descargado en vivo el mismo día: 26 filas por tipo,
2000-2025, columna `tasa_hechos` presente y consistente con lo citado.

## Pros y contras de las opciones

**1. Dos indicadores separados.** A favor: no diluye la señal de homicidios
con el ruido de robos; usa el dato que la fuente ya publica. En contra: la
dimensión de seguridad pasa a depender de tres series en vez de una, más
superficie de fuente caída (mitigado por el store persistente).

**2. Compuesto.** A favor: un solo indicador nuevo. En contra: mezcla señales
de calidad distinta.

**3. Sólo homicidios.** A favor: menor alcance. En contra: descarta un dato
ya disponible sin ninguna limitación de la fuente que lo justifique.

**4. Statu quo.** A favor: ninguno — el argumento que lo sostenía es falso.

### Redundancia: señal real y artefacto del forward-fill, declarados por separado

Medido tras esta corrección (`validacion_externa.matriz_redundancia_itvc()`):
`pares_altos` (|r| ≥ 0,7) del ITVC pasa de 50 a 66, y los 16 nuevos son todos
pares que incluyen `tasa_homicidios`, `tasa_robos` o `ratio_motos_autos` —
ninguno marcado `por_diseno`. Incluye `tasa_homicidios`↔`tasa_robos` con
r = 0,711 EN LA MISMA DIMENSIÓN.

Dos cosas están mezcladas ahí, y hay que separarlas:

- **Artefacto real y medible**: `validacion_externa._rebase` hace forward-fill
  de una serie ANUAL sobre la ventana mensual de 33 meses, así que dentro de
  esa ventana la serie de `tasa_homicidios`/`tasa_robos` es una escalera de
  2-3 escalones. Correlacionar una escalera con cualquier serie que tenga
  tendencia propia da |r| alto casi por construcción —de ahí el 0,928 con
  `carga_servicio_deuda_hogares` y el 0,925 con `motorizacion_total`, dos
  series sin relación conceptual con la tasa de homicidios—. Esto NO es
  redundancia de contenido: es un artefacto de cómo se reconstruye una serie
  anual dentro de una matriz mensual.
- **Señal real, no artefacto**: `tasa_homicidios`↔`tasa_robos` (r = 0,711) SÍ
  comparten el forward-fill (las dos son anuales, mismas escaleras), pero
  también comparten una fuente y un ciclo genuinos —ambas son delito
  registrado por el mismo sistema (SNIC), en el mismo país y el mismo
  período—, así que parte de ese 0,711 es correlación real de ciclo
  delictivo, no sólo el artefacto de la reconstrucción.

**No se marcan `por_diseno` en esta corrección** porque hacerlo sin poder
separar cuánto es artefacto y cuánto es señal sería declarar "esperado" algo
que en parte es un defecto de medición real. La opción más honesta y más
barata: **excluir las series puramente anuales (un punto por año) del cálculo
de redundancia mensual**, ya que la correlación que producen contra CUALQUIER
serie con tendencia no es informativa sobre redundancia de contenido. Queda
para un ADR de `validacion_externa.py` dedicado —cambiaría el cálculo para
los tres índices que usan la función genérica (ITCM/ITCG/ITCP), no sólo el
ITVC, y merece su propia medición del efecto en cada uno. No se implementa
acá por alcance: esta corrección es de calibración de tres indicadores, no
un rediseño del motor de redundancia.

### Efecto en la serie histórica reconstruida

`validacion_externa.py` reconstruye la serie ITVC de 33 meses con el ANCLA
VIGENTE en el código de hoy, no con la de cada mes en su momento —así que
corregir un ancla mueve los 33 meses reconstruidos, no sólo el último—. La
revisión adversarial que motivó esta corrección midió, sobre el ancla
original (2023), que esa reconstrucción se movía en 25 de 33 meses al sumar
los tres indicadores nuevos (delta medio 0,29, máximo 0,70 puntos de ITVC)
mientras el mes vigente casi no se movía (93,1 → 93,2) — es la firma esperada
de un cambio de ancla, no de un error. **No se remidió ese delta específico
tras cambiar el ancla a la mediana** por presupuesto de tiempo de esta
corrección: el patrón (mes vigente estable, histórico reconstruido sensible al
ancla) sigue aplicando, pero los dos números de arriba son del ANCLA ANTERIOR
y no hay que citarlos como si describieran el estado post-corrección. Queda
pendiente medirlo si se audita de nuevo.

### Confirmación (corrección post-merge)

`tests/test_itvc_anclas_snic.py`: fija el valor de la mediana usada como
ancla para los dos indicadores, fija el reparto de colores de los 26 años de
la tabla de arriba, y prueba con mutación que anclar contra 2023 (el valor
original, incorrecto) produce un reparto DISTINTO — si alguien revierte la
corrección sin querer, el test lo dice.

## Más información

- `config.py`, bloque "G2": `MAX_DIAS["tasa_homicidios"] = MAX_DIAS["tasa_robos"] = 560`,
  mismo critero que `iaf_transferencias`/`velocidad_resolucion` (anual, fecha
  del dato al 31-dic).
- [[0324-el-snic-conserva-homicidios-por-nombre-no-por-ranking]] y
  [[0325-correcciones-a-la-tanda-carne-motos-snic]] — decisiones que este ADR
  revierte parcialmente: el desglose por nombre se conserva (sigue siendo la
  fuente de `tipos_principales`), lo que cambia es que dos de esos tipos pasan
  a puntuar.
- [[0108]] — matriz de redundancia del ITVC, ADR de referencia para no repetir
  una misma señal dos veces.
- [[0028-idc-z-scores]] — precedente de anclar contra la distribución propia
  de la serie en vez de un punto elegido; la corrección de este ADR aplica el
  mismo principio con la mediana en lugar de un z-score porque acá no hace
  falta más que ordenar 26 puntos.
