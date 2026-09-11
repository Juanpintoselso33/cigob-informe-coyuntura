# 03 — Motor paramétrico y robustez

## El motor común: `parametrica.py`

Los tres índices con bandas (ITCM, ITCG, ITCP) comparten el motor de **puntaje
interpolado entre anclas** (ADR-0021): cada indicador define bandas
`(low, high, puntaje)`; el ancla de una banda finita es su punto medio, el de
una banda abierta su borde; entre anclas se interpola linealmente y en los
extremos es plano. Elimina los saltos de escalón del scoring por banda.

`interpolacion_sombra.py` publica el contraste escalón-vs-interpolado que
respaldó esa decisión.

## Los cuatro índices

### ITCM — `itcm.py` (macro)

Seis dimensiones y 15 componentes activos al 8-sep-2026. Pesos nominales:
estabilidad monetaria 26%, viabilidad fiscal-comercial 24%, financiamiento 16%,
actividad 11%, competitividad externa 11% e inversión 12%.

- Estabilidad: IPC 60%, REM 20% y composición de liquidez/presión compradora 20%.
  El REM entra como equivalente mensual de su tasa anual; la matriz de liquidez
  entra con inversión exacta de su tensión. No participan IDM ni ICIP.
- Financiamiento: reservas netas 34%, IdC 21%, costo real del Tesoro 25%, crédito
  privado real 20%. IdC usa z-scores de nivel, no el antiguo cociente mensual.
- Actividad: EMAE 60%, difusión sectorial 20%, IPI manufacturero suavizado 20%.
- Competitividad: TCRM. Inversión: IAI. Son dimensiones de un componente.

Tablas, anclas explícitas y transformaciones vigentes: `scripts/itcm.py` y
[manual macro](../manuales/macro.md). Una banda descriptiva no sustituye la
interpolación ni las anclas explícitas que define cada motor.

### ITCG — `itcg.py` (gestión)

Escala 0–100 de ejecución del programa; cinco dimensiones (35/25/15/15/10).
Mantiene 14 posiciones nominales y 13 activas: reestructuración de organismos
está suspendida. El peso interno liberado renormaliza sobre reducción de
dotación y gasto de funcionamiento; la dimensión sigue pesando 25%.
Una puntuación elevada acredita avance según esta definición, no eficacia
social, calidad del gasto ni satisfacción de los usuarios.

### ITCP — `itcp.py` (política)

Siete dimensiones: legislativo 21%, alianzas territoriales 19%, cohesión 15%,
conflicto social 10%, imagen/voto 7%, judicial 15%, sector privado 13%.
De 19 posiciones nominales, 17 están activas: apoyo empresario y judicialización
están suspendidos. Sector privado queda representado sólo por la brecha de
obra pública; no se debe presentar como una encuesta al empresariado.

### ITCIS — `itvc.py` + `publicar._itvc_indices` (impacto social)

- Seis dimensiones: ingresos/consumo 28,06%, precios 25%, empleo 24,19%,
  vulnerabilidad financiera 10%, percepción 8,25%, seguridad 4,5%.
- 19 posiciones nominales y 18 activas. Sentimiento digital está suspendido;
  la percepción queda enteramente representada por el ICC.
- La referencia principal es el promedio 4T-2023. Victimización declara una
  base alternativa; servicios públicos usa umbrales de carga sobre el salario
  (10% agua/energía y 5% transporte, ADR-0235). No es una base homogénea.
- Techo de 140 por componente y sin piso, salvo motorización, exenta. El
  snapshot declara recorte o exención. No equivalen a intervalos de confianza.
- Tensión = 5 − (ITCIS − 100) × 0,2, acotada a 0–10.

### Pesos nominales y efectivos

`peso` en cada componente conserva su peso nominal. Al faltar o suspender
componentes, el motor divide por la suma de los pesos de los presentes.
`peso_efectivo` informa la participación resultante en el índice completo.
Confundir ambos produce aparentes discrepancias en dimensiones suspendidas.
Los manuales generados describen la estructura; el snapshot permite auditar el
cálculo efectivamente publicado.

## La batería de robustez (tres pilares, ADR-0019/0020/0031)

La robustez compacta se calcula dentro de `publicar.py` para cada snapshot; el
pipeline nocturno regenera además el informe ampliado y la validación externa.

### 1. Monte Carlo — `sensibilidad.py`
Perturba pesos (±20% relativo) e insumos (±5% **del ancho entre anclas** —
scale-free, no multiplicativo) con semilla fija. Hay dos productos coordinados:

- `robustez_compacta()` ejecuta **1.000 simulaciones** durante `publicar.py` y
  embebe p05-p95, mediana y probabilidad de zona en `web/src/data/informe.json`.
- `analizar_bloque()` ejecuta **2.000 simulaciones** después de publicar y
  escribe el análisis ampliado, incluido leave-one-out, en
  `output/sensibilidad.json`.

Un test verifica que el valor puntual cae dentro del rango.

### 2. Dimensión crítica — flag ADR-0020
Una dimensión bajo el umbral crítico se marca en el snapshot y la web la
señaliza ("el promedio del índice no la compensa"). Hoy: vulnerabilidad
financiera (mora materializada 70% y carga del servicio de deuda 30%,
ADR-0231).

### 3. Validación externa — `validacion_externa.py`

El ITCM se contrasta con el Índice Líder UTDT. Los tres índices socioeconómicos
usan un panel definido en `panel_validacion.py`:

| Índice | Referencias de su familia |
|---|---|
| ITCIS | Mayoristas, shoppings, electricidad y gas residenciales, transporte y naftas |
| ITCG | Merval USD, inversión directa y de cartera de no residentes, financiamiento externo privado |
| ITCP | EPU, ICG UTDT y clima electoral |

Los factores comunes requieren cobertura suficiente. El ICC y los supermercados
ya son componentes del ITCIS y no lo validan de manera independiente. El
contrafáctico sin ICC se conserva como diagnóstico separado.

Se publican niveles, primeras diferencias, contrastes sin tendencia y pruebas
de giros. Una correlación de niveles alta no acredita causalidad ni capacidad
predictiva. Los resultados pueden ser débiles o negativos y deben conservarse.
La muestra corta y los rezagos de publicación limitan las conclusiones; una
reconstrucción revisada no reproduce necesariamente lo conocido en cada mes.

Las series históricas se reconstruyen desde sus componentes, con controles de
cobertura. Los valores recientes pueden diferir de la tarjeta que reúne el
último dato de cada fuente. El último mes del contraste no debe presentarse
como si coincidiera automáticamente con el período de la portada.

## Tests — `tests/`

La suite pytest sin red cubre bandas, interpolación y ejemplos completos de
ITCM/ITCG/ITVC/ITCP; contratos de fuentes; series; y reconciliación del snapshot
publicado (suma ponderada = índice, robustez encierra el valor, tensión =
fórmula). Cuando un ADR cambia el motor, los valores esperados se recalibran
**con el engine**, nunca a mano.
