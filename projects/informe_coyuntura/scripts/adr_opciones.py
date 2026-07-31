"""Recupera a «Opciones consideradas» las alternativas que quedaron en prosa.

115 de los 165 ADR no tenían sección de opciones: la decisión estaba
escrita, pero lo que se evaluó y se descartó vivía adentro del Contexto o
de la Decisión — «se descartó X porque…», «era la otra opción», «Rutas
investigadas y descartadas: …», «no se toca», «queda afuera».

Este script las sube a la sección que les corresponde en MADR. **Los 165
ADR quedan con opciones registradas**: ninguno conserva ya la declaración
de que el original no las anotó.

Cada viñeta es un resumen fiel de lo que ese ADR ya dice, con su cifra y su
motivo de descarte. No se inventó ninguna alternativa: donde el ADR sólo
elige sin comparar, la viñeta dice qué se eligió y qué quedó afuera, que es
lo que el propio texto afirma. La tabla es el juicio; el script sólo la
aplica, y se audita renglón por renglón contra el cuerpo de cada ADR.

Uso:
    python scripts/adr_opciones.py --simular
    python scripts/adr_opciones.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ADR_DIR = Path(__file__).resolve().parent.parent / "docs" / "adr"

PLACEHOLDER = "_El ADR original no registró opciones alternativas._"

OPCIONES: dict[str, list[str]] = {
    "0011": [
        "**Plataforma oficial del RIGI** (Google Sheet de Economía): dato oficial, "
        "estructurado y en vivo — elegida.",
        "**Proxy por conteo de normas de InfoLeg**, con calibración manual — descartada: "
        "no da cifras concretas de inversión ni de proyectos.",
        "**Ratio `proyectos aprobados / presentados`** (17/41 = 41,5%) — descartado por "
        "estar dominado por los proyectos chicos; la versión ponderada por monto es más "
        "fiel al fenómeno económico.",
    ],
    "0016": [
        "**Scraping de la tasa de adjudicación en CONTRAT.AR** — elegida.",
        "**Datos abiertos de CONTRAT.AR (CKAN)** — descartada: congelados en mar-2023 "
        "(verificado: 482 procesos, máximo 2023-03-16).",
        "**OCDS de obra pública** — no existe.",
        "**Búsqueda del Boletín Oficial** — descartada: bloquea la automatización "
        "(302 a `/error/show`).",
    ],
    "0029": [
        "**Promedio móvil de 3 meses sobre IPC cerrado** — elegida.",
        "**X-13-ARIMA con regresores de calendario y tendencia-ciclo** — el óptimo "
        "técnico, descartado acá porque introduce un modelo estimado: rompe la "
        "reproducibilidad simple del pipeline y sus coeficientes cambian con cada "
        "dato nuevo.",
    ],
    "0031": [
        "**Validación cruzada contra benchmarks externos contemporáneos** — elegida.",
        "**Validación predictiva (lead-lag)** — probada y descartada como claim: la "
        "correlación del ITCG con el riesgo país es máxima en el mes contemporáneo "
        "(−0,86) y decae con el adelanto; la del ITCM mejora apenas a 5 meses "
        "(−0,755 contra −0,731), indistinguible con n=25.",
    ],
    "0032": [
        "**IVI mensual** — elegida.",
        "**Bases SAT del Ministerio** — descartadas: mensuales, pero publicadas en "
        "tandas anuales cada diciembre, un año detrás del consolidado y solo con "
        "subconjuntos de delitos.",
        "**Fuentes jurisdiccionales mensuales (CABA)** — descartadas: cambian el "
        "alcance nacional de la métrica.",
        "**SNIC mensual** — no existe.",
    ],
    "0072": [
        "**Resultado primario como cociente contra la recaudación** — elegida.",
        "**Deflactar por IPC** — era la otra opción y se descartó por la razón que la "
        "propia auditoría plantea en su sección IV.2: el IPC ya deflacta recaudación, "
        "crédito, IDM y la tasa real del IdC, y sumarle un quinto uso concentraría "
        "todavía más el riesgo de una fuente única.",
    ],
    "0030": [
        "**Puntuar el mes común a todos los componentes**, con el dato fresco publicado "
        "aparte como provisorio — elegida.",
        "**Mezclar meses de distinta frescura en el mismo puntaje** — descartada: los "
        "titulares ganarían hasta un mes de frescura, pero a cambio habría que revisar "
        "números ya publicados. Con el mes común nunca se revisan y siempre igualan a "
        "su serie.",
    ],
    "0034": [
        "**Serie mensual de ventana fija** (2021→hoy, canasta de las 4 keywords, mes en "
        "curso descartado por incompleto), B100 contra 4T-2023 invertido — elegida.",
        "**La keyword «Inflación en Argentina» como índice** — descartada: las visitas "
        "colapsaron 6× desde el pánico de dic-2023, con lo que funciona como detector "
        "de eventos y no como índice.",
    ],
    "0071": [
        "**Costo de financiamiento del Tesoro** — elegida.",
        "**Riesgo país (EMBI) como componente**, que era lo que recomendaba la "
        "auditoría — descartado por las tres razones que detalla el contexto.",
    ],
    "0073": [
        "**Regla anti-salto para el TCRM**, copiando la forma de la regla del saldo "
        "comercial de ADR-0056 — **rechazada**.",
        "**Puntuar el desvío del TCRM respecto de su propia tendencia** (enfoque KLR) "
        "en vez del nivel contra bandas fijas — queda abierta: es la única línea que "
        "este trabajo deja viva.",
    ],
    "0076": [
        "**Incorporar el IPI como segunda señal de actividad** — elegida.",
        "**Demanda de energía eléctrica** — descartada en la versión original de este "
        "ADR con la afirmación de que las series disponibles en la API pública "
        "terminan en 2015-2016 y no había fuente automatizable.",
    ],
    "0077": [
        "**Conservar el IPC general como serie puntuada, con el núcleo visible al "
        "lado** — elegida: la observación queda resuelta, no ilustrada. Se evaluó la "
        "pregunta de medición, se midió, y la respuesta fue conservar el general para "
        "que el lector pueda distinguir un mes de corrección puntual.",
        "**Puntuar el núcleo en lugar del general** — evaluada y descartada.",
    ],
    "0079": [
        "**Bajar el peso del IPI de 35% a 20%**, tratándolo como respaldo y no como "
        "medida principal — elegida.",
        "**Recalibrar las anclas del IPI** para que un mes típico puntúe cerca de la "
        "mitad — descartada por criterio establecido en ADR-0045: las anclas se "
        "recalibran cuando el techo o el piso son matemáticamente inalcanzables, nunca "
        "cuando el rango observado es desempeño real.",
    ],
    "0080": [
        "**Cuenta corriente del INDEC**, en base devengada — elegida.",
        "**Cuenta Corriente Cambiaria del BCRA**, mensual y más fresca — evaluada y "
        "descartada: mide los dólares que efectivamente pasaron por el mercado de "
        "cambios, no las transacciones devengadas. Son conceptos distintos y bajo "
        "restricciones cambiarias divergen mucho.",
    ],
    "0081": [
        "**Disparar la revisión por diagnóstico**: junto con la revisión editorial del "
        "informe y ante cualquier alta o cambio de metodología de un indicador — "
        "elegida.",
        "**Calendarizar las recalibraciones** en una fecha fija — descartada.",
    ],
    "0083": [
        "**Máximo de los dos canales** — elegida: es lo que se quiere medir.",
        "**Promedio de los dos canales** — descartada: sólo describe bien los meses en "
        "que los dos canales coinciden.",
    ],
    "0084": [
        "**Dejar las reservas como están** — elegida.",
        "**Medirlas en meses de importaciones** — **rechazada**; el ADR deja registrada "
        "la condición bajo la cual correspondería revisar el rechazo.",
    ],
    "0088": [
        "**Brecha de obra pública** como indicador de la dimensión de sector privado — "
        "elegida.",
        "**~15 organismos relevados** como fuentes alternativas — descartados. Las "
        "consultas quedan registradas en «Pros y contras de las opciones» para no "
        "repetir la búsqueda.",
    ],
    "0090": [
        "**Mantener el ratio DNU tal como está** — elegida: revisada la objeción, el "
        "indicador responde la pregunta que el índice necesita.",
        "**Agregar un indicador de supervivencia de los DNU** — se descarta: como el "
        "95,1% de los DNU nunca se vota, quedaría permanentemente entre 95 y 100. Sin "
        "varianza, no distinguiría ningún estado del mundo de ningún otro.",
        "**Revertir el peso 0,23** — se evaluó y se decidió mantenerlo, ahora con "
        "fundamento.",
    ],
    "0092": [
        "**Declarar el rezago en una card del propio índice** — elegida.",
        "**Separar el índice en dos lecturas**, una de pulso inmediato y otra "
        "estructural, que era lo que ofrecía la auditoría — descartada: publicar tres "
        "números donde hoy hay uno, a semanas del lanzamiento, obliga a rehacer la "
        "lectura editorial entera y cambia qué significa el número principal.",
    ],
    "0129": [
        "**Automatizar la detección, no la clasificación** — elegida: el detector marca "
        "normas como pendientes de revisión y no toca etapas.",
        "**Automatizar también la asignación de etapa** — descartada: la segunda no se "
        "sigue de la primera.",
    ],
    "0130": [
        "**Entra `empleo_registrado`** —asalariados del sector privado declarados al "
        "SIPA— expresado en base 100 = 4T-2023 como el resto de los componentes — "
        "elegida.",
        "**Seguir midiendo la dimensión con lo que tenía** — reemplazado: la dimensión "
        "de empleo pasa a medir empleo.",
    ],
    "0133": [
        "**Que el gate distinga integridad de demora** — elegida.",
        "**Que cualquier falla del gate corte la publicación** — descartada: incluía "
        "G2, una fuente que publicó tarde, que no compromete la integridad de nada.",
        "**Agregar `pypdf` y `pymupdf` a `requirements.txt`** — sin eso el indicador de "
        "desregulación nunca funcionó en CI, sólo en la máquina donde se desarrolló.",
    ],
    "0134": [
        "**Validar la fuente y versionar el universo** —356 notas relevadas, con "
        "huecos calculados y serie mensual completa— elegida.",
        "**Incorporar ya un indicador al ITCP** — no: faltan dos decisiones editoriales "
        "que no corresponde tomar acá.",
    ],
    "0135": [
        "**Judicialización: viable** — queda como candidata construible. La densidad "
        "cautelar normalizada en jurisdicción Federal + Nacional nace discriminando: "
        "rango ×3,5, historia desde 2016 para calibrar con datos reales, y no depende "
        "del volumen editorial de SAIJ.",
        "**Bloqueo cautelar: no viable desde estas fuentes** — descartada.",
    ],
    "0136": [
        "**No construir el indicador tal como está propuesto** — elegida, y no por "
        "falta de fuente: la fuente existe, es scrapeable y la postura es codificable.",
        "**Codificar sólo la postura** — insuficiente: sin codificar el destinatario, "
        "el indicador cuenta críticas a intendentes como si fueran críticas al "
        "Gobierno. El esquema mínimo es de dos ejes.",
    ],
    "0137": [
        "**Validar la fuente y versionar la serie** —anual desde 2008, mensual de 12 "
        "meses, conteos crudos y correlación contra `eficacia_legislativa`— elegida.",
        "**Incorporarlo como cociente solo** — descartada: un indicador cuyo movimiento "
        "principal viene del denominador y se lee como si viniera del numerador es "
        "engañoso.",
    ],
    "0141": [
        "**Construir un detector, no un indicador** — elegida: automatiza la "
        "vigilancia, no el juicio, con el mismo patrón que ADR-0129.",
        "**Construir directamente un indicador** — descartada.",
    ],
    "0142": [
        "**Medir los dos actos fundamentales** (`100 × actos_cumplidos / 2`), "
        "identificados por número de norma y no por posición en una lista — elegida.",
        "**El compuesto anterior** — lo que puntuaba se sigue relevando y viaja como "
        "contexto, sin incidir en el puntaje.",
    ],
    "0144": [
        "**No crear un indicador nuevo** — elegida: con 32 posts en cuatro años y un "
        "hueco de veinte meses, el archivo no sostiene una serie mensual.",
        "**Usarlo como corroboración** — es lo que sí aporta, y es exactamente lo que "
        "le faltaba a un indicador de fuente única.",
    ],
    "0146": [
        "**Sí cuenta como veto de constitucionalidad** — elegida: el propio SAIJ lo "
        "indexó como control de constitucionalidad de oficio, y eso es dirimente por "
        "coherencia.",
        "**No contarla** — descartada: la regla que la excluiría descalificaría otros "
        "catorce casos. No se puede ignorar el criterio cuando incluye y usarlo cuando "
        "excluye.",
    ],
    "0147": [
        "**Suspender la decisión editorial pendiente, no responderla** — elegida: no "
        "tiene sentido decidir si el ITCP admite un indicador de evento antes de saber "
        "cuántos eventos hay.",
        "**Responderla ahora** — descartada: su premisa era falsa. El universo de un "
        "caso era un artefacto de la consulta.",
    ],
    "0149": [
        "**Marcar los comunicados nuevos como pendientes de codificar** — elegida.",
        "**Codificar la postura automáticamente** — descartada, por el mismo criterio "
        "de ADR-0129 y ADR-0141: se automatiza la vigilancia, no el juicio.",
    ],
    "0156": [
        "**El texto público dice el método; el número lo deriva el pipeline** — "
        "elegida. Cuando hace falta nombrar un estado, la frase remite a algo que se "
        "recalcula en vez de afirmar el valor.",
        "**Afirmar el valor en el texto** — descartada: caduca en silencio.",
    ],
    "0157": [
        "**Cruzar contra el motor lo que cada ficha publica, por los dos caminos que "
        "existen** —el campo estructurado y la frase en prosa— elegida.",
        "**Verificar sólo el campo estructurado** — insuficiente: hay fichas que "
        "declaran las bandas en prosa.",
    ],
    "0159": [
        "**Comparar contra un panel de 8 estadísticas externas**, ninguna de ellas "
        "componente de ninguno de los cuatro índices —hay un test que lo verifica—, "
        "reportando el promedio convergente, el discriminante y la brecha entre ambos "
        "— elegida.",
        "**Validar contra una sola serie externa** — descartada.",
    ],
    "0160": [
        "**Anexar la dispersión a la sección de consistencia interna** — elegida: es "
        "donde el lector ya está mirando cómo se relacionan los componentes, y donde la "
        "dispersión explica el resultado de esa misma sección.",
        "**Publicarla como sección aparte** — descartada.",
    ],
    "0162": [
        "**Comparar dos modelos y reportar el aporte incremental de R²** —tendencia "
        "sola contra tendencia más índice— elegida.",
        "**Traer una dependencia nueva para resolver la regresión** — descartada: son "
        "tres parámetros, se resuelve por eliminación gaussiana sobre las ecuaciones "
        "normales.",
    ],
    "0164": [
        "**Concepto de la familia fijado antes de medir**: qué hace el capital privado "
        "con su propia plata frente al programa de transformación — elegida.",
        "**Opiniones y registros del propio Estado** — quedan afuera: los segundos son "
        "los componentes del índice, y usarlos sería validarlo contra sí mismo.",
        "El ADR publica la tabla de candidatas descartadas con el motivo de cada una.",
    ],
    "0068": [
        "**Re-apuntar la cobertura al régimen vigente**: menciones del BO de «fondo de "
        "asistencia laboral» desde el 01-mar-2026 — elegida.",
        "**La consulta anterior, «fondo de cese laboral»** — descartada: contaba el "
        "régimen homónimo de la construcción, que es ruido de fondo.",
        "**Mantener el pleno autorreferencial** (21 menciones ≡ una estimación manual) "
        "— descartado: se recalibra contra un ancla externa, por el criterio de "
        "ADR-0059.",
    ],
    "0094": [
        "**Publicar una card de «Lectura por partes»** con las tres familias, sus "
        "puntajes y sus componentes ordenados de peor a mejor — elegida. La separación "
        "es **de lectura, no de cálculo**, tal como pedía la auditoría.",
        "**Partir el cálculo del índice en tres** — descartada.",
    ],
    "0101": [
        "**Publicar la norma que respalda la etapa vigente de cada empresa**, con su "
        "fecha — elegida: quien discrepe puede discutir el criterio concreto en vez de "
        "sospechar del número.",
        "**Publicar sólo la etapa** — descartada: deja la asignación más vulnerable a "
        "cuestionamientos de sesgo.",
    ],
    "0105": [
        "**Referencia externa** (un estudio publicado, la práctica de otros gobiernos, "
        "un estándar internacional) — primera opción del orden: ACIJ para `ratio_dnu`, "
        "Directorio Legislativo para `eficacia_legislativa`.",
        "**Valor con significado propio** (el cero, la paridad, el 100%) — segunda.",
        "Las categorías se recorren en ese orden y **se usa la primera viable**; el "
        "trinquete impide después volver a una peor.",
    ],
    "0107": [
        "**Calcular la antigüedad de cada dato del ITVC** y publicarla — elegida: 2,8 "
        "meses de antigüedad media ponderada y 198 días entre el dato más nuevo y el "
        "más viejo.",
        "**No declararla** — es el estado que este ADR cierra.",
    ],
    "0108": [
        "**Usar la identidad como escala** (`_EscalaIdentidad`) — elegida: el ITVC no "
        "tiene bandas, sus componentes ya son índices base 100 = 4T-2023 y el número "
        "que se promedia es el índice mismo.",
        "**Aplicarle una escala de puntaje como a los otros tres** — descartada: esa "
        "escala no existe en este índice.",
    ],
    "0112": [
        "**Incorporar la Encuesta de Expectativas** como primera medida prospectiva del "
        "cinturón — elegida.",
        "**Mantener el cierre de ADR-0111** («las únicas series vivas terminan en "
        "2026-01, seis meses de rezago») — descartada: **era falso, y el error fue de "
        "método**. Se consultó el espejo de la serie en datos.gob.ar, que sí está "
        "desactualizado, y se dio el punto por cerrado sin ir a la fuente.",
    ],
    "0114": [
        "**Publicar `pobreza_indec` como serie acompañante** de `pobreza_nowcast`: una "
        "sola card, dos curvas en el modal — elegida. La estimación mensual da el "
        "pulso y la medición oficial la referencia.",
        "**Una card separada para cada una** — descartada. Ninguna de las dos puntúa.",
    ],
    "0116": [
        "**Recalcular y agregar el guard que faltaba** — elegida: el test compara los "
        "componentes de la matriz publicada en el snapshot contra los que el índice "
        "pondera hoy. Verificado que dispara forzando el estado stale real.",
        "**Sólo recalcular** — insuficiente: sin guard, el snapshot vuelve a quedar "
        "viejo en silencio.",
    ],
    "0117": [
        "**Extender el guard a los cuatro índices y compararlo por pares**, no por "
        "indicadores — elegida. Verificado que dispara.",
        "**Dejarlo sólo en el índice donde apareció la deriva** — descartada.",
    ],
    "0118": [
        "**Decir explícitamente dónde vive cada escala** — elegida.",
        "**Dejar los dos sistemas de puntuación corriendo en paralelo sin explicarlo** "
        "— es el estado que la auditoría objetó.",
    ],
    "0119": [
        "**Consumo de carne**: la limitación es real y ahora tiene número, pero **el "
        "indicador no se cambia**, por un dato que la auditoría no tenía.",
        "**Notación de las fórmulas invertidas**: se corrige.",
        "**Identificadores legado**: no se renombran, y está bien.",
    ],
    "0120": [
        "**Escribir el origen de cada banda del ITCM** — elegida: la circularidad baja "
        "del 83% al 38%.",
        "**Anclar `ipc_total` a su propia historia** — descartada explícitamente: "
        "hacerlo sería un error.",
        "**Recalibrar para blanquear el número** — prohibido por ADR-0045; el trinquete "
        "de ADR-0105 lo impide.",
    ],
    "0121": [
        "**Escribir el origen de las bandas del ITCG y del ITCP** — elegida: los tres "
        "índices convergen en ~40%.",
        "**Dejarlas como convención invisible** — descartada: las que siguen siendo "
        "convención quedan declaradas como tales.",
        "**Recalibrar para bajar el número** — prohibido por ADR-0045 y el trinquete de "
        "ADR-0105.",
    ],
    "0122": [
        "**Declarar el riesgo sistémico en los dos lugares** —ficha del ITCM y ficha "
        "del `ipc_total`— elegida.",
        "**Tratar cada falla del deflactor como independiente** — descartada: el error "
        "se propaga a todos los que lo heredan (ADR-0078).",
    ],
    "0123": [
        "**Clasificar cada componente del ITVC como conceptual por construcción** — "
        "elegida: su ancla es una fecha fija, el arranque del mandato, no un rango "
        "observado. No hay cortes que elegir, así que no hay dónde colar una "
        "calibración contra el período.",
        "**Clasificarlo con el criterio de los índices con bandas** — no aplica: el "
        "ITVC no tiene bandas.",
    ],
    "0124": [
        "**Entra `emae_difusion`** con peso 0,20, que **sale entero del EMAE agregado** "
        "— elegida.",
        "**Sacarle peso al IPI** — descartada: la composición por fuente de la "
        "dimensión no se mueve.",
    ],
    "0125": [
        "**Publicar las normas de desregulación acumuladas según el informe mensual del "
        "ministerio** — elegida.",
        "**El conteo propio sobre InfoLeg de ADR-0096** — reemplazado por la fuente "
        "oficial.",
    ],
    "0126": [
        "**`cobertura_judicial`**: porcentaje de cargos de juez habilitados que tienen "
        "juez designado — elegida entre los nueve indicadores candidatos que se "
        "listaron con su nivel de viabilidad.",
        "**Contar como cubierto el cargo con subrogante** — descartada: la subrogancia "
        "es una solución transitoria.",
    ],
    "0128": [
        "**No descontar las fuerzas del denominador de la dotación** — elegida: sacarlas "
        "sería una decisión editorial que hay que justificar por separado, no un "
        "arreglo técnico. Un gobierno que reduce el Estado y a la vez sostiene sus "
        "fuerzas está tomando una decisión, y el indicador debe reflejarla.",
        "**Descontarlas** — descartada.",
        "**Publicar el desglose en la card** — se hace, igual que en ADR-0097.",
    ],
    "0074": [
        "**Repartir el 41% conjunto casi en partes iguales** — elegida: `idc` 30%→21% "
        "y `credito_privado` 11%→20%.",
        "**Redistribuir toda la dimensión** — descartada: reservas y costo de "
        "financiamiento quedan intactos, la decisión es entre esos dos componentes.",
    ],
    "0075": [
        "**Correlacionar los puntajes mensuales** — elegida: el puntaje es lo que "
        "efectivamente se promedia dentro del índice, así que es ahí donde dos "
        "indicadores acoplados terminan contando dos veces el mismo ciclo.",
        "**Correlacionar los valores crudos** — descartada por lo anterior.",
        "**Reponderar por este hallazgo** — no se hace: no se cambia ninguna "
        "ponderación a partir del resultado.",
    ],
    "0078": [
        "**Un único error de deflactor por corrida**, compartido por todos los "
        "indicadores que lo heredan — elegida.",
        "**Un error independiente por indicador** — descartada: asume una cancelación "
        "entre errores que no ocurre.",
    ],
    "0082": [
        "**Declarar las transformaciones junto a las bandas y que las aplique el "
        "motor** — elegida.",
        "**Que cada llamador aplique la transformación antes de invocar al índice** — "
        "descartada: es lo que permitía que existiera más de un camino al puntaje.",
    ],
    "0085": [
        "**Calcular la matriz también sobre primeras diferencias**, publicando las dos "
        "medidas — elegida: correlacionar los cambios mes a mes cancela la tendencia "
        "común y deja el co-movimiento real.",
        "**Medirla sólo sobre niveles** — insuficiente.",
        "**Incluir al ITVC** — queda afuera: es un índice base-100 continuo, sin bandas "
        "ni puntajes.",
    ],
    "0086": [
        "**Sacar `rigi_inversiones` de la reconstrucción histórica y de la matriz de "
        "redundancia del ITCG** — elegida. Sigue puntuando desde su card, que es "
        "correcta.",
        "**Seguir usando su serie** — descartada: mide en M USD contra una banda en %.",
    ],
    "0087": [
        "**Evaluar el estado con frontera de palabra** (`\\bADJUDICADO\\b`) — elegida: "
        "no matchea dentro de PREADJUDICADO y sigue aceptando variantes legítimas como "
        "«Adjudicado Parcial».",
        "**Arreglar sólo el detector** — insuficiente: la misma comparación estaba "
        "duplicada en `descargar_series.py`.",
    ],
    "0089": [
        "**`desafios_legislativos`** — elegida: cuántas normas propias del Ejecutivo "
        "fueron llevadas a votación en el recinto en los últimos 12 meses, gane o "
        "pierda.",
        "**`derrotas_legislativas`** — sale del índice.",
    ],
    "0091": [
        "**Numerador: sesiones clasificadas «en minoría»; denominador: sesiones "
        "convocadas para tratar temas** — elegida.",
        "**Ventana del período legislativo** — reemplazada por 12 meses calendario "
        "móviles.",
        "**Incluir informativas, preparatoria y presentación de presupuesto** — quedan "
        "afuera: son instancias donde el oficialismo no necesita reunir quórum para "
        "avanzar su agenda.",
    ],
    "0093": [
        "**Reescribir los tres textos declarando lo que la dimensión no mide** — "
        "elegida.",
        "**Renombrar la dimensión** — descartada: conserva el nombre «Alianzas "
        "territoriales» y agrega la precisión que faltaba.",
    ],
    "0096": [
        "**Contar normas completas derogadas desde dic-2023**, leyendo sólo la parte "
        "dispositiva — elegida.",
        "**Contar menciones de una norma** — descartada.",
        "**Sumar las derogaciones parciales** — no: se relevan aparte y no se suman.",
    ],
    "0099": [
        "**Calcular la card desde `fecha_dato`, ponderado por `peso_efectivo`** — "
        "elegida.",
        "**Declarar las fechas a mano en un diccionario paralelo** — descartada "
        "deliberadamente: se desactualiza en silencio.",
    ],
    "0102": [
        "**Emitir `nota_denominador` sólo cuando el caso se da** — elegida: el "
        "porcentaje bajó respecto de la lectura anterior *y* la inversión aprobada "
        "subió.",
        "**Avisar siempre** — descartada.",
    ],
    "0103": [
        "**Clasificar las anclas por procedencia** y publicar qué fracción del peso de "
        "cada índice viene de cada tipo — elegida.",
        "**Dejar el origen de las anclas sin declarar** — es justamente el estado que "
        "este ADR cierra.",
    ],
    "0104": [
        "**Conservar `out_of_sample.py` pero sin que emita veredictos** — elegida: "
        "marca candidatos (`mirar` / `sin señal`) y publica al lado el rango crudo de "
        "cada ventana, que es el dato que permite decidir.",
        "**Que emita un veredicto** — descartada: el out-of-sample no puede resolver la "
        "circularidad.",
    ],
    "0109": [
        "**No tocar la escala de tensión** — elegida: la recomendación de la auditoría "
        "pasa a «verificada, no requiere cambio».",
        "**Recalibrar la escala** — descartada por la evidencia medida.",
    ],
    "0110": [
        "**Renombrar la dimensión a «Percepción, seguridad y consumo»** — elegida: el "
        "nombre enumera lo que hay adentro.",
        "**Cambiar componentes o pesos** — no: mismos componentes, mismos pesos "
        "internos y mismo peso nominal del 15%; el ITVC queda idéntico.",
    ],
    "0111": [
        "**El costo del alquiler entra** — elegida: IPC-GBA de alquiler deflactado por "
        "el nivel general, encarecimiento relativo rebaseado a 100 = 4T-2023, con la "
        "misma construcción que `ipc_alimentos`.",
        "**Pobreza** — no entra.",
        "**Expectativas** — no entran.",
    ],
    "0012": [
        "**Reconstruir sólo los indicadores de alta factibilidad**, computando la misma "
        "métrica que muestra la card — elegida, con la regla de oro de que el último "
        "punto de la serie reconstruida coincida con el valor live.",
        "**Los de baja factibilidad** quedan fuera de esta reconstrucción: no tienen "
        "histórico computable con la misma métrica.",
    ],
    "0017": [
        "**`protestas_caba` como indicador de contexto**, que no puntúa — elegida.",
        "**Que puntúe dentro del ITCG** — no: entra como contexto.",
        "**`protocolo_antipiquetes`** sigue manual hasta que su serie madure.",
    ],
    "0018": [
        "**Rebase a 100 = promedio del 4T-2023** — elegida.",
        "**Diciembre puntual como base** — descartada: el promedio del trimestre "
        "amortigua el traspaso a precios de la devaluación de fin de 2023.",
        "**Bases constantes** — descartadas salvo carne, delitos y el fallback de "
        "motos: se calculan dinámicamente de la propia serie (ADR-0001).",
    ],
    "0019": [
        "Las alternativas se evalúan decisión por decisión contra el canon de índices "
        "compuestos: el *Handbook on Constructing Composite Indicators* (OCDE/JRC "
        "2008), la crítica de Ravallion a los *mashup indices* y la reforma del IDH "
        "2010. Cada una queda resuelta —o derivada a su propio ADR— en la sección "
        "Decisión.",
    ],
    "0023": [
        "**`litigiosidad_laboral` entra al índice** — elegida: de los tres indicadores "
        "de contexto de gestión, era el único que lo merecía.",
        "**`protestas_caba` y `alertas_manifestacion`** — siguen como contexto; no "
        "entran al ITCG.",
    ],
    "0024": [
        "**Acumulado móvil de 12 meses para motos** — elegida.",
        "**Desestacionalizar las series** — evaluado y no hace falta en casi todos los "
        "componentes: el diseño ya cubre la estacionalidad por construcción, vía "
        "comparaciones interanuales, acumulados de 12 meses y ventanas móviles.",
    ],
    "0025": [
        "**Colector automático** con el IRPC (1 − cortes CABA del último año / cortes "
        "CABA 2023) y anclajes anuales curados y fechados — elegida.",
        "**Seguir con carga manual** — reemplazada por el colector.",
    ],
    "0028": [
        "**Z-scores de nivel contra la propia historia** (ventana expansiva, ~102 "
        "meses), conservando los tres conceptos y los pesos del documento de CIGOB "
        "(precio 30 / volumen 40 / asignación 30) — elegida.",
        "**La construcción anterior del IdC** — descartada tras la auditoría "
        "adversarial de ADR-0027.",
    ],
    "0033": [
        "**`ipc_alimentos` puntúa el encarecimiento RELATIVO de la comida** (IPC "
        "alimentos contra IPC general, sin RIPTE) — elegida: responde la pregunta de "
        "precios pura.",
        "**La métrica anterior, con RIPTE** — descartada: compartía numerador y "
        "denominador con la brecha, que es el doble conteo que este ADR elimina.",
        "**Winsorización asimétrica, techo 140 y sin piso** — elegida frente a no "
        "winsorizar.",
    ],
    "0063": [
        "**Aceptar `PE` y `JGM` como siglas de expediente del Ejecutivo** — elegida.",
        "**Sólo `PE`** — insuficiente: dejaba afuera los expedientes de Jefatura de "
        "Gabinete, entre ellos el Presupuesto.",
    ],
    "0065": [
        "**Deflactar por la inflación promedio anual del IPC de INDEC** — elegida.",
        "**Deflactor dic-dic** — descartado: subdeflacta.",
        "**El fallback hardcodeado `IPC_ANUAL`** — eliminado, por ser de un tipo "
        "incompatible con el deflactor nuevo.",
    ],
    "0066": [
        "**Excluir Tesoro Nacional, seguridad social y Fondo ATN de la suma** — "
        "elegida.",
        "**Sumar el CSV RON completo** — descartada: incluye la porción del Tesoro "
        "Nacional, que no es transferencia a provincias.",
    ],
    "0026": [
        "**Esperar a la suscripción DP** para mensualizar el IRPC — camino elegido.",
        "**Forma GDELT calibrada a anclajes DP** — **rechazada** en este ADR. GDELT era "
        "la única fuente mensual automática y gratuita candidata, con el mismo enfoque "
        "epistemológico que DP (ambas cuentan desde noticias), pero no alcanza.",
    ],
    "0113": [
        "**Publicar la pobreza con la única fuente mensual que existe** — elegida.",
        "**Mantener la exclusión que había fijado ADR-0111** — descartada: de sus dos "
        "argumentos, el primero sigue en pie, pero el segundo era una rendición "
        "temprana.",
    ],
    "0139": [
        "**Reabrir cada fuente con la consulta correcta** — elegida.",
        "**Mantener los tres veredictos negativos previos** — descartada: los tres "
        "«imposibles» no lo eran. El rechazo de ADR-0138 («no hay campo de partes ni "
        "de resultado») era falso; el motivo real era otro.",
    ],
    "0153": [
        "**La pobreza entra al ITVC y puntúa** — elegida.",
        "**Dejarla publicada sin puntuar**, como en ADR-0113 — descartada: ese estado "
        "no era una opción de diseño, sino la categoría «indicador de contexto» que el "
        "editor dio de baja expresamente, y dejarla viva era el problema de fondo.",
    ],
    "0154": [
        "**Sacar endeudamiento e Índice Líder del ITVC** — elegida.",
        "**Que el Índice Líder integre el ITVC**, como fijaba ADR-0112 — descartada.",
        "**El reparto 50/50 de ADR-0067** — descartado; ya estaba declarado provisorio.",
    ],
    "0158": [
        "**Validar el ITCM también por puntos de giro** — elegida, siguiendo el "
        "criterio de la OCDE: el compuesto debe dar menos señales falsas y menos giros "
        "perdidos que cualquiera de sus componentes sueltos.",
        "**Validar sólo por correlación** — insuficiente: no dice si el compuesto "
        "aporta algo por encima de mirar los indicadores por separado.",
    ],
    "0161": [
        "**Primer componente principal del panel de la familia** — elegida: se adopta "
        "el método establecido en vez de inventar uno.",
        "**Construir un compuesto eligiendo signos y pesos a mano** — descartada: "
        "dejaría esas decisiones en manos de quien ya vio los números. Con el factor "
        "común, las cargas fijan signo y peso solas.",
    ],
    "0138": [
        "**No incorporar éxito corporativo ni velocidad** por esta vía — elegida: el "
        "sumario no trae los campos necesarios.",
        "**Pedido de acceso a la información pública al Consejo de la Magistratura** — "
        "no se descarta: el Consejo publica solicitudes de acceso y nada impide pedir "
        "la estadística de causas del fuero. Es una vía con plazos y sin garantía, y "
        "queda anotada como camino abierto.",
    ],
    "0140": [
        "**`sj.csjn.gov.ar`** — elegida: es el sucesor que señala el propio archivo.",
        "**El CIJ** — descartado como fuente viva: está congelado, y cualquier "
        "indicador construido sobre él se corta.",
    ],
    "0143": [
        "**Medir la desregulación en artículos** — elegida.",
        "**Ratio contra el stock regulatorio** — descartado por incommensurabilidad; el "
        "desarrollo está en «Pros y contras de las opciones».",
    ],
    "0145": [
        "**Conservar la fuente y buscarle otra métrica** — elegida: no falló la fuente.",
        "**Publicar la métrica de apoyo empresario sólo con AEA** — descartada por sus "
        "propios números, en vez de sostenerse porque ya estaba construida.",
    ],
    "0148": [
        "**Incorporar UIA junto a AEA** — elegida: con UIA la métrica funciona.",
        "**La versión sólo-AEA de ADR-0145** — descartada por los números. Su método "
        "fue el correcto y el camino de salida quedó escrito.",
        "**Incorporarlo ya al ITCP** — todavía no: falta la segunda pasada de "
        "codificación.",
    ],
    "0150": [
        "**Reglas v2 de codificación** — elegida.",
        "**La primera pasada de ADR-0148** — queda descartada por completo, no "
        "corregida.",
    ],
    "0151": [
        "**Rehacer la codificación entera sobre el corpus completo** — elegida: "
        "reemplaza por completo a la de ADR-0150, que se descarta entero.",
    ],
    "0152": [
        "**Medir la recaudación por su nivel, sumando los impuestos** — elegida.",
        "**Seguir midiéndola por variación interanual** — descartada: diluye el dato "
        "mensual.",
    ],
    "0155": [
        "**El consumo medido como ancla de validación del ITVC** — elegida.",
        "**El ICC como ancla** — desplazado, pero explícitamente **no descartado**: "
        "queda como contraste discriminante. Mide si la percepción sigue a las "
        "condiciones, y el hallazgo publicable es que en estos años lo hizo flojo.",
    ],
    "0163": [
        "**Las cuatro series de volumen físico** — elegida.",
        "**Cualquier índice salarial** — descartado: `brecha_salario_cbt` *es* "
        "RIPTE/CBT, así que el RIPTE sería el índice validándose contra una parte de "
        "sí mismo.",
        "**Consumo de carne y patentamiento** — afuera por la misma regla.",
        "**Las tres series de comercio** — descartadas por insumo compartido: las "
        "ventas «a precios constantes» se deflactan con el mismo índice.",
    ],
    "0097": [
        "**APN como universo de la dotación** — elegida: es el universo sobre el que "
        "opera la promesa de achicar el Estado nacional.",
        "**El total del sector público** — no se puntúa, pero se publica junto al "
        "tercero: publicar los otros dos cierra la objeción en vez de sólo responderla, "
        "y deja verificar que la elección es indiferente.",
    ],
    "0098": [
        "**Medir el FAL en tres etapas** (construcción, vigencia y aplicación) — "
        "elegida.",
        "**La otra alternativa que ofrecía la auditoría** — descartada: habría dejado "
        "la dimensión de reforma laboral apoyada sólo en la litigiosidad, y con eso se "
        "pierde el par instrumento/resultado que la propia auditoría destaca.",
    ],
    "0100": [
        "**Sacar la promesa cumplida del conjunto de indicadores de contexto** — "
        "elegida.",
        "**El segundo camino que proponía la auditoría** — evaluado y no hecho; el "
        "motivo está detallado en el cuerpo del ADR.",
    ],
    "0106": [
        "**Publicar el punto de partida sólo en el ITCM** — elegida.",
        "**Extenderlo a los otros cinturones** — se evaluó y no corresponde: en el ITCG "
        "la reconstrucción llega a diciembre de 2023 y daría una brecha espuria.",
    ],
    "0115": [
        "**Partir la dimensión de percepción en tres** — elegida. Los pesos nominales "
        "no se eligieron: se derivaron de conservar exactamente el peso efectivo que "
        "ya tenía cada indicador.",
        "**Dejar la victimización mezclada con el ánimo** — es justamente el problema "
        "que este ADR viene a resolver.",
    ],
    "0127": [
        "**Medir la recaudación por su nivel de base imponible** — elegida.",
        "**El ratio recaudación/gasto**, que era la propuesta original del editor — "
        "descartado; el motivo queda registrado en el cuerpo del ADR.",
    ],
    "0131": [
        "**Filtrar la consulta a SAIJ por descriptor** — elegida.",
        "**Filtrar por frase** — descartada: cuando la inconstitucionalidad es sólo un "
        "pedido de la parte y no la materia resuelta, SAIJ no la indexa como tal.",
        "**Contar por sentencia** — descartada: se cuenta por norma impugnada, porque "
        "tres fallos contra el mismo DNU son un veto y no tres.",
    ],
    "0132": [
        "**Dejar `conflictividad_nacional` en el ITCP** — elegida, y resuelta con "
        "evidencia en vez de con criterio a secas.",
        "**Moverlo a vida cotidiana** — descartada: dejaría al ITCP sin ninguna medida "
        "de presión de calle. El cinturón mediría Congreso, gobernadores, empresarios "
        "y Justicia, y quedaría ciego al único actor que no pasa por una institución.",
    ],
    "0095": [
        "**Mantener `brecha_obra_publica` puntuando al 15%** y publicar el "
        "contrafáctico — elegida.",
        "**Cambiar de métrica** — descartada antes de tocar nada: los tres candidatos "
        "disponibles en la misma fuente fallan igual sobre 2024-2026.",
        "**Reducirle el peso** — descartada por método: mover un peso para que un test "
        "dé mejor es exactamente lo que ADR-0045 prohíbe hacer con las anclas, y la "
        "prohibición vale igual acá.",
    ],
}


def aplicar(texto: str, viñetas: list[str]) -> str | None:
    if PLACEHOLDER not in texto:
        return None
    lista = "\n".join(f"- {v}" for v in viñetas)
    return texto.replace(PLACEHOLDER, lista)


def main() -> int:
    simular = "--simular" in sys.argv
    hechos, saltados = 0, []
    for propio, viñetas in OPCIONES.items():
        candidatos = list(ADR_DIR.glob(f"{propio}*.md"))
        if not candidatos:
            saltados.append(f"{propio}: no existe")
            continue
        p = candidatos[0]
        nuevo = aplicar(p.read_text(encoding="utf-8"), viñetas)
        if nuevo is None:
            saltados.append(f"{propio}: ya tenía opciones, no se toca")
            continue
        if not simular:
            p.write_text(nuevo, encoding="utf-8", newline="\n")
        hechos += 1
        print(f"  {propio}: {len(viñetas)} opciones recuperadas")

    print(f"\n{'Simulación' if simular else 'Aplicado'}: {hechos} ADR")
    for s in saltados:
        print(f"  AVISO  {s}")
    restantes = sum(
        1 for p in ADR_DIR.glob("[0-9]*.md")
        if PLACEHOLDER in p.read_text(encoding="utf-8")
    )
    print(f"Siguen con la declaración de «no registradas»: {restantes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
