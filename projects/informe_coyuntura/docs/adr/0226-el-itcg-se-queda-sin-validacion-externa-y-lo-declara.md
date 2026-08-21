---
madr: 4
id: '0226'
estado: 'aceptado'
fecha: 2026-08-21
cinturon: 'gestion'
archivos: ['scripts/validacion_externa.py', 'scripts/publicar.py', 'tests/test_giros_referencia_completa.py']
relacionado: ['0031', '0045', '0108', '0158', '0159', '0161', '0162', '0164', '0167', '0218', '0225', '0228', '0229']
ambito: 'ITCG · contra qué se valida el índice, y qué se hace cuando la respuesta es que no hay contra qué'
origen: 'Editor, 21-ago-2026: «buscar alguna validación externa que sea UN SOLO INDICADOR», y después: «no vamos a privar al índice de validez, robustez y capacidad por tener un validador externo que es un accesorio» · «sigue faltando la validez externa después»'
---

# ADR-0226 — El ITCG se queda sin validación externa única, y lo declara

`scripts/validacion_externa.py` · `scripts/publicar.py`
- **Relacionados**: [[0225-el-supermercado-deja-de-validar-el-indice-y-pasa-a-integrarlo]]
  (el mismo movimiento en el otro cinturón, y el precedente que ordena éste),
  [[0159-validacion-por-panel-para-los-socioeconomicos]] y
  [[0161-el-contraste-externo-es-un-factor-comun-no-una-variable]] (el panel),
  [[0162-aporte-del-indice-por-encima-de-la-tendencia]] (la vara que decidió),
  [[0158-validacion-del-itcm-por-puntos-de-giro]] (el régimen de giros),
  [[0218-el-cierre-de-pymes-se-mide-con-la-srt]] (el error de categoría)

## Contexto y planteo del problema

El editor pidió una validación externa que fuera **un solo indicador**, con la
condición que ordena todo lo demás: *"tiene que ser contra una que sea un BUEN
validador, no cualquier cosa que correlacione bien"*. Elegir por el r es
circular, y en una muestra de treinta y un meses casi todas las series
argentinas comparten la tendencia del período.

El ancla vigente era el **Merval en dólares**, y al medirla resultó peor de lo
que parecía:

| | Merval en dólares |
|---|---|
| niveles (lo que se publicaba) | **+0,751** |
| **destendenciado** | **+0,066** |
| cambios mes a mes | +0,132 |
| \|r\| medio en cambios de las estadísticas AJENAS del panel | 0,153 |

El 99% de la correlación publicada era que las dos series suben durante treinta
y un meses. Y el índice se movía mes a mes con el que era su contraste propio
**menos** que con el promedio de las series que no tienen nada que ver con él.

### El hallazgo estructural: la serie que uno querría no existe

Antes de mirar un número se escribió qué tendría que moverse en el mundo si el
ITCG mide bien, y recién después se buscó. Lo primero que apareció es lo que
**no** hay: **ninguna serie mensual, argentina, publicada por un tercero, que
mida avance de reformas**. Y los índices internacionales de capacidad o calidad
estatal, contra los 31 puntos mensuales del ITCG:

| fuente | puntos desde dic-2023 | por qué |
|---|---|---|
| OCDE, regulación de mercados de productos | **0 utilizables** | se actualiza cada cinco años y la edición vigente retrata el Estado **antes** de la desregulación |
| Fraser, libertad económica | **0** | la edición de sep-2025 rankea el año 2023 |
| Banco Mundial, efectividad de gobierno y calidad regulatoria | 1 | anual, y la revisión 2025 recalculó la serie histórica hacia atrás |
| Bertelsmann (capacidad de conducción / implementación) | 1 | bienal, y su ventana mezcla diez meses de la gestión anterior |
| OCDE, encuesta de confianza en el gobierno | 0 | **Argentina no participa** |
| Heritage · Índice de Calidad Institucional | 3 | el techo del barrido; el ICI además promedia ocho fuentes de terceros, dos discontinuadas |

Tampoco hay tracker argentino independiente con serie descargable: el balance de
promesas de Chequeado es **anual** y el tablero del Ministerio de Desregulación
publica un stock al momento de la consulta, sin historia.

**Eso explica por qué el ancla había terminado siendo un precio de mercado.**

## Factores de decisión

- **Un validador tiene que medir una CONSECUENCIA, no un instrumento.** El ITCG
  mide lo que el gobierno **hizo**; lo que lo valida tiene que medir lo que
  **pasó** por haberlo hecho.
- **Quien produce el dato no puede ser quien rinde el examen.**
- **El índice manda; el ancla se elige de lo que queda** — la regla editorial de
  [[0225-el-supermercado-deja-de-validar-el-indice-y-pasa-a-integrarlo]]: *"no
  vamos a privar al índice de validez, robustez y capacidad por tener un
  validador externo que es un accesorio"*.
- Antes de mover un indicador se mide si duplica señal: matriz de redundancia
  con umbral 0,7, en niveles **y destendenciada**
  ([[0108-redundancia-interna-del-itvc]]).
- El aporte de una serie se juzga con el R² incremental sobre una tendencia
  ([[0162-aporte-del-indice-por-encima-de-la-tendencia]]).
- No se mueve nada para que un número quede mejor
  ([[0045-comisiones-caidas-recalibracion-bandas]]).

## Opciones consideradas

- **El ITCG se queda sin ancla única, publica el panel y declara la validez
  externa como problema abierto** — elegida.
- **El gasto en subsidios económicos como ancla titular** — era la recomendación
  de la investigación y **se descartó**: error de categoría y productor
  interesado.
- **El gasto en subsidios como componente del índice** — evaluado con la misma
  vara que el supermercado y **descartado por la medición**.
- **Riesgo país (EMBI)** — mejora al Merval en los tres planos pero cae bajo la
  misma objeción conceptual: sigue siendo una expectativa de mercado.
- **Precio relativo de los regulados** — el mejor en números y descalificado.
- **Resultado financiero del SPN** · **empleo público (SIPA)** — fallan.
- **Mantener el Merval como titular** — descartada.

### Lo que dio cada candidata, medido antes de decidir

Contra la reconstrucción mensual del ITCG, dic-2023 → jun-2026. La columna que
manda es la de **cambios mes a mes** ([[0167-el-ancla-de-validacion-se-elige-en-diferencias]]);
con n = 30, el \|r\| crítico al 5% es 0,361.

| candidata | niveles | destendenciado | **cambios** | cambios 2025-26 |
|---|---|---|---|---|
| Subsidios económicos, 12m real | −0,942 | −0,308 | **−0,263** | **−0,360** |
| Precio relativo de los regulados | +0,862 | +0,464 | **+0,405** | −0,126 |
| Riesgo país (EMBI) | −0,874 | −0,234 | −0,286 | −0,245 |
| Percepción de eficiencia del gasto (UTDT) | −0,489 | +0,082 | +0,282 | +0,483 |
| Empleo público (SIPA) | −0,947 | −0,428 | −0,263 | −0,112 |
| Resultado financiero del SPN, 12m real | +0,816 | +0,268 | **+0,062** | −0,203 |
| **Merval en dólares** (ancla anterior) | +0,751 | +0,066 | +0,132 | +0,197 |

**El mejor en números estaba descalificado.** El precio relativo de los regulados
era el único que cruzaba significancia al 5%, y su serie de origen —el IPC
Regulados— era el numerador de `peso_tarifas`, **componente del ITCIS**. ADR-0232
reemplazó luego ese componente por la canasta IIEP; este párrafo conserva el
universo evaluado en esta decisión, no describe la fuente tarifaria vigente. Además
su correlación es el episodio tarifario de 2024: el precio relativo salta de 100
a 140,5 entre dic-2023 y dic-2024, se ameseta, y de ene-2025 en adelante el r se
apaga y cambia de signo.

**Los dos que parecían obvios se caen.** El resultado financiero del SPN era el
candidato conceptual número uno —si el Estado ejecuta el ajuste, el resultado
mejora— y da **+0,062** en cambios, con el signo invertido desde 2025. La serie
explica por qué: el resultado 12m real mejora sin parar durante 2024 (de −4.139 a
+371 mil millones de pesos constantes) y **se deteriora desde entonces** —+214 en
dic-2025, +137 en may-2026, **−11,9 en jun-2026**— mientras el ITCG va de 49,3 a
81,8. **El índice y el resultado fiscal se desacoplaron a principios de 2025.**
El empleo público, por su parte, cae 2,5% en treinta meses: su −0,947 en niveles
es una deriva mínima y monótona.

## Decisión

### 1. El gasto en subsidios NO es validación externa, y el motivo es de categoría

Es la parte que conviene dejar escrita para que nadie la reintente. Los
subsidios correlacionaban bien —de todas las candidatas mensuales limpias era la
única cuya correlación en cambios se **fortalece** en la segunda mitad de la
muestra— y aun así están del lado equivocado de la comparación:

> **El ITCG mide lo que el gobierno HIZO. Un validador tiene que medir lo que
> PASÓ como consecuencia.**

Bajar subsidios es un **instrumento** de la misma agenda que el índice puntúa,
no un efecto de ella. Que correlacione no es sorprendente ni informativo: es
casi una identidad. Es el mismo error de categoría que
[[0218-el-cierre-de-pymes-se-mide-con-la-srt]] corrigió cuando `mortalidad_pymes`
medía producción industrial — un número que anda y un nombre que promete otra
cosa.

Y se suma una objeción que sola ya alcanzaría: **lo publica la Secretaría de
Hacienda**, es decir el mismo gobierno cuya ejecución el índice mide. Un índice
de ejecución validado contra el reporte de gasto de quien ejecuta es corregir el
examen con el examen.

### 2. Tampoco entra como componente, y lo decidió la medición

Si los subsidios miden que la agenda avanza, entonces son candidatos a
**indicador** del ITCG — la jugada que
[[0225-el-supermercado-deja-de-validar-el-indice-y-pasa-a-integrarlo]] hizo con
las ventas en supermercados. Se los evaluó con la misma vara.

**Redundancia: la habrían pasado.** Contra los catorce componentes, seis pares
superan 0,7 en niveles —`cepo_mulc` −0,919, `desregulacion_normativa` −0,911,
`reduccion_estado` −0,890, `libertad_opcion_salud` −0,880, `protocolo_antipiquetes`
−0,868, `privatizaciones` −0,814— pero **todos se desarman al destendenciar**: el
máximo cae a +0,494 y el par que más se sospechaba, `gasto_funcionamiento`, da
−0,314 en niveles y **−0,044** destendenciado. Es la época en común, no señal
repetida. Y el contexto lo confirma: la matriz vigente del ITCG tiene **18 pares
sobre 0,7 de 77** (23%), **10 de sus 14 componentes** arrastran al menos uno, y
el más alto es **+0,994** (`libertad_opcion_salud` × `protocolo_antipiquetes`).
Vetar al que entra por 0,92 sería aplicarle un estándar que diez de los catorce
que ya están adentro no cumplen.

**Aporte: no lo pasa, y es lo que decide.** Regresado sobre las cinco dimensiones
del ITCG:

| plano | R² | de su variación NO reproducida por el índice |
|---|---|---|
| niveles | 0,960 (ajustado 0,952) | **4%** |
| destendenciado | 0,607 (ajustado 0,528) | 39% |
| primeras diferencias | 0,247 (**ajustado 0,090**) | 75% |

El primero hay que leerlo con cuidado y se declara: una simple recta en el tiempo
ya explica el **0,884** de su nivel, así que buena parte de ese 96% es tendencia
de los dos lados. Por eso la decisión no se apoya ahí sino en la vara del
proyecto, [[0162-aporte-del-indice-por-encima-de-la-tendencia]]:

> **aporte sobre tendencia = 0,011**, con el signo esperado.

Contra los **0,347** con los que el supermercado se ganó su lugar en el ITCIS, y
en el mismo orden de magnitud que los **0,006** del contraste que ese mismo
movimiento descartó. No alcanza.

Como referencia de escala, la misma regresión sobre series que nadie propone
como componentes del ITCG deja **31% sin reproducir** (Merval) y **42%**
(actividad). El candidato deja 4%. En el plano donde este índice vive —es un
compuesto de contadores acumulados, cuyo movimiento mes a mes es sobre todo
ruido— los subsidios son casi una función de lo que el índice ya tiene.

### 3. La validez externa del ITCG queda declarada como PROBLEMA ABIERTO

El titular pasa a ser el **factor común del panel** —el valor de las empresas en
dólares y tres medidas de cuánto capital de afuera entra—, que es contra lo que
el gráfico ya venía comparando. El Merval **sale de titular y no se retira**:
sigue siendo una de las cuatro del panel, que es lo que siempre fue.

Y la sección **dice que no hay validación externa única posible hoy**, con el
barrido de arriba. Declararlo es más honesto que llenar la casilla con la serie
que mejor correlacione, que es exactamente lo que el editor pidió no hacer.

**Cuatro condiciones, fijadas de antemano**, para que la promoción de una
candidata futura no dependa de mirar el número el día que aparezca:

1. medir una **consecuencia** de la capacidad de gestión, no un instrumento de
   la agenda;
2. publicarla **alguien que no sea el poder ejecutivo nacional**;
3. tener **al menos 24 observaciones** desde diciembre de 2023;
4. **aportar 0,10 o más** de R² sobre una tendencia en el tiempo, con el signo
   esperado.

El umbral de 0,10 es **convención declarada**: se ubica un orden de magnitud por
encima de lo que aportan los contrastes ya descartados (0,006 y 0,011) y por
debajo del alta que sí prosperó en otro cinturón (0,347).

### Consecuencias

- La matriz cruzada ([[0031-validacion-cruzada-tercer-pilar]]) lee
  `validacion.pares` del bloque del ITCG. Al pasar el titular al factor, esa
  clave cambia de contenido: la columna se renombra de `merval` a
  `capital_privado`. Dejarla con el rótulo viejo habría hecho que la matriz
  dijera una cosa y comparara otra, sin que nada avisara — el mismo detalle que
  [[0225-el-supermercado-deja-de-validar-el-indice-y-pasa-a-integrarlo]] tuvo que
  atrapar en el otro cinturón.
- `validacion_externa` publica ahora el **r destendenciado** del Merval. Es el
  número que sostiene todo el cambio y no estaba en ningún lado; se calcula, no
  se escribe a mano, para que envejezca con los datos.
- **No se tocó ningún indicador, ningún peso ni ninguna banda.** El ITCG sigue
  con sus catorce componentes.
- **El ITCG y el ITCIS quedan los dos sin serie de referencia única**, cada uno
  por su motivo y los dos declarados. El ITCM conserva la suya
  ([[0158-validacion-del-itcm-por-puntos-de-giro]]) y el ITCP el EPU.

### Confirmación

`tests/test_giros_referencia_completa.py` fija el hallazgo metodológico que sale
de acá (ver abajo). El resto lo cubren los tests que ya existían: la matriz
cruzada, el panel y las fichas.

## Pros y contras de las opciones

**A favor de declarar el problema abierto.** Es verdad, es verificable, y evita
la trampa que el editor nombró: llenar la casilla con lo que mejor correlacione.
Un lector que ve "no hay contra qué validar esto todavía, y estas son las cuatro
condiciones que tendría que cumplir una candidata" sabe más que uno que ve un
+0,75 que es 99% tendencia.

**En contra, dicho de frente.** El cinturón se queda sin el número que un lector
espera de una sección llamada validación externa. El factor común del panel es
menos legible que una serie sola —fue la objeción original del editor y sigue en
pie—, y su varianza explicada es del 46,4%: menos de la mitad del movimiento de
las cuatro series es común. El panel del ITCG además tiene una brecha
convergente-discriminante **negativa en los dos planos**, así que tampoco está
sosteniendo mucho. Nada de esto se arregla con este ADR; queda medido y a la
vista, que es lo único que corresponde hacer mientras no exista la serie.

## Más información

### El hallazgo que sobrevive a la decisión: recortar la referencia fabrica giros

La investigación había medido una concordancia de fase de **0,815** entre el ITCG
y el gasto en subsidios. Al implementarlo dio **0,593**, y la diferencia no era
un bug.

`puntos_de_giro` estima el ciclo como desviación de una media móvil centrada, así
que **en el borde de una serie la tendencia se calcula con ventana incompleta y
aparecen extremos locales que no existen**. [[0158-validacion-del-itcm-por-puntos-de-giro]]
ya lo había documentado hacia adentro. Lo que faltaba es la otra mitad: si la
**serie de referencia** se recorta para hacerla coincidir con la ventana del
índice, el corte crea un borde nuevo en medio de datos que sí existen.

| historia de la referencia que entra al cálculo | concordancia | giros de la referencia dentro de la ventana |
|---|---|---|
| recortada en dic-2023 | 0,815 | 3 |
| con 12 meses más | 0,519 | 2 |
| completa (desde 2017-11) | **0,593** | **1** |

Dos de los tres giros los había fabricado el corte. El test que quedó lo fija por
dos caminos: uno sintético que demuestra el mecanismo —con la misma ventana de
solape y los mismos giros del índice, la referencia recortada inventa giros
adentro y mueve la concordancia— y uno sobre la corrida real, que exige que la
referencia del ITCM traiga al menos una ventana entera de historia previa. Para
que ese segundo mire lo que corresponde, `giros_itcm` registra ahora la ventana
de la referencia que **entró al cálculo** y no la serie que se descargó: sin eso
el test miraba el insumo y no el cálculo, y recortar la referencia movía la
concordancia publicada de 0,600 a 0,643 **con el test en verde**.

Corolario del mismo hallazgo, y por eso no se publica: la concordancia del ITCG
contra el Merval (0,208) **no es utilizable**. El colector del Merval trae sólo
tres años, así que su serie está estructuralmente recortada y su ciclo, medido
contra un borde. El argumento contra el Merval se sostiene igual con los tres
números de Pearson, que no dependen de esto.

### El contraste que distingue: la percepción de eficiencia del gasto

La UTDT pregunta todos los meses, dentro de su Índice de Confianza en el
Gobierno, por la **eficiencia en la administración del gasto público**. Entre
dic-2023 y jun-2026 ese subíndice **bajó de 2,51 a 2,12** sobre 5 mientras el
ITCG subía de 18,7 a 81,8: **−0,489** en niveles, el signo contrario al esperado,
que en cambios mes a mes se da vuelta a **+0,282** y en 2025-26 sube a **+0,483**.

No se publica como cifra y el motivo es de mantenimiento: la UTDT publica el
índice general como planilla pero **no** ese subíndice como serie, así que
reconstruirlo exige bajar 25 MB de microdatos por un camino frágil y sumar una
dependencia que el proyecto no tiene. La reconstrucción se hizo una vez, el
21-ago-2026, y se verificó contra el índice general publicado —diferencia media
absoluta **0,0066** sobre 138 meses—, pero **un contraste que se cae si un
archivo deja de publicarse es peor que no tenerlo**. Lo que sí se publica es el
ICG total, que sigue siendo el contraste discriminante de la sección.

### La conclusión acotada que vale igual

Si en algún momento se decidiera conservar un ancla de mercado para este
cinturón, **el riesgo país es estrictamente mejor que el Merval en los tres
planos** —−0,874 en niveles contra +0,751, −0,234 destendenciado contra +0,066,
−0,286 en cambios contra +0,132—. No resuelve la objeción conceptual, que es la
que motivó todo esto, pero queda anotado por si el criterio cambia.

### El colector que quedó escrito y no se usa

El colector del gasto en subsidios —las dos líneas del IMIG, deflactadas y
acumuladas a doce meses, con guardas que fallan en voz alta si las líneas no
llegan al mismo mes o si hay un hueco en la fuente— se escribió y se testeó antes
de que la decisión cambiara. **No entra al repositorio**: no tiene dónde
enchufarse y código sin uso es deuda. Queda en la rama `wt-ancla-itcg-respaldo`
por si el criterio cambia; lo que importa conservar es el razonamiento de arriba,
no las cincuenta líneas.
