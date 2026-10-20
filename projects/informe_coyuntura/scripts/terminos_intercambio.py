"""Tipo de cambio real × términos del intercambio (ADR-0360).

La dimensión competitividad externa del ITCM colgaba de un solo dato, el tipo de
cambio real multilateral del BCRA: dice si el peso está caro o barato, pero no
si ese nivel se sostiene. Los términos del intercambio del INDEC (precios de
exportación sobre precios de importación) aportan esa segunda lectura: un peso
apreciado con buenos precios de exportación no es lo mismo que el mismo peso
con precios en caída.

## Cómo se convierte en un solo número

Igual que el desequilibrio monetario (desequilibrio_monetario.py): cada
componente se lleva a una posición 0-1 y el puntaje sale de interpolar
BILINEALMENTE entre las cuatro esquinas de la matriz. No se promedian.

                       | términos altos (b=1) | términos bajos (b=0)
    -------------------+----------------------+---------------------
    peso competitivo   |   85 · verde         |   50 · amarillo
    peso apreciado     |   30 · naranja       |   10 · rojo

La matriz es ASIMÉTRICA a propósito, y a diferencia de la del desequilibrio
(ADR-0257) acá el orden de las cruzadas tiene fundamento: con el peso
competitivo el ajuste ya ocurrió y la posición se defiende aunque los precios
no ayuden; un peso apreciado sostenido por buenos precios depende de una
variable externa y volátil.

El indicador publica el PUNTAJE 0-100 directamente (las anclas del ITCM son la
identidad), así que no hay una segunda escala que se pueda desincronizar.
"""
import parametrica

# ── Fuente ───────────────────────────────────────────────────────────────────
# INDEC, índices de precios y cantidades del comercio exterior: términos del
# intercambio, serie trimestral, base 2004 = 100, publicada en la API de series
# de datos.gob.ar. Cada fila es un trimestre, fechado en su primer mes.
SERIE_TI_ID = "82.2_ITI_2004_T_27"
SERIES_API = "https://apis.datos.gob.ar/series/api/series/"

# ── Posición del tipo de cambio real (a) ─────────────────────────────────────
# Sale de los umbrales institucionales que el indicador ya tenía (BANDAS_TCR,
# abajo), no de una ventana estadística: puntaje 10 (≤75, atraso severo) es
# a = 0 y puntaje 100 (≥110, competitivo) es a = 1. Así no depende del punto de
# arranque de ninguna ventana —diciembre de 2023 fue el pico de la devaluación
# y la habría vuelto la referencia de «competitivo»—.
INF = float("inf")
# ITCRM oficial del BCRA (base 17-dic-2015=100). Apreciación real = pérdida de
# competitividad. Calibradas con la historia 1997-2026 (p10≈75, p25≈87,
# mediana≈106): >110 competitivo · 95-110 cómodo (~nivel 2015) · 85-95
# apreciación moderada · 75-85 apreciación marcada · ≤75 atraso severo.
# Eran las bandas del tcrm en BANDAS_ITCM hasta ADR-0360.
BANDAS_TCR = [
    (110.0, INF, 100), (95.0, 110.0, 80), (85.0, 95.0, 60), (75.0, 85.0, 35), (-INF, 75.0, 10),
]
PUNTAJE_TCR_MIN = 10.0
PUNTAJE_TCR_MAX = 100.0

# ── Posición de los términos del intercambio (b) ─────────────────────────────
# Percentiles 0/25/50/75/100 de la serie desde el trimestre que contiene a
# diciembre de 2023 (4T-2023) hasta el último publicado al calibrar (2T-2026):
# 11 trimestres. CONGELADOS, como en desequilibrio_monetario.py: si el corte
# se moviera con el último dato, el puntaje de un mes dejaría de ser
# reproducible. La ventana es corta y los cortes se revisan cuando crezca.
POSICIONES = (0.0, 0.25, 0.50, 0.75, 1.0)
CORTES_TI = (129.7, 138.1, 140.4, 143.63, 148.15)
VENTANA_TI = "4T-2023 / 2T-2026"

# ── Esquinas de la matriz (puntaje 0-100) ────────────────────────────────────
PUNTAJE_COMPETITIVO_TI_ALTO = 85.0
PUNTAJE_COMPETITIVO_TI_BAJO = 50.0
PUNTAJE_APRECIADO_TI_ALTO = 30.0
PUNTAJE_APRECIADO_TI_BAJO = 10.0

# ── Frecuencia ───────────────────────────────────────────────────────────────
# El INDEC publica el trimestre unos dos meses y medio después de cerrarlo
# (el 2T sale a mediados de septiembre). Para la serie histórica, un trimestre
# cuenta como publicado a partir del tercer mes posterior a su cierre: el 2T
# (abril-junio) entra en septiembre. Cada mes usa el último trimestre publicado,
# sin imputar ni anticipar con otra serie.
MESES_REZAGO_PUBLICACION = 3
# El trimestre vigente normal va de 5 a 7 meses detrás del mes que puntúa (el
# 2T, que empieza en abril, se usa de septiembre a noviembre). 9 tolera que el
# INDEC se atrase un trimestre; más que eso es una serie congelada y ese mes no
# se calcula — ni en la card ni en la serie histórica.
MAX_REZAGO_TI_MESES = 9

# El compuesto arranca con el período que cubre el Monitor.
MES_INICIO = "2023-12"

CELDAS = {
    (True, True): "competitivo_ti_altos",
    (True, False): "competitivo_ti_bajos",
    (False, True): "apreciado_ti_altos",
    (False, False): "apreciado_ti_bajos",
}


def _sumar_meses(mes: str, n: int) -> str:
    anio, m = map(int, mes[:7].split("-"))
    total = anio * 12 + (m - 1) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def etiqueta_trimestre(mes_inicio: str) -> str:
    """'2026-04' → '2T-2026'."""
    anio, m = map(int, mes_inicio[:7].split("-"))
    return f"{(m - 1) // 3 + 1}T-{anio}"


def posicion_tcr(tcrm: float) -> float:
    """Posición 0-1 del tipo de cambio real según su puntaje institucional."""
    puntaje = parametrica.puntaje_interpolado(float(tcrm), BANDAS_TCR)
    a = (puntaje - PUNTAJE_TCR_MIN) / (PUNTAJE_TCR_MAX - PUNTAJE_TCR_MIN)
    return min(1.0, max(0.0, a))


def posicion_ti(valor: float, cortes: tuple = CORTES_TI) -> float:
    """Posición 0-1 del valor entre los percentiles `cortes`, saturando afuera."""
    valor = float(valor)
    if valor <= cortes[0]:
        return POSICIONES[0]
    if valor >= cortes[-1]:
        return POSICIONES[-1]
    for (x0, p0), (x1, p1) in zip(zip(cortes, POSICIONES),
                                  zip(cortes[1:], POSICIONES[1:])):
        if x0 <= valor <= x1:
            if x1 == x0:
                return p1
            return p0 + (p1 - p0) * (valor - x0) / (x1 - x0)
    return POSICIONES[-1]


def puntaje_matriz(a: float, b: float) -> float:
    """Interpolación bilineal entre las cuatro esquinas (ADR-0360)."""
    a, b = float(a), float(b)
    return (
        (1 - a) * (1 - b) * PUNTAJE_APRECIADO_TI_BAJO
        + a * (1 - b) * PUNTAJE_COMPETITIVO_TI_BAJO
        + (1 - a) * b * PUNTAJE_APRECIADO_TI_ALTO
        + a * b * PUNTAJE_COMPETITIVO_TI_ALTO
    )


def celda(a: float, b: float) -> str:
    """Cuadrante de la matriz donde cae el mes, para la lectura cualitativa."""
    return CELDAS[(a >= 0.5, b >= 0.5)]


def trimestre_vigente(mes: str, trimestres: dict) -> str | None:
    """Primer mes del último trimestre publicado en `mes` (o None si ninguno).

    Un trimestre que empieza en q cierra en q+2 y cuenta como publicado desde
    q+2+MESES_REZAGO_PUBLICACION. Si el INDEC todavía no lo subió, se usa el
    anterior: en `trimestres` sólo está lo que la fuente tiene.
    """
    candidatos = [
        q for q in trimestres
        if _sumar_meses(q, 2 + MESES_REZAGO_PUBLICACION) <= mes[:7]
    ]
    return max(candidatos) if candidatos else None


def _meses_entre(desde: str, hasta: str) -> int:
    a0, m0 = map(int, desde[:7].split("-"))
    a1, m1 = map(int, hasta[:7].split("-"))
    return (a1 - a0) * 12 + (m1 - m0)


def construir_serie(*, tcrm: dict, terminos: dict) -> list:
    """Serie mensual del compuesto. `tcrm` = {YYYY-MM: ITCRM}; `terminos` =
    {YYYY-MM (primer mes del trimestre): índice}. Un mes entra sólo si tiene
    tipo de cambio real y un trimestre publicado a no más de
    MAX_REZAGO_TI_MESES; no se imputa nada."""
    serie = []
    for mes in sorted(m for m in tcrm if m >= MES_INICIO):
        q = trimestre_vigente(mes, terminos)
        if q is None or _meses_entre(q, mes) > MAX_REZAGO_TI_MESES:
            continue
        a = posicion_tcr(tcrm[mes])
        b = posicion_ti(terminos[q])
        puntaje = puntaje_matriz(a, b)
        serie.append({
            "mes": mes,
            "puntaje": round(puntaje, 1),
            "tcrm": round(float(tcrm[mes]), 2),
            "terminos_intercambio": round(float(terminos[q]), 2),
            "trimestre_ti": etiqueta_trimestre(q),
            "mes_trimestre_ti": q,
            "posicion_tcr": round(a, 4),
            "posicion_ti": round(b, 4),
            "celda": celda(a, b),
        })
    return serie


def parsear_terminos(data: list) -> dict:
    """Filas [[YYYY-MM-DD, valor], ...] de la API → {YYYY-MM: valor}."""
    out = {}
    for fecha, valor in data:
        if valor is None:
            continue
        out[str(fecha)[:7]] = round(float(valor), 4)
    if not out:
        raise ValueError("términos del intercambio: la API no devolvió datos")
    return dict(sorted(out.items()))


def fetch_terminos() -> dict:
    import datos_gob
    params = {"ids": SERIE_TI_ID, "format": "json", "limit": 1000,
              "start_date": "2004-01-01"}
    r = datos_gob.get(SERIES_API, params=params,
                      headers={"User-Agent": "CIGOB-InformeCoyuntura/1.0"},
                      timeout=30)
    r.raise_for_status()
    return parsear_terminos(r.json()["data"])
