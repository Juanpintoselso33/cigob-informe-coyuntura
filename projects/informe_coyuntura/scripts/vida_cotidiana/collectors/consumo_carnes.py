"""Consumo per cápita de carnes (vacuna + aviar + porcina) — SAGYP, mes a mes.

ADR-0392: la card y lo que puntúa salen de la MISMA serie, el consumo aparente
por habitante (promedio móvil de 12 meses) que publica la Secretaría de
Agricultura para cada carne. Hasta ADR-0392 la card mostraba el tablero de
consumo y el puntaje salía de la faena del INDEC, porque el tablero es una foto
del mes sin historia (ADR-0217). Las series mensuales de cada área sí la tienen:

| Carne | Fuente | Desde |
|---|---|---|
| Vacuna | «Principales indicadores del sector bovino», tabla «Comercialización carne bovina» (PDF mensual) | ene-2024 en la edición vigente |
| Aviar | «Indicadores de oferta y demanda» del área avícola (XLSX) | 2016 |
| Porcina | «Evolución mensual de los indicadores» del área porcina (PDF) | 2017 |

Las tres usan la población 2022-2040 del INDEC (censo 2022), y su suma reproduce
el total del tablero: julio de 2026, 46,74 + 20,14 + 47,01 contra 46,75 + 20,13
+ 47,06 del tablero (las diferencias son revisiones de la fuente).

El PDF de bovinos trae sólo desde enero de 2024. Lo leído se acumula en
`data/vida/consumo_carnes_sagyp.json` (una revisión de la fuente pisa el mes;
un mes que la edición ya no trae se conserva), y el 4T-2023 de la vacuna, que
es la base del índice, se reconstruye una vez y queda fijo en
`ANCLA_VACUNA_4T2023` (ver su comentario).
"""
import io
import json
import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-Monitor/1.0)"}
HTTP_TIMEOUT = 90

_BASE = "https://www.magyp.gob.ar/sitio/areas"
URL_BOVINOS = (f"{_BASE}/bovinos/informacion_sectorial/_archivos//000030_Indicadores/"
               "000001-%20Indicadores%20bovinos.pdf")
URL_AVIAR = (f"{_BASE}/aves/estadistica/carne/_archivos//000008_Indicadores%20Actuales/"
             "{anio}0000_{year}/000000_Indicadores%20de%20Oferta%20y%20Demanda%202016-{year}.xlsx")
URL_PORCINOS = (f"{_BASE}/porcinos/estadistica/_archivos//000007_Evoluci%C3%B3n%20de%20los%20Indicadores/"
                "000000_Evolucion%20Mensual%20Indicadores.pdf")

STORE = Path(__file__).resolve().parents[3] / "data" / "vida" / "consumo_carnes_sagyp.json"
CARNES = ("vacuna", "aviar", "porcina")

# El 4T-2023 de la vacuna (kg/hab/año, promedio móvil de 12 meses), que la
# edición vigente del PDF de bovinos ya no trae. Diciembre es el anual oficial
# de 2023 con la población del censo 2022 (tablero de consumo 2025: 52,72; el
# del 2024, con la población anterior, decía 52,24). Octubre y noviembre se
# despejan de la identidad del promedio móvil, M(t) − M(t−1) = (x(t) − x(t−12))/12,
# con los mensuales de 2024 de la edición vigente y los de nov/dic-2022 de la
# edición de agosto de 2023, llevados a la población nueva con el cociente
# medio entre las dos ediciones en feb-jul 2023 (1,052; va de 1,044 a 1,062).
# Con el cociente en cualquiera de los dos extremos la base del índice se
# mueve ±0,04 kg sobre 53,49. Ver ADR-0392.
ANCLA_VACUNA_4T2023 = {"2023-10": 53.80, "2023-11": 53.94, "2023-12": 52.72}

MESES_LARGOS = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5,
                "junio": 6, "julio": 7, "agosto": 8, "septiembre": 9,
                "octubre": 10, "noviembre": 11, "diciembre": 12}
MESES_CORTOS = {k[:3]: v for k, v in MESES_LARGOS.items()}
_DECIMAL = re.compile(r"\b\d{1,3},\d{2}\b")


def _num(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _texto_pdf(pdf_bytes: bytes) -> str:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def _filas_por_mes(lineas, meses: dict, columna: int) -> dict:
    """{AAAA-MM: valor} recorriendo una tabla con renglones de año y de mes.

    Un renglón que EMPIEZA con un año abre ese año; uno que empieza con un mes
    toma el `columna`-ésimo número con dos decimales del renglón (los
    kg/hab/año son los únicos números con coma decimal en estas tablas)."""
    out, anio = {}, None
    for linea in lineas:
        partes = linea.strip().split()
        if not partes:
            continue
        if re.fullmatch(r"20\d{2}", partes[0]):
            anio = int(partes[0])
            continue
        mes = meses.get(partes[0].lower().rstrip("."))
        if anio is None or mes is None:
            continue
        decimales = _DECIMAL.findall(linea)
        if len(decimales) < 2:
            continue      # mes sin dato todavía
        out[f"{anio}-{mes:02d}"] = _num(decimales[columna])
    return out


def parsear_bovinos(pdf_bytes: bytes) -> dict:
    """Promedio móvil de la vacuna, de la tabla «Comercialización carne bovina».

    Cada mes trae: consumo aparente (miles de t), per cápita del mes
    anualizado, per cápita promedio móvil, y exportaciones. El móvil es el
    SEGUNDO número con coma decimal del renglón."""
    texto = _texto_pdf(pdf_bytes)
    i = texto.find("COMERCIALIZACION")
    if i < 0:
        raise ValueError("bovinos: no está la tabla de comercialización")
    fin = texto.find("Variación", i)
    out = _filas_por_mes(texto[i:fin if fin > 0 else None].splitlines(), MESES_LARGOS, 1)
    if len(out) < 12:
        raise ValueError(f"bovinos: sólo {len(out)} meses en la tabla — cambió el formato")
    return out


def parsear_porcinos(pdf_bytes: bytes) -> dict:
    """Promedio móvil de la porcina: el ÚLTIMO número con coma decimal del renglón
    (antes va el per cápita del mes)."""
    out = _filas_por_mes(_texto_pdf(pdf_bytes).splitlines(), MESES_CORTOS, -1)
    if len(out) < 24:
        raise ValueError(f"porcinos: sólo {len(out)} meses — cambió el formato")
    return out


def parsear_aviar(xlsx_bytes: bytes) -> dict:
    """Promedio móvil de la aviar: columna «Consumo Aparente per capita promedio
    móvil» de la planilla de oferta y demanda (renglón de año, luego los meses)."""
    import openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_bytes), data_only=True, read_only=True)
    ws = wb.worksheets[0]
    col = None
    out, anio = {}, None
    for fila in ws.iter_rows(values_only=True):
        if col is None:
            for j, celda in enumerate(fila):
                if isinstance(celda, str) and "promedio" in celda.lower() and "per capita" in celda.lower():
                    col = j
            continue
        rotulo = fila[0]
        if isinstance(rotulo, (int, float)) or (isinstance(rotulo, str) and re.fullmatch(r"20\d{2}", rotulo.strip())):
            anio = int(rotulo)
            continue
        mes = MESES_LARGOS.get(str(rotulo or "").strip().lower())
        if anio and mes and isinstance(fila[col], (int, float)):
            out[f"{anio}-{mes:02d}"] = round(float(fila[col]), 2)
    if col is None or len(out) < 24:
        raise ValueError(f"aviar: planilla irreconocible ({len(out)} meses)")
    return out


def _bajar(url: str) -> bytes:
    r = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT, verify=False)
    r.raise_for_status()
    return r.content


def _bajar_aviar() -> bytes:
    """La planilla vive en una carpeta por año; al cambiar de año puede tardar en
    aparecer la nueva, así que se prueba el año en curso y el anterior."""
    from datetime import date
    ultimo = None
    for year in (date.today().year, date.today().year - 1):
        try:
            return _bajar(URL_AVIAR.format(anio=str(year)[2:], year=year))
        except requests.RequestException as e:
            ultimo = e
    raise ultimo


def cargar_store() -> dict:
    try:
        d = json.loads(STORE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        d = {}
    return {c: dict(d.get(c) or {}) for c in CARNES}


def actualizar_store() -> dict:
    """Baja las tres fuentes, las mezcla con lo acumulado y lo guarda.

    Una fuente caída no borra nada: su carne queda con lo acumulado y el error
    se registra. Si fallan las tres, se levanta la excepción."""
    store = cargar_store()
    errores = {}
    for carne, bajar, parsear in (
            ("vacuna", lambda: _bajar(URL_BOVINOS), parsear_bovinos),
            ("aviar", _bajar_aviar, parsear_aviar),
            ("porcina", lambda: _bajar(URL_PORCINOS), parsear_porcinos)):
        try:
            store[carne].update(parsear(bajar()))
        except Exception as e:      # noqa: BLE001 — una fuente no tumba a las otras
            errores[carne] = str(e)[:200]
            logger.warning("consumo de carnes %s: %s", carne, e)
    if len(errores) == len(CARNES):
        raise RuntimeError(f"consumo de carnes: fallaron las tres fuentes {errores}")
    STORE.parent.mkdir(parents=True, exist_ok=True)
    STORE.write_text(json.dumps(
        {"_meta": {"fuente": "SAGYP — per cápita promedio móvil 12m por carne (ADR-0392)",
                   "errores_ultima_lectura": errores},
         **{c: dict(sorted(store[c].items())) for c in CARNES}},
        indent=1, ensure_ascii=False), encoding="utf-8")
    return store


def series_por_carne(store: dict | None = None) -> dict:
    """{carne: {AAAA-MM: kg/hab/año}} con el ancla del 4T-2023 de la vacuna
    debajo de lo leído (un dato real de la fuente gana sobre el ancla)."""
    store = store if store is not None else cargar_store()
    out = {c: dict(store.get(c) or {}) for c in CARNES}
    out["vacuna"] = {**ANCLA_VACUNA_4T2023, **out["vacuna"]}
    return out


def registro_del_mes(series: dict) -> dict:
    """El registro de la card: el último mes con las tres carnes, y la variación
    interanual de cada una contra el mismo mes del año anterior."""
    comunes = sorted(set.intersection(*(set(series[c]) for c in CARNES)))
    if not comunes:
        raise ValueError("consumo de carnes: no hay un mes con las tres carnes")
    mes = comunes[-1]
    anio, m = mes.split("-")
    mes_ant = f"{int(anio) - 1}-{m}"
    actual = {c: series[c][mes] for c in CARNES}
    actual["total"] = round(sum(actual.values()), 2)

    def var(cat):
        if cat == "total":
            if all(mes_ant in series[c] for c in CARNES):
                ant = sum(series[c][mes_ant] for c in CARNES)
                return round((actual["total"] / ant - 1) * 100, 2)
            return None
        ant = series[cat].get(mes_ant)
        return round((actual[cat] / ant - 1) * 100, 2) if ant else None

    return {
        "mes": mes,
        "total": actual["total"],
        "vacuna": round(actual["vacuna"], 2),
        "aviar": round(actual["aviar"], 2),
        "porcina": round(actual["porcina"], 2),
        "ratio_bovina": round(actual["vacuna"] / actual["total"] * 100, 2),
        "variaciones": {c: var(c) for c in ("vacuna", "aviar", "porcina", "total")},
    }


def fetch_consumo_carnes() -> dict:
    return registro_del_mes(series_por_carne(actualizar_store()))
