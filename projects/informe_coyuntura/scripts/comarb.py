"""Recaudación de los sistemas COMARB (Comisión Arbitral del Convenio Multilateral).

Es el Impuesto sobre los Ingresos Brutos que liquidan los contribuyentes de
Convenio Multilateral más los regímenes de retención y percepción provinciales:
SIFERE (liquidación de IIBB), SIRCREB (acreditaciones bancarias), SIRCAR
(agentes de recaudación), SIRTAC (tarjetas), SIRPEI (percepciones en
importaciones) y SIRCUPA (cuentas de pago).

**Qué NO es**: recaudación provincial total. Cada provincia además recauda de
sus contribuyentes locales por fuera del Convenio Multilateral, y eso no pasa
por acá. Es una porción grande y homogénea de la base imponible provincial, no
su universo — hay que declararlo donde se publique.

Fuente: gacetilla mensual en PDF publicada en ca.gob.ar (el dominio viejo
comarb.gob.ar redirige ahí).

Dos cosas que este módulo resuelve y conviene no "simplificar":

1. **Los nombres de archivo NO siguen un patrón estable.** Conviven
   `..._01_Ene_2023.pdf`, `..._04-04-2024.pdf`, `..._Recaudación_...` con
   tilde, `..._10_Oct 2025.pdf` con espacio y variantes de mayúsculas.
   Construir la URL a partir del período pierde meses en silencio, así que se
   scrapea el listado.

2. **El orden de columnas del PDF cambia en enero.** Los meses con acumulado
   traen `$ 2.181.517 29 % TOTAL`; enero, que no tiene columna ENE-XXX, trae
   `$ 2.118.722 TOTAL 38%`. Se aceptan los dos órdenes.

Además reconstruye 2022, que la Comisión no publica como gacetilla: cada
gacetilla de 2023 informa su propia variación interanual, así que el nivel del
año anterior sale de `nivel / (1 + var)`. Verificado por dos caminos
independientes: la suma de los 12 meses reconstruidos da 2.009.661 millones y el
acumulado ENE-DIC deducido del acumulado 2023 da 2.009.671 — 0,00% de desvío,
sólo redondeo. Sin ese año la variación interanual del combinado no podría
empezar antes de ene-2024 y no cubriría dic-2023, que es el piso de backfill
del proyecto.
"""
import io
import json
import re
import time
import urllib.parse
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "macro" / "comarb_recaudacion.json"

LISTADO = "https://www.ca.gob.ar/gacetillas"
BASE = "https://www.ca.gob.ar"
SISTEMAS = ("SIFERE", "SIRCAR", "SIRPEI", "SIRCREB", "SIRCUPA", "SIRTAC")
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; CIGOB-informe/1.0)"}
TIMEOUT = 90

_MES = {m: i for i, m in enumerate(
    ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"], 1)}


def _monto(s: str) -> float:
    return float(s.replace(".", ""))


def _pct(s: str) -> float:
    return float(s.replace(".", "").replace(",", "."))


def _periodo(href: str) -> str | None:
    """YYYY-MM del archivo, tolerando las variantes de nombre."""
    nom = urllib.parse.unquote(href.split("/")[-1])
    carpeta = href.split("/")[-2] if "/" in href else ""
    anio = re.search(r"(20\d{2})", carpeta) or re.search(r"(20\d{2})", nom)
    m = re.search(r"[_\-](\d{2})[_\- ]", nom)
    mes = int(m.group(1)) if m else None
    if not mes:
        mm = re.search(r"[_\-]([a-zA-Záéíó]{3})[a-zá]*[_\- ]", nom)
        mes = _MES.get(mm.group(1)[:3].lower()) if mm else None
    return f"{anio.group(1)}-{mes:02d}" if anio and mes else None


def _busca(txt: str, rotulo: str):
    """(nivel, variación i.a.) del rótulo, en los dos órdenes de columna."""
    for pat in (r"\$\s*([\d.]+)\s+(-?[\d.,]+)\s*%\s*" + rotulo,
                r"\$\s*([\d.]+)\s*" + rotulo + r"\s+(-?[\d.,]+)\s*%"):
        m = re.search(pat, txt)
        if m:
            return _monto(m.group(1)), _pct(m.group(2))
    return None, None


def _leer_pdf(blob: bytes) -> dict | None:
    import pdfplumber
    with pdfplumber.open(io.BytesIO(blob)) as pdf:
        txt = "\n".join((p.extract_text() or "") for p in pdf.pages)
    total, var = _busca(txt, "TOTAL")
    if total is None:
        return None
    reg = {"total": total, "var_ia_publicada": var}
    for s in SISTEMAS:
        niv, _ = _busca(txt, s)
        if niv is not None:
            reg[s.lower()] = niv
    # Control de la extracción: los seis sistemas suman el total. Da 0,00% en
    # los 42 meses publicados, así que un desvío es señal de layout cambiado.
    suma = sum(v for k, v in reg.items() if k not in ("total", "var_ia_publicada"))
    reg["desvio_suma_pct"] = round(100 * (suma / total - 1), 3) if total else None
    return reg


def _cache_leer() -> dict:
    try:
        return json.loads(CACHE.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {"_meta": {}, "gacetillas": {}, "reconstruido_2022": {}}


def _cache_escribir(d: dict) -> None:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def actualizar(session: requests.Session | None = None, verbose: bool = False) -> dict:
    """Descarga las gacetillas que falten y devuelve el store completo.

    Sólo baja los períodos ausentes del caché: cada PDF pesa ~1 MB y son 42, así
    que re-bajar todo en cada corrida del cron sería ~40 MB por nada.
    """
    ses = session or requests.Session()
    ses.headers.update(HEADERS)
    store = _cache_leer()
    gacetillas = store.setdefault("gacetillas", {})

    html = ses.get(LISTADO, timeout=TIMEOUT, verify=False).text
    hrefs = sorted(set(re.findall(r'href="([^"]*[Gg]acetilla[^"]*\.pdf)"', html)))
    nuevos = 0
    for href in hrefs:
        per = _periodo(href)
        if not per or per in gacetillas:
            continue
        url = urllib.parse.urljoin(BASE, urllib.parse.quote(href, safe=":/?&=%"))
        try:
            reg = _leer_pdf(ses.get(url, timeout=TIMEOUT, verify=False).content)
        except Exception as e:                                    # noqa: BLE001
            if verbose:
                print(f"  [WARN] COMARB {per}: {type(e).__name__}: {e}")
            continue
        if reg:
            reg["archivo"] = href.split("/")[-1]
            gacetillas[per] = reg
            nuevos += 1
            if verbose:
                print(f"  [OK] COMARB {per}: ${reg['total']:,.0f} M "
                      f"(desvío suma {reg['desvio_suma_pct']}%)")
        time.sleep(0.2)

    # 2022 desde la variación publicada en las gacetillas de 2023
    rec = store.setdefault("reconstruido_2022", {})
    for mes in range(1, 13):
        per23, per22 = f"2023-{mes:02d}", f"2022-{mes:02d}"
        g = gacetillas.get(per23)
        if per22 in rec or not g or g.get("var_ia_publicada") is None:
            continue
        rec[per22] = round(g["total"] / (1 + g["var_ia_publicada"] / 100), 1)

    store["_meta"] = {
        "descripcion": "Recaudación mensual de los sistemas COMARB (IIBB Convenio "
                       "Multilateral + regímenes de retención/percepción), en millones "
                       "de pesos nominales. NO es recaudación provincial total.",
        "fuente": LISTADO,
        "gacetillas": len(gacetillas),
        "reconstruidos_2022": len(rec),
        "nuevos_en_esta_corrida": nuevos,
    }
    _cache_escribir(store)
    return store


def niveles(session: requests.Session | None = None, verbose: bool = False) -> dict:
    """{YYYY-MM: recaudación nominal en millones de $}, 2022 incluido."""
    store = actualizar(session, verbose)
    out = {k: float(v) for k, v in (store.get("reconstruido_2022") or {}).items()}
    out.update({k: float(v["total"]) for k, v in (store.get("gacetillas") or {}).items()})
    return out


def niveles_cacheados() -> dict:
    """Igual que `niveles()` pero SIN red: para tests y para el cálculo de la
    card, que no debe volver a bajar 42 PDFs."""
    store = _cache_leer()
    out = {k: float(v) for k, v in (store.get("reconstruido_2022") or {}).items()}
    out.update({k: float(v["total"]) for k, v in (store.get("gacetillas") or {}).items()})
    return out


BASE_TRIM = ("2023-10", "2023-11", "2023-12")   # 4T-2023, misma base que el ITVC
VENTANA_MINIMA = 36                             # meses para estimar 12 factores
# Ventana única para la card y para la serie. NO cambiar en un solo lado: los
# factores estacionales se estiman sobre la muestra, así que dos ventanas
# distintas dan dos series distintas y el gate G3 (card ≠ serie) falla.
LIMITE_MESES = 80


def base_imponible_real_sa(nacional: dict, ipc: dict) -> dict:
    """Base imponible REAL desestacionalizada, 100 = promedio del 4T-2023.

    Nacional (DGI) + provincial (sistemas COMARB) sumados en NIVEL, deflactados
    por IPC y desestacionalizados. Es el reemplazo de la variación interanual que
    usaba el indicador hasta el 29-jul-2026, y el motivo del cambio es que
    teniendo el dato mensual la interanual desperdicia resolución: compara contra
    un mes de hace un año en vez de decir cuánto de la base real de la transición
    queda hoy. Con el dato de junio de 2026: la interanual informaba +3,3%
    («creciendo») contra un 2025 deprimido, mientras el nivel dice 88,2, o sea
    11,8% POR DEBAJO de la transición. Las dos son ciertas; para un índice de
    tensión la segunda es la que informa.

    Desestacionalización por cociente sobre media móvil centrada de 12 meses
    (ratio-to-moving-average, 2x12), promediando los factores por mes calendario
    y normalizándolos a promedio 1 para no inventar nivel. Hace falta: el nivel
    real crudo tiene 30,5 puntos de amplitud entre el mes calendario más alto y
    el más bajo —mayo 1,182 y junio 1,119 por vencimientos y aguinaldo, marzo
    0,861— y sin corregir eso el indicador mediría el calendario tributario. Ya
    corregido, la estacionalidad residual baja a 3,1 puntos.

    Dos propiedades que van declaradas en la ficha, no escondidas:
      · es más NERVIOSA que la interanual (junio 2026 cae 9,5 puntos contra mayo);
        con 3-4 observaciones por mes calendario un mes todavía mueve su factor;
      · REVISA el pasado: los factores se re-estiman al acumular meses, así que
        puntos anteriores pueden cambiar algo.

    Los dos callers —la card en macro.py y la serie en descargar_series.py— tienen
    que pasar la MISMA ventana de meses: los factores estacionales dependen de la
    muestra, así que ventanas distintas darían números distintos y G3 fallaría.
    Por eso ambos usan `LIMITE_MESES`.

    [[YYYY-MM: índice]] — vacío si no hay ventana suficiente o falta la base.
    """
    prov = niveles_cacheados()
    comb = {k: nacional[k] + prov[k]
            for k in sorted(set(nacional) & set(prov) & set(ipc))
            if nacional[k] and prov[k]}
    if len(comb) < VENTANA_MINIMA or not all(m in comb for m in BASE_TRIM):
        return {}

    ipc_ancla = ipc[max(comb)]
    real = {k: v * ipc_ancla / ipc[k] for k, v in comb.items()}

    # tendencia: media móvil centrada 2x12
    ks = sorted(real)
    tendencia = {}
    for i in range(6, len(ks) - 6):
        a = sum(real[x] for x in ks[i - 6:i + 6]) / 12
        b = sum(real[x] for x in ks[i - 5:i + 7]) / 12
        tendencia[ks[i]] = (a + b) / 2
    if not tendencia:
        return {}

    brutos: dict[str, list] = {}
    for k, t in tendencia.items():
        if t:
            brutos.setdefault(k[5:7], []).append(real[k] / t)
    if len(brutos) < 12:                       # sin los 12 meses no se corrige nada
        return {}
    factor = {m: sum(v) / len(v) for m, v in brutos.items()}
    promedio = sum(factor.values()) / len(factor)
    factor = {m: f / promedio for m, f in factor.items()}

    sa = {k: v / factor[k[5:7]] for k, v in real.items()}
    base = sum(sa[m] for m in BASE_TRIM) / len(BASE_TRIM)
    return {k: round(100 * v / base, 1) for k, v in sa.items()} if base else {}


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()
    s = niveles(verbose=True)
    print(f"\n[OK] comarb: {len(s)} meses  ({min(s)} → {max(s)})")
