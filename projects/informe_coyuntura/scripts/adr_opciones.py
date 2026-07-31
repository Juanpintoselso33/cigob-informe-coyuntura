"""Recupera a «Opciones consideradas» las alternativas que quedaron en prosa.

115 ADR no tenían sección de opciones y la migración les dejó una
declaración explícita de que el original no las registró. De esos, 54 sí
discuten alternativas evaluadas y descartadas, pero adentro del Contexto o
de la Decisión: «se descartó X porque…», «era la otra opción», «Rutas
investigadas y descartadas: …».

Este script las sube a la sección que les corresponde en MADR. Cada viñeta
es un resumen fiel de lo que ese ADR ya dice — con sus cifras y su motivo
de descarte. No se inventa ninguna alternativa: los 61 ADR que no discuten
ninguna conservan la declaración de que no fueron registradas.

La tabla es el juicio; el script solo la aplica. Se audita renglón por
renglón contra el cuerpo de cada ADR.

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
