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
