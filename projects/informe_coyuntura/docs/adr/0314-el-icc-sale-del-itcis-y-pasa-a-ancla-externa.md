---
madr: 4
id: '0314'
estado: 'aceptado'
fecha: 2026-09-15
cinturon: 'vida'
indicadores: [icc_utdt, sentimiento_digital]
archivos: ['scripts/itvc.py', 'scripts/validacion_externa.py', 'scripts/panel_validacion.py', 'scripts/publicar.py', 'scripts/procedencia_anclas.py', 'web/src/lib/descripciones.ts', 'web/src/lib/fichas.ts', 'tests/test_itvc.py', 'tests/test_redundancia_itvc.py', 'tests/test_suspension_libera_el_peso.py', 'tests/test_publicar.py', 'tests/test_motorizacion_total.py', 'tests/test_procedencia_anclas.py', 'tests/test_politica_sin_universo.py']
relacionado: ['0034', '0108', '0115', '0154', '0155', '0225', '0245', '0248']
ambito: 'ITCIS · dimensión de confianza y percepción · el ICC deja de puntuar y pasa a ancla de validación externa'
origen: 'Juan, Slack #monitor-de-proyecto-de-gobierno, 15-sep-2026: "Sacar el ICC de Impacto Social, probarlo como validación externa; para confianza usar votómetro y alguna cosa más"'
---

# ADR-0314 — El ICC sale del ITCIS y pasa a ancla de validación externa

## Contexto y planteo del problema

La dimensión "Confianza y percepción" del ITCIS pesaba 8,25% del índice con
dos componentes: `icc_utdt` (81,82% interno) y `sentimiento_digital` (18,18%
interno). ADR-0248 suspendió a `sentimiento_digital` en agosto de 2026 por
validación externa adversa (r = −0,788 contra Ipsos, signo opuesto al
esperado en 34 de 42 ventanas móviles), y su peso pasó íntegro al ICC
—que quedó como el único componente vivo de la dimensión—.

`validacion_externa.py` documentaba esto explícitamente como una limitación:
el ICC no podía usarse como ancla del ITCIS porque era, al mismo tiempo,
componente del índice. La sección "ITCIS vs ICC" existía sólo como contraste
DISCRIMINANTE, recalculando el ITCIS sin ICC para no comparar el índice
contra un ingrediente propio — un sustituto de la validación real, no la
validación real.

Es la misma situación que ADR-0154 resolvió para el Índice Líder del ITCM y
que ADR-0225 resolvió al revés para `consumo_supermercados` (que dejó de ser
ancla para integrar el índice, porque mide condiciones materiales del hogar):
**un indicador no puede ser componente y juez del mismo índice.**

## Factores de decisión

- El ICC mide percepción y ánimo, no condiciones materiales — encaja mejor
  como contraste externo que como parte de lo que el ITCIS certifica.
- Sacarlo deja la dimensión de confianza sin ningún componente activo
  (`sentimiento_digital` sigue suspendido), así que hay que decidir qué pasa
  con ese 8,25% nominal.
- El votómetro (`votometro_ventaja_lla`) ya integra el ITCP (dimensión
  "Imagen y voto", 100% interno de esa dimensión) con su propio peso en el
  score global. Sumarlo también al ITCIS pondría la misma serie a puntuar dos
  veces en dos índices con dos pesos — un caso de doble conteo real, no
  cosmético: el ITCP y el ITCIS son cinturones distintos del mismo score
  global (`generar_informe.calcular_score_global`).
- El votómetro, además, es un ratio de intención de voto en puntos porcentuales
  (pp), no una serie rebaseada a 4T-2023 como el resto de los componentes del
  ITCIS — integrarlo exigiría una transformación nueva (rebase + elección de
  signo) que hoy no existe y que nadie pidió calibrar.

## Opciones consideradas

1. **Sacar el ICC del índice; dejar la dimensión de confianza sin componente
   activo, con su peso nominal redistribuido a las otras cinco dimensiones
   por el mecanismo de renormalización que el motor ya aplica a cualquier
   dimensión sin datos.** No agrega ningún componente nuevo.
2. **Sacar el ICC y sumar el votómetro** (`votometro_ventaja_lla`) como
   reemplazo, para que la dimensión de confianza siga teniendo un componente
   propio.
3. Dejar el ICC en el índice y no habilitarlo como ancla (statu quo).

## Decisión

**Opción 1.** El ICC sale de `DIMENSIONES_ITVC` (dimensión `percepcion`) y
pasa a ser el ancla de validación externa del ITCIS en
`validacion_externa.py`, con el mismo rol que el Índice Líder cumple para el
ITCM y el ICG para el ITCG: se correlaciona el ITCIS completo contra la serie
cruda del ICC, en niveles y en diferencias, como contraste DISCRIMINANTE (si
la percepción sigue a las condiciones materiales, no que el índice "deba"
parecerse al ICC). El ICC pasa a `publicar.VIDA_OCULTOS` —deja de ser card,
igual que `indice_lider`— y se agrega a la familia del panel de
`panel_validacion.py` con el mismo patrón que el Líder (etiquetado con la
familia de su propio índice, como contraste ajeno para los otros tres).

La dimensión de confianza y percepción queda declarada en
`DIMENSIONES_ITVC` con `sentimiento_digital` como único indicador (suspendido
desde ADR-0248), así que no tiene HOY ningún componente activo: el motor la
salta entera —el mismo mecanismo que ya usa con cualquier dimensión sin datos
disponibles ese mes— y su 8,25% nominal se redistribuye proporcionalmente
entre las cinco dimensiones restantes. No hace falta código nuevo: es la
renormalización que `itvc.calcular_itvc` ya hacía.

**El votómetro NO se agrega** (opción 2 descartada, no por indefendible sino
por ser la que más compromete): duplicaría una serie entre dos cinturones con
dos pesos, y el efecto medido es mínimo comparado con ese riesgo (ver
Consecuencias). Queda documentada acá para que Juan decida con los números.

### Efecto medido (snapshot del 15-sep-2026, antes/después)

| | Con ICC (antes) | Sin ICC, redistribuido (Opción 1) |
|---|---|---|
| ITVC (ITCIS) | 93,0 | 93,1 |
| Tensión del cinturón | 6,4 | 6,4 (no se mueve al redondeo de un decimal) |
| `ingresos` (peso efectivo) | 28,06% | 30,58% |
| `precios` (peso efectivo) | 25,00% | 27,25% |
| `vulnerabilidad` (peso efectivo) | 10,00% | 10,90% |
| `empleo` (peso efectivo) | 24,19% | 26,37% |
| `seguridad` (peso efectivo) | 4,50% | 4,90% |
| `percepcion` | 8,25% (sólo ICC) | no se publica (sin componente activo) |

El score_global no se mueve por este cambio: la tensión del cinturón
(insumo de `calcular_score_global`) queda en 6,4 antes y después. El único
movimiento es interno al ITCIS, y es de +0,1 punto.

La correlación medida entre el ITCIS completo (ahora sin ICC) y el ICC, sobre
33 meses reconstruidos: **niveles r = −0,258 (n=32), diferencias r = +0,287
(n=30)**. Es débil y de signo mixto — exactamente lo esperable de un
contraste discriminante entre condiciones materiales y percepción, no una
confirmación de que deban moverse juntos.

**Ese signo no es un detalle: es la circularidad que el ancla vino a
eliminar, medida.** Dejando el ICC ADENTRO del índice (contrafactual: ITCIS
con ICC vs. ICC), la correlación en niveles da **r = +0,161**; sacándolo
—que es la Opción 1, la decidida— da **r = −0,258**. El signo se invierte:
un índice que integra su propio contraste se correlaciona artificialmente
con él por construcción, y eso es exactamente lo que la sección
"Consecuencias" venía a evitar.

### Sacar el ICC no sólo mueve el punto de hoy: revisa la serie histórica

La tabla "Efecto medido" de más arriba compara un solo punto (el snapshot del
15-sep-2026). Pero `construir_series_itvc` reconstruye el ITCIS mes a mes
desde las series de sus componentes, así que sacar un componente **recalcula
la serie completa hacia atrás**, no sólo el mes de hoy. Comparando la
reconstrucción con ICC (contrafactual) contra la reconstrucción sin ICC
(la real, ya publicada) mes a mes:

| Período | Con ICC (contrafactual) | Sin ICC (Opción 1, publicado) | Diferencia |
|---|---|---|---|
| 2024-01 a 2024-04 | 95,4 → 98,1 | 96,7 → 99,4 | **+1,3** en los cuatro meses |
| 2025-05 | 93,7 | 92,8 | **−0,9** |
| 2025-11 | 94,7 | 93,8 | **−0,9** |
| 2026-01 | 96,1 | 95,2 | **−0,9** |

El rango de revisión medido es de **−0,9 a +1,3 puntos** según el mes — más
que el +0,1 que muestra el snapshot de hoy, porque ahí las dos
reconstrucciones ya convergen. Sacar un componente de un índice cuya
dimensión de confianza pesaba 8,25% no es neutral hacia atrás.

El panel de validación del ITCIS también se mueve, no sólo el punto de
contraste con el ICC. En niveles, la asociación media del índice contra las
estadísticas de su propio terreno (convergente) pasa de **0,162 a 0,288**, y
contra las ajenas (discriminante) de **0,222 a 0,346** — ambas suben porque
`icc_utdt` se sumó al panel de 14 estadísticas (antes 13) del lado "propio".
En diferencias el movimiento es menor: convergente 0,221→0,211, discriminante
0,191→0,161 (`output/validacion_externa.json` → `panel_validacion.itvc`).

### Candidatos para "confianza y percepción" — no implementados

Juan pidió, además del votómetro, "alguna cosa más" para la dimensión de
confianza. Búsqueda sobre las 107 series ya persistidas en el repo
(`web/src/data/series.json`) y sobre lo que usan otros cinturones como ancla:
no hay ninguna serie de percepción/confianza social independiente del ICC,
del ICG UTDT (ancla propia del ITCG) o de `clima_electoral` (derivada del
mismo votómetro, y ya en la familia del panel del ITCP). Usar cualquiera de
las tres duplicaría un ancla que ya cumple ese rol en otro índice.

No se propone un candidato nuevo con rezago medido en esta sesión — inventar
uno sin medir su rezago real y su cobertura sería exactamente la clase de
decisión de contenido editorial que este ADR no puede tomar por Juan. Fuentes
posibles a evaluar en una sesión dedicada (sin medir): encuestas de humor
social de otros centros (CEOP, Management & Fit, Poliarquía) o un subíndice
propio del ICC (situación personal vs. país) que la UTDT también publica.

### Riesgo latente aceptado: `sentimiento_digital` queda con el 100% de la dimensión

Sacar el ICC no sólo redistribuye peso ENTRE dimensiones (arriba): también
cambia el reparto DENTRO de `percepcion`. Con el ICC adentro,
`sentimiento_digital` pesaba 18,18% de esa dimensión (el ICC se llevaba el
81,82% restante); sacado el ICC, `DIMENSIONES_ITVC["percepcion"]["indicadores"]`
queda `{"sentimiento_digital": 1.0}` — **100%**.

Hoy no tiene efecto (`sentimiento_digital` está suspendido desde ADR-0248 por
validación externa adversa: r = −0,788 contra Ipsos, signo opuesto al
esperado en 34 de 42 ventanas móviles), así que la dimensión entera se salta
y su peso se redistribuye a las otras cinco. **Pero si esa suspensión se
levanta sin revisar este número, `sentimiento_digital` se lleva de entrada el
8,25% completo de la dimensión de confianza en vez del 1,5% que tenía cuando
compartía con el ICC** — casi seis veces más, sin que nadie haya vuelto a
decidir ese peso. `tests/test_web_declara_los_pesos_del_itvc.py` (línea 42)
ya documentó el modo de falla simétrico cuando `sentimiento_digital` salió en
ADR-0248 y el ICC se quedó con el 100%; este ADR reintroduce la misma
situación del otro lado.

**Decisión consciente**: se acepta el riesgo por ahora — la Opción 1 (sin
reemplazo) ya está tomada y no se bloquea por esto — pero queda escrito para
que un futuro "reactivar `sentimiento_digital`" no sea sólo sacar la
suspensión: hay que fijar de nuevo su peso interno en `percepcion` antes de
reactivarlo, no heredar el 100% por default.

### Consecuencias

- El ITCIS pasa de 18 a 17 componentes.
- `publicar._scoring_indice`/`_semaforos` ya no evalúan `icc_utdt`: pasa a
  `VIDA_OCULTOS`, se sigue relevando (colector y serie intactos) y se sigue
  publicando su serie para quien quiera graficarla, igual que `indice_lider`.
- `validacion_externa.construir_series_itvc` deja de devolver la variante
  "ITVC sin ICC" (ya no tiene sentido: el ITVC ya no incluye al ICC).
- Los tests que fijaban 18 componentes, la composición de `percepcion` y la
  suma de pesos nominales a 1,0 se actualizaron: la suma de `peso` (nominal)
  de las dimensiones publicadas da 0,9175 y no 1,0 mientras `percepcion` no
  tenga un componente activo — es `peso_efectivo` el que sigue sumando 1,0.

### Confirmación

`tests/test_itvc.py` fija que `percepcion` no aparece en `dimensiones` cuando
sólo tiene un indicador suspendido declarado, y que el ejemplo del documento
recalcula sin el ICC. `tests/test_redundancia_itvc.py` confirma que `icc_utdt`
ya no aparece en la matriz de redundancia INTERNA. `tests/test_publicar.py`
confirma que `icc_utdt` no es card (`VIDA_OCULTOS`) y que el ITCIS reconcilia
con 17 componentes. `tests/test_procedencia_anclas.py` confirma que no queda
declarada una procedencia para un indicador que ya no puntúa.

## Pros y contras de las opciones

**1. Redistribuir sin reemplazo.** A favor: cero riesgo de doble conteo,
efecto medido y chico, usa el mecanismo de renormalización que ya existe. En
contra: la dimensión de confianza queda momentáneamente sin ningún
componente propio hasta que se decida un reemplazo real.

**2. Sumar el votómetro.** A favor: la dimensión conserva un componente.
En contra: duplica una serie que ya puntúa en el ITCP con otro peso, y
requiere una transformación (rebase, signo) que hoy no existe para un pp de
intención de voto.

**3. Statu quo.** A favor: cero trabajo. En contra: dejaba al ICC sin poder
usarse nunca como ancla real —la limitación que este ADR resuelve— con la
excusa metodológica ya escrita en el propio código.

## Más información

Precedentes directos: ADR-0154 (Índice Líder sale del ITCM, mismo motivo),
ADR-0225 (consumo_supermercados entra al ITCIS y deja de ser su ancla, la
misma regla en la dirección opuesta), ADR-0248 (suspensión de
`sentimiento_digital`, la que dejó a `percepcion` con un solo componente
antes de este cambio).
