import sys
from datetime import date
sys.stdout.reconfigure(encoding='utf-8')

# ── Ponderación entre cinturones: por fase del mandato ────────────────────────
# "Marco Conceptual del Informe de Coyuntura" (CIGOB, may-2026): "los cinturones
# no tienen igual peso temporal. En los primeros 2-4 años de gobierno
# (especialmente en ciclos electorales cortos), el cinturón de gestión (...)
# pesa más que en gobiernos de largo plazo" — construye el capital de
# credibilidad que después permite sacrificios macro mayores. El doc no fija
# números: estos valores son la operacionalización CIGOB-informe (ajustar
# cuando la fundación los formalice).
#
# Son CUATRO desde el 2026-08-14 (ADR-0205). Espíritu de época salió del
# tablero: era provisorio, tenía un solo indicador y aun así se llevaba el 20%
# del global. El marco de Matus sigue teniendo su cinturón de espíritu de
# época; lo que se retira es la operacionalización, que no estaba a la altura
# de pesar como los otros cuatro.

MANDATO_INICIO = date(2023, 12, 10)   # asunción del mandato presidencial vigente
FASE_TEMPRANA_ANIOS = 4               # "primeros 2-4 años": tomamos el techo

PESOS_FASE_TEMPRANA = {               # mandato en construcción de credibilidad
    "macro": 0.25,
    "politica": 0.25,
    "vida_cotidiana": 0.25,
    "gestion": 0.25,
}
# Consolidación: se conservan los pesos RELATIVOS que tenían los cuatro entre
# sí (25/25/20/15 sobre 0,85) renormalizados a 1. Sacar un cinturón no es
# ocasión para recalibrar la importancia de los otros: eso sería una decisión
# de metodología distinta, y se toma aparte si se toma.
PESOS_FASE_CONSOLIDACION = {          # mandato consolidado (4+ años / reelección)
    "macro": 0.29,
    "politica": 0.29,
    "vida_cotidiana": 0.24,
    "gestion": 0.18,
}


def fase_mandato(hoy: date | None = None) -> str:
    hoy = hoy or date.today()
    anios = (hoy - MANDATO_INICIO).days / 365.25
    return "temprana" if anios < FASE_TEMPRANA_ANIOS else "consolidacion"


def pesos_cinturones(hoy: date | None = None) -> dict:
    return PESOS_FASE_TEMPRANA if fase_mandato(hoy) == "temprana" else PESOS_FASE_CONSOLIDACION


# Pesos vigentes hoy (lo que consumen generar_informe.py y publicar.py).
PESOS_CINTURONES = pesos_cinturones()

# ── Siglas PÚBLICAS de los cuatro índices (ADR-0190) ──────────────────────────
# La sigla que lee el lector no es la clave técnica. `itvc` sigue siendo la
# clave del snapshot, el nombre del módulo y el de las tablas de BigQuery: lo
# que cambió en agosto de 2026 es cómo se llama en la página, junto con el
# cinturón (Vida cotidiana → Impacto social). Las otras tres esperan la
# definición editorial que ADR-0190 dejó pendiente —incluida la colisión de
# ITCG con el ICG de la UTDT, que el propio informe publica—; cuando lleguen
# se cambian acá y en web/src/lib/datos.ts::indiceDe, que son los dos únicos
# lugares donde la sigla se declara. La prosa las nombra literal, y
# tests/test_siglas_publicas.py es el que impide que quede una vieja suelta.
SIGLAS_PUBLICAS = {"itcm": "ITCM", "itcg": "ITCG", "itvc": "ITCIS", "itcp": "ITCP"}

# Umbrales de clasificación de estado por cinturón (score 0-10)
# score <= ESTABLE_MAX → "estable" | <= EN_TENSION_MAX → "en_tension" | > EN_TENSION_MAX → "tensionado"
UMBRALES = {
    "ESTABLE_MAX": 3,
    "EN_TENSION_MAX": 6,
}


def estado_de_score(score: float) -> str:
    """Traduce la tensión 0-10 de un cinturón a su estado.

    ÚNICA definición. Antes había tres criterios distintos para lo mismo:
    `generar_informe._estado`, una "réplica" en `publicar._estado`, y adentro de
    `detectar_barbarismo` un tercero —`score >= EN_TENSION_MAX + 1`— que se
    usaba para contar los cinturones de la alerta multicinturón.

    Ese `+1` sólo coincide con `> EN_TENSION_MAX` cuando los scores son enteros,
    y no lo son: tienen un decimal. Entre 6 y 7 quedaba una ZONA MUERTA donde un
    cinturón estaba clasificado "tensionado" y a la vez no contaba para la
    alerta. En agosto de 2026 le pasaba a vida cotidiana, en 6,9: el informe la
    llamaba tensionada y la regla "dos o más señalan inestabilidad" la ignoraba.

    Lo encontró una revisión adversarial del rediseño visual, al intentar
    mostrar en la web si un cinturón contaba para la alerta (ADR-0195).
    """
    if score <= UMBRALES["ESTABLE_MAX"]:
        return "estable"
    if score <= UMBRALES["EN_TENSION_MAX"]:
        return "en_tension"
    return "tensionado"


def es_tensionado(score: float) -> bool:
    """Si este cinturón cuenta para la alerta multicinturón."""
    return estado_de_score(score) == "tensionado"

# Mapping cinturón dominante → barbarismo activo (marco PES de Matus)
BARBARISMO_MAP = {
    "macro": "tecnocrático",
    "politica": "político",
    "gestion": "gerencial",
    "vida_cotidiana": "político",
}

# ── G2: rezago máximo en días por indicador (default: mensual con margen) ────
# Mide el rezago del DATO (`fecha_dato`), no el del fetch: cuántos días puede
# tener el último punto publicado antes de que la card cuente como atrasada.
#
# Vive acá y no en `gate_calidad.py` por el mismo motivo que `DIAS_SIN_FETCH`:
# tiene DOS consumidores —el gate, que reporta la demora, y `publicar.py`, que
# marca `desactualizado` en el snapshot— y una política con dos dueños se
# desincroniza en silencio. Repetir la constante dejaba al snapshot diciendo
# "al día" mientras el gate reportaba demora, o al revés.
MAX_DIAS_DEFAULT = 110
MAX_DIAS = {
    # trimestrales EPH (fecha = inicio del trimestre, publica ~70d después del cierre)
    "informalidad": 280, "subocupacion_demandante": 280,   # ADR-0249: se llamaba `pluriempleo`
    # SIPA: son declaraciones de las empresas que se consolidan y se revisan,
    # con ~3 meses de rezago estructural (ADR-0130). 150 días deja margen sobre
    # ese ritmo sin dejar de avisar si la fuente se muere de verdad.
    "empleo_registrado": 150,
    # fuentes con rezago estructural largo
    # ANUAL: la serie RON de Hacienda es por año calendario ejecutado y el
    # archivo del año nuevo aparece bien entrado el año siguiente. La fecha del
    # dato es el cierre del año de referencia (31-dic), así que el rezago crece
    # todo el año hasta que se publica el archivo siguiente: 560 días cubre ese
    # ciclo completo sin dejar de avisar si la fuente se muere de verdad. Hasta
    # el 29-jul-2026 la card declaraba `date.today()` y este tope no existía
    # porque el indicador se mostraba fresco siempre.
    "iaf_transferencias": 560,
    # ANUALES del bloque judicial (ADR-0168). Sin tope propio, un indicador
    # anual queda marcado como desactualizado siempre, que es exactamente el
    # falso positivo que ADR-0133 separó de una falla de integridad.
    # velocidad_resolucion: el anuario del año N sale bien entrado N+1, y la
    # fecha del dato es el cierre del año de referencia — mismo ciclo que
    # iaf_transferencias.
    "velocidad_resolucion": 560,
    # judicializacion: el punto del año en curso se recalcula en cada corrida y
    # se fecha al 1-ene de ese año, así que el rezago crece hasta 365 días antes
    # de que aparezca el punto siguiente. 430 cubre el ciclo con margen.
    "judicializacion": 430,
    "protocolo_antipiquetes": 430,      # DP publica monitoreos esporádicos
    "litigiosidad_laboral": 220,        # SRT
    "libertad_opcion_salud": 220,       # SSS
    # mensuales con ~2-3 meses de rezago de publicación
    "emae_ia": 140, "iai": 140, "icip": 140, "brecha_salario_cbt": 150,
    # ADR-0218: la SRT publica con ~3 meses de rezago (verificado: en agosto
    # de 2026 el último dato era mayo). El tope de 140 venía del IPI, que es
    # más rápido; con esta fuente dejaría menos de un mes de margen.
    "mortalidad_pymes": 165, "despacho_cemento": 140, "consumo_carne": 140,
    # SIPA publica con el mismo rezago de ~3 meses que la SRT (ADR-0219).
    "trabajo_independiente": 165,
    # DNRPA (ADR-0223). El rezago está MEDIDO sobre el historial de
    # actualizaciones del catálogo, no copiado de ningún documento: el mes M
    # aparece entre el día 1 y el 4 de M+1 (sep-2025 a ago-2026), con un solo
    # caso más tardío, el 13-mar-2026. Es dato registral, no una encuesta.
    # Con esa cadencia la card nunca pasa de ~72 días de antigüedad; 90 es el
    # punto donde una publicación se corrió más allá del mes siguiente entero,
    # o sea un mes salteado, que es justo lo que el tope tiene que agarrar.
    # ADR-0224: el tope pasa al componente que quedó. Es el MISMO número y por
    # la misma medición —los dos registros de la DNRPA publican con la misma
    # cadencia y el colector exige que lleguen al mismo mes—, así que el tope
    # de autos vale para la suma sin recalibrar nada.
    "motorizacion_total": 90,
    # ADR-0225/0256. El default de 110 marcaría atraso todos los meses. El tope
    # sale de MEDIR el calendario del INDEC, no de estimarlo: sobre las 14
    # publicaciones entre julio-2025 y agosto-2026, el mes M sale entre 48 y 57
    # días después de terminado (mediana 53) y las publicaciones se separan
    # entre 23 y 34 días. Como `fecha_dato` es el día 1 del mes de referencia,
    # el último punto nace con 78-86 días y llega como mucho a **116** la
    # víspera de la publicación siguiente. 130 deja margen sobre ese techo
    # medido y sigue agarrando un mes salteado, que lo llevaría a ~146.
    # Bajó de 140 al dejar de encadenar el rezago del espejo de datos.gob.ar:
    # desde ADR-0256 la serie sale de la planilla del propio INDEC.
    "consumo_supermercados": 130,
    "endeudamiento_familiar": 140, "inseguridad": 150,
    # IEF: la serie es mensual, pero el BCRA libera la planilla por lote
    # semestral. 300 días cubre el ciclo sin presentarla como fuente mensual.
    "carga_servicio_deuda_hogares": 300,
    # Trabajo: planilla mensual con 2-3 meses de rezago observado.
    "jornadas_individuales_no_trabajadas_12m": 150,
}


def rezago_maximo_tolerado(indicador: str) -> int:
    """Días de rezago del dato que este indicador puede acumular, o el default."""
    return MAX_DIAS.get(indicador, MAX_DIAS_DEFAULT)


# ── Días tolerados sin un fetch exitoso, por indicador (ADR-0191/0210) ────────
# Mide el rezago del FETCH (`obtenido_en`, que el colector sella sólo cuando la
# fuente contestó), no el del DATO (`fecha_dato`).
#
# Vive acá y no en `gate_calidad.py` porque tiene DOS consumidores —el gate y
# `generar_informe.py`, que arma los `flags` del snapshot— y una política con
# dos dueños se desincroniza. Mismo criterio que los pesos en ADR-0207.
#
# **Una entrada explícita acá declara que el indicador anda por caché a
# propósito**, y por eso no cuenta como carry-forward mientras esté en su
# ventana. Un indicador SIN entrada usa el default y sigue avisando desde el
# primer día: es la diferencia entre "sabemos que este se refresca a mano" y
# "esta fuente se acaba de caer y no nos enteramos". Bajar esa guardia a todos
# habría dejado muda por dos semanas una caída real — que es exactamente cómo
# se perdió `sentimiento_digital` el 9-jul-2026.
DIAS_SIN_FETCH_DEFAULT = 14
DIAS_SIN_FETCH = {
    # SAIJ bloquea por IP el rango de egreso de los runners (403 desde Azure,
    # 200 desde una IP argentina — medido el 12-ago-2026 y re-confirmado el
    # 18-ago contra un runner, donde también fallan los UA de browser: no es
    # cuestión de headers). Hasta que haya un egreso propio el refresco es
    # manual desde Argentina, al ritmo mensual del informe. 45 días deja margen
    # sobre ese ciclo sin volver a dejar que se congele en silencio.
    "judicializacion": 45,
}


def dias_sin_fetch_tolerados(indicador: str) -> int:
    """Ventana declarada para este indicador, o el default."""
    return DIAS_SIN_FETCH.get(indicador, DIAS_SIN_FETCH_DEFAULT)


def cache_es_esperable(indicador: str, dias_sin_fetch: int | None) -> bool:
    """True si servir este indicador desde caché HOY es la política, no una falla.

    Pide las dos cosas: que el indicador tenga tolerancia DECLARADA y que
    todavía esté adentro. Sin `obtenido_en` (`dias_sin_fetch is None`) devuelve
    False — son los manuales y los derivados de series, que no tienen fetch
    propio que medir y no pueden reclamar una ventana que nadie les midió.
    """
    if indicador not in DIAS_SIN_FETCH or dias_sin_fetch is None:
        return False
    return dias_sin_fetch <= DIAS_SIN_FETCH[indicador]
