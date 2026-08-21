---
madr: 4
id: '0222'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'vida'
indicadores: [sentimiento_digital]
archivos: ['scripts/vida_cotidiana/config.py', 'scripts/vida_cotidiana/collectors/trends.py', 'scripts/vida_cotidiana/main.py', 'scripts/descargar_series.py', 'scripts/publicar.py', 'scripts/gate_calidad.py', 'web/src/lib/fichas.ts', 'web/src/lib/descripciones.ts', 'web/src/lib/formulas.ts', 'web/src/lib/datos.ts', 'tests/test_sentimiento_canasta.py']
complementa: ['0034']
relacionado: ['0033', '0115', '0220']
ambito: 'ITCIS · `sentimiento_digital` · composición de la canasta de Google Trends, ponderación y empalme de escalas'
origen: 'Editor, agosto de 2026: sumar «dólar», «empleo» y «corrupción» a la canasta de búsquedas'
---

# ADR-0222 — La canasta de búsquedas pesa por término, no por volumen

## Contexto y planteo del problema

El pedido era chico: agregar tres términos —`dolar`, `empleo`, `corrupcion`— a
la canasta de cuatro que ADR-0034 dejó puntuando. Google Trends admite **cinco
términos por consulta**, así que siete no entran en una y hacía falta resolver
cómo empalmar dos consultas cuya escala es relativa a su propio payload.

Al medir el empalme apareció algo que no se estaba buscando: **el problema de
escalas no es el que se creía, y la canasta actual ya estaba rota por él.**

Trends normaliza cada consulta por un escalar —el máximo del payload vale 100—
y **redondea a entero**. Un término cuyo volumen es una fracción chica del
máximo del payload se queda sin resolución. Medido el 20 de agosto de 2026
sobre la ventana fija 2021→hoy:

| Término | Payload | Valores distintos en 68 meses | r contra su propia forma |
|---|---|---|---|
| `trabajo` | los 4 actuales | 33 | +1,000 |
| `precios` | los 4 actuales | 35 | +0,999 |
| `inflacion` | los 4 actuales | 18 | +0,998 |
| **`inseguridad`** | los 4 actuales | **2** (cero y uno) | **+0,529** |
| `dolar` | `inflacion` + los tres nuevos | 40 | +1,000 |
| **`corrupcion`** | `inflacion` + los tres nuevos | **1** (cero siempre) | indefinida |

«Su propia forma» es el mismo término consultado solo, que es su medición sin
truncar. O sea: **`inseguridad` lleva desde ADR-0034 aportando un dither de 0/1
en vez de una serie**, y `corrupcion` al lado de `dolar` no existe.

El segundo hallazgo es la ponderación. La canasta se calculaba como el promedio
del payload **en valores crudos**, y en esa escala los términos no pesan igual:
pesan por volumen. Los pesos implícitos eran

    trabajo 53%  ·  precios 38%  ·  inflacion 8%  ·  inseguridad 2,5%

Nadie eligió eso. Es un subproducto de que «trabajo» se busca veinte veces más
que «inseguridad», y explica por qué el indicador parecía estable: **más de la
mitad de su movimiento lo decidía un solo término**, y ese término resultó ser
el peor de los cuatro (abajo).

## Factores de decisión

- El empalme entre consultas tiene que estar **verificado con datos**, no
  supuesto.
- Un término tiene que medir lo que su nombre dice —la regla que ADR-0217 y
  ADR-0218 tuvieron que aplicar dos veces en este mismo cinturón.
- Los pesos de un compuesto se eligen y se declaran; no se heredan del volumen
  de búsqueda.
- El componente pesa 1,5% del ITCIS: la complejidad del cálculo tiene que estar
  a la altura de eso.

## Opciones consideradas

### Para el empalme de escalas

- **Término ancla en las dos consultas**, con el que se reescala la segunda —el
  camino estándar. Verificado y **descartado por innecesario**: ver abajo.
- **Rebasar cada término contra su propio 4T-2023 dentro de su propia
  consulta** — elegida.
- **Achicar la canasta a cinco** para que entre en una sola consulta —
  descartada: obliga a elegir qué término del pedido no entra por una razón
  técnica, y no resuelve el truncamiento, que ocurre *dentro* de la consulta.

### Para `trabajo` vs `empleo`

- **Entran los dos** — descartada: le da dos de siete pesos a la dimensión
  laboral, uno de ellos polisémico.
- **Se fusionan en un promedio** — descartada: promediar un término limpio con
  uno contaminado no limpia nada, sólo esconde la mezcla.
- **`empleo` reemplaza a `trabajo`** — elegida.

## Decisión

1. **La canasta pasa a seis términos con peso IGUAL, 1/6 cada uno**:
   `inflacion`, `precios`, `dolar`, `empleo`, `inseguridad`, `corrupcion`.
   Entran los tres pedidos; sale `trabajo`.

2. **Una consulta por término**, sobre la misma ventana fija 2021→hoy, y cada
   término se rebasa contra su propio 4T-2023 **dentro de esa consulta**. La
   canasta es el promedio simple de los seis índices.

3. **No hay ancla ni empalme.** Trends devuelve `c · real(t)` con `c` un escalar
   propio de cada consulta; al dividir por el promedio del 4T-2023 de la *misma*
   consulta, `c` se cancela. Es el argumento de invariancia de ADR-0034 aplicado
   **por término** en vez de a la canasta entera, y vuelve el tope de cinco
   términos irrelevante. El ancla sólo haría falta para conservar el peso por
   volumen entre términos, que es justamente el peso que esta decisión descarta.

4. **La serie publicada pasa a ser un índice base 100 = 4T-2023** (antes:
   interés 0–100). No cambia nada aguas abajo: `itvc.py` y
   `validacion_externa.py` la rebasean invertida contra su propio 4T-2023, y
   rebasear una serie que ya está en base 100 devuelve el mismo número.

5. **Se termina el doble registro card/serie.** La card publica el último mes
   cerrado de la misma canasta —desglosada por término— en vez de un pulso
   propio de tres meses. Con seis términos ese pulso costaba seis consultas más
   para un número que no puntúa. `sentimiento_digital` sale de las excepciones
   G3 del gate y el par vuelve a reconciliar.

6. **Cada término se reemplaza entero cuando su propia descarga es sana**; el
   que falla conserva su serie previa, y la canasta sólo emite los meses en que
   están los seis. Antes el reemplazo era todo-o-nada porque mezclar corridas
   mezclaba escalas; con el rebase por término cada serie es adimensional y
   convivir deja de ser un problema.

### Por qué sale `trabajo`

`empleo` y `trabajo` **no son redundantes**: r = +0,39 en el mismo payload,
+0,40 por separado. Lo que decide no es la correlación sino de qué está hecho
lo que `trabajo` agrega. Sus *related queries* del último año:

| `trabajo` | `empleo` |
|---|---|
| ley de trabajo · trabajo social · ministerio de trabajo · ley contrato de trabajo · potenciar trabajo · día del trabajo · trabajo practico | portal empleo · portal de empleo · oficina de empleo · computrabajo · bolsa de empleo · linkedin empleo · buscar empleo |

Derecho laboral, un plan social, el feriado y la tarea escolar de un lado;
búsqueda de trabajo del otro. Su estacionalidad lo confirma: `trabajo` hace
pico en mayo (1,17×) y piso en enero (0,83×) y diciembre (0,84×) —el calendario
escolar—, mientras que `empleo` es plano salvo diciembre.

Y es el término que sostenía la aparente estabilidad del indicador: con 53% del
peso y el rango dinámico más chico de los siete (sd del log = 0,134 contra 0,503
de `inflacion`), anclaba la canasta cerca de 100. **La estabilidad del indicador
venía del término con peor validez de constructo.**

### Cómo se lee `corrupcion`

Es un proxy de **saliencia de escándalo**, no de urgencia del hogar, y eso está
declarado: un pico se lee como «se habla de un caso», no como «empeoró el
bolsillo». El único mes que supera el doble de su mediana en cinco años es
agosto de 2025, y aporta +14,9 puntos a la canasta de ese mes.

Entra igual, y no por deferencia al pedido: es el término **menos redundante**
de los seis (|r| máximo 0,24 contra cualquier otro) y el que más señal aporta.
Sacándolo de la canasta nueva, la correlación entre los cambios mensuales de la
canasta y los del ICC de la UTDT en los últimos 18 meses se da vuelta y queda en
+0,10 —o sea, sin señal y con el signo equivocado—; con él queda en −0,52.

El indicador vive en la dimensión de *confianza y percepción* (ADR-0115), donde
la saliencia de un escándalo es parte de lo que se mide, no una intrusión.

### Por qué peso igual y no otra cosa

Los seis términos son **casi ortogonales entre sí**: la correlación absoluta
máxima entre sus índices es 0,56 (`inflacion`–`empleo`) y la mediana es 0,27.
No hay bloques que corregir —`inflacion`, `precios` y `dolar` no son «lo mismo»:
r(inflacion, precios) = −0,29—, así que agrupar por tema no tendría sustento.

Se probó una ponderación por influencia igual (peso ∝ 1/sd del log, para que
cada término aporte lo mismo a la varianza). Mueve poco el resultado y le da el
peso más alto al término más plano, que en esta canasta es sinónimo del más
diluido. Se descartó: es una perilla sin número que la justifique.

### Consecuencias

**El ITCIS de hoy no se mueve.** El componente ya venía recortado en el techo de
140 (ADR-0033) y sigue ahí:

| | Antes | Después |
|---|---|---|
| Canasta (índice, jul-2026) | 67,2 | 57,6 |
| Componente crudo (invertido) | 148,8 | **173,6** |
| Componente aplicado (techo 140) | 140,0 | 140,0 |
| Dimensión percepción | 99,8 | 99,8 |
| **ITCIS** | **90,6** | **90,6** |

Sobre los 67 meses de historia el componente cambia 16,0 puntos en promedio, que
al 1,5% que pesa son **0,24 puntos de ITCIS en promedio y 0,60 en el mes de
mayor efecto**.

**La limitación que esto deja declarada, y que es el resultado y no un
artefacto**: la canasta nueva pasa el techo de 140 en **19 de 67 meses** (7 de
los últimos 12) contra 1 de 67 antes. La lectura honesta es que la urgencia
digital hoy está ~42% por debajo del pánico del 4T-2023 y el techo absorbe la
diferencia; la lectura incómoda es que un componente recortado siete meses de
cada doce deja de informar. No se corrige acá acomodando la canasta —eso sería
elegir los términos para que el número quede lindo—: **el techo de ADR-0033 y la
base 4T-2023 de este componente son una decisión editorial aparte**, y ésta es
la anotación de que hace falta tomarla.

**Exposición al rate limit.** La corrida pasa de una consulta a Trends a seis, y
Trends bloquea por IP con facilidad —durante este trabajo bloqueó por más de una
hora—. Lo compensan tres cosas: la card dejó de tener consulta propia (antes eran
dos rondas, ahora una), el store es idempotente dentro del día (el colector y
`descargar_series.py` comparten los mismos seis pedidos) y un término que falla
conserva su serie previa en vez de tirar abajo la canasta entera. Si la fuente
queda muda varios días, la demora la ve G2 como en cualquier fuente mensual: la
card se fecha con el mes del dato y no con la corrida, que antes era lo que la
hacía verse fresca siempre.

### Confirmación

`tests/test_sentimiento_canasta.py` cubre lo que puede volver a romperse: que la
canasta tenga los seis términos y ninguno repetido, que ninguno exceda el tope
de cinco por consulta, que el rebase por término sea invariante al escalar de la
consulta (la propiedad que reemplaza al ancla), que un término sin los tres
meses de la base no entre, que la canasta sólo emita meses completos, que la
serie llegue al 4T-2023, que un store del formato anterior —misma forma, otra
unidad— se descarte en vez de publicarse como si fuera un índice, que la card se
feche con el mes del dato, y que sin canasta el fetcher levante en vez de
devolver una lista vacía que borraría la serie del CSV.

Las 26 guardas se probaron **rompiéndolas a propósito** y comprobando que
fallan. Dos pasaban por el motivo equivocado y hubo que rehacerlas: la del store
viejo se cumplía por una clave ausente y no por la marca de formato, y la de la
ficha se conformaba con que los términos aparecieran en la lista de cambios —o
sea, daba por buena una ficha que contara que entraron y siguiera describiendo
la canasta vieja—.

El par card/serie lo vigila G3 en `gate_calidad.py`, ahora sin excepción.

**Corrida real (21-ago-2026, 14:01).** Las cifras de arriba se calcularon sobre
respuestas de Trends capturadas a mano mientras la IP estaba bloqueada; la
corrida del colector las reproduce **al décimo**: canasta 57,6 en jul-2026,
componente crudo 173,6, y el techo superado en 19 de 67 meses, 7 de los últimos
12. La card publica 57,6 y la serie termina en 57,6 —el par reconcilia—, el
ITCIS queda en 90,6 y el gate pasa sin fallas de integridad. En el store de
producción cada término tiene entre 32 y 42 valores distintos en 67 meses: los 2
de `inseguridad` y el 1 de `corrupcion` dentro de un payload compartido eran el
truncamiento, y desaparecieron.

## Más información

### El banco de pruebas (20–21 de agosto de 2026)

**Estabilidad.** Dos corridas del mismo payload el mismo día dan valores
idénticos (diferencia máxima 0,00 en el índice B100, r = +1,0000) para
`trabajo`, `empleo`, `corrupcion` e `inseguridad`. Reproduce lo que ADR-0034
había medido con tres corridas.

**Invariancia de escala — la prueba que reemplaza al ancla.** Para el mismo
término leído en dos consultas distintas, el cociente entre las dos lecturas
tiene que ser una constante si la consulta sólo aplica un escalar:

| Término | Cociente medio | CV del cociente | Diferencia máx. del índice B100 |
|---|---|---|---|
| `trabajo` | 1,000 | 0,0% | 0,00 |
| `dolar` | 1,000 | 0,0% | 0,00 |
| `precios` | 0,813 | 0,8% | 1,39 |
| `inflacion` | 0,227 | 2,9% | 4,98 |
| `empleo` (truncado) | 0,036 | 17,9% | 30,11 |
| `inseguridad` (truncado) | 0,015 | 43,0% | 77,19 |

Las cuatro primeras filas son la verificación: el escalar existe, es único y se
cancela. Las dos últimas son el modo de falla, y **no es del empalme sino del
truncamiento**: un término sin resolución dentro de su payload no tiene forma
que empalmar. De ahí la regla de una consulta por término.

**Validación de constructo.** Contra los cambios mensuales del ICC de la UTDT en
los últimos 18 meses —donde se espera signo negativo, más búsquedas de urgencia
con peor ánimo—: la canasta actual da −0,32 y la nueva −0,52. Con los siete
términos (dejando `trabajo` adentro) da −0,61; sacándole `corrupcion` a esa
misma canasta de siete queda en −0,05, y sacándosela a la de seis, en +0,10.
O sea: el signo lo sostiene `corrupcion`, no la cantidad de términos. Contra
el IPC mensual en niveles, la canasta nueva conserva r = +0,61, igual que la
actual (+0,61); ADR-0034 reportaba +0,76 sobre una ventana más corta.

Se informan las cuatro cifras a propósito. La composición **no se eligió
maximizando esa correlación** —con 17 diferencias mensuales, elegir por ahí es
sobreajustar y es la circularidad que ADR-0120 vino a acotar—: se eligió por
validez de constructo y resolución, y la correlación se mira después, como
resultado.

### Lo que no se tocó

- El peso del componente (1,5% del ITCIS) y los pesos internos de la dimensión
  percepción quedan como los dejó ADR-0115.
- El techo de winsorización de 140 (ADR-0033) queda como está, con la limitación
  anotada arriba.
- `itvc.py` y `validacion_externa.py` no cambian: el rebase invertido de una
  serie ya en base 100 devuelve el mismo índice.

### Precedente que esto extiende

ADR-0034 descartó «Inflación en Argentina» como índice porque sus visitas habían
colapsado seis veces desde diciembre de 2023 —«detector de eventos, no índice»—.
`dolar` tiene la misma forma: su 4T-2023 fue un pico de pánico cambiario y hoy
está en 19,7 contra esa base. Se revisó si eso era un quiebre de régimen —el fin
del cepo en abril de 2025 habría hecho desaparecer la consulta rutinaria del
«dólar blue», que es el 44% de sus related queries— y **no lo es**: la caída es
gradual y del mismo orden que la de `inflacion` (0,68× contra 0,66× entre
ene-2024/mar-2025 y abr-2025/jul-2026), y abril de 2025 es un pico local, no un
escalón. Entra, y su nivel bajo es una lectura, no un artefacto.
