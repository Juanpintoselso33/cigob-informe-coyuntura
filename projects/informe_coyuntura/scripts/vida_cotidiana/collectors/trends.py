"""
Colector Google Trends — sentimiento / interes digital en Argentina
Usa pytrends (no requiere API key).
IMPORTANTE: urllib3 v2 rompe pytrends — monkey-patch aplicado aqui.
Rate limits: Google bloquea requests frecuentes. Aceptar fallas silenciosas.
Frecuencia: tiempo real (promedio 7-90 dias segun escala elegida).
"""
import json
import logging
import time
from datetime import datetime
from pathlib import Path

from config import (
    TRENDS_KEYWORDS, TRENDS_GEO,
    TRENDS_VENTANA_DESDE, TRENDS_BASE_MESES, TRENDS_MIN_MESES,
    MIGRACION_TANDA_INTENCION, MIGRACION_TANDA_CIUDADANIAS,
    MIGRACION_TANDA_TRABAJO_VISAS, MIGRACION_TANDA_DESTINOS,
    MIGRACION_TANDA_DIAGNOSTICO, MIGRACION_CATEGORIA_EMPLEO,
)

logger = logging.getLogger(__name__)

# Store del sentimiento digital: lo comparten el colector (que arma la card) y
# descargar_series.py (que arma la serie publicada). Fuente UNICA, como el de
# intencion migratoria — si cada uno consultara Trends por su cuenta, la card y
# la serie saldrian de corridas distintas y ademas se duplicarian los pedidos
# contra una fuente con rate limit.
SENTIMIENTO_STORE = (Path(__file__).resolve().parents[3]
                     / "data" / "vida" / "sentimiento_serie.json")

# Marca de formato del store. El de antes de ADR-0222 guardaba en `mensual` el
# promedio CRUDO de un payload compartido (interes 0-100); el de ahora guarda un
# INDICE base 100 = 4T-2023. Son numeros parecidos y unidades distintas, asi que
# un store viejo leido como nuevo publicaria una escala por otra sin que falle
# nada. Sin esta marca no hay forma de distinguirlos mirando el archivo.
SENTIMIENTO_ESQUEMA = "adr-0222"


def _patch_urllib3():
    """
    pytrends usa Retry(method_whitelist=...) que fue renombrado a allowed_methods en urllib3 v2.
    Patch aplicado antes de importar pytrends para evitar TypeError en runtime.
    """
    try:
        import urllib3.util.retry as _retry_mod
        retry_cls = _retry_mod.Retry
        if not hasattr(retry_cls, "_default_allowed_methods_compat_applied"):
            _orig_init = retry_cls.__init__

            def _patched_init(self, *args, **kwargs):
                if "method_whitelist" in kwargs:
                    kwargs.setdefault("allowed_methods", kwargs.pop("method_whitelist"))
                _orig_init(self, *args, **kwargs)

            retry_cls.__init__ = _patched_init
            retry_cls._default_allowed_methods_compat_applied = True
    except Exception as e:
        logger.debug("urllib3 patch SKIP: %s", e)


def _mensual_de_df(df, kw: str, hoy: datetime) -> dict:
    """{YYYY-MM: interes} de UN termino, sin el mes en curso (incompleto)."""
    if df is None or df.empty or kw not in df.columns:
        return {}
    serie = df[kw]
    mensual = {}
    for d, v in serie.groupby(serie.index.strftime("%Y-%m")).mean().items():
        if v > 0 and d < hoy.strftime("%Y-%m"):
            mensual[d] = round(float(v), 1)
    return mensual


def indice_de_termino(mensual: dict) -> dict:
    """Indice base 100 = 4T-2023 de UN termino, rebaseado DENTRO de su consulta.

    Acá es donde muere el problema de escalas. Trends devuelve `c * real(t)`,
    con `c` un escalar propio de cada consulta (el maximo del payload vale 100).
    Al dividir por el promedio del 4T-2023 de la MISMA consulta, `c` se cancela
    y queda el cociente real. Por eso seis consultas distintas se pueden
    promediar sin ancla ni empalme, y por eso un termino que se pudo refrescar
    hoy convive con otro que quedo de una corrida vieja: cada uno es adimensional.
    Verificado (20-ago-2026) contra el mismo termino en payloads distintos: el
    cociente entre las dos lecturas es constante (CV 0,0% en `trabajo` y `dolar`,
    0,8% en `precios`) y el indice B100 coincide hasta el decimo.
    """
    base = [mensual[m] for m in TRENDS_BASE_MESES if mensual.get(m)]
    if len(base) < len(TRENDS_BASE_MESES):
        return {}
    b = sum(base) / len(base)
    return {m: round(v / b * 100.0, 1) for m, v in mensual.items()} if b else {}


def compuesto_sentimiento(store: dict) -> dict:
    """Canasta mensual: promedio SIMPLE de los indices por termino (ADR-0222).

    Peso igual y explicito, 1/N por termino. Solo se emiten los meses en los que
    estan LOS N terminos: si un mes se calculara con los que haya, la canasta
    cambiaria de composicion mes a mes y los saltos serian de composicion, no de
    busquedas.
    """
    if store.get("_meta", {}).get("esquema") != SENTIMIENTO_ESQUEMA:
        return {}
    indices = {}
    for kw in TRENDS_KEYWORDS:
        idx = indice_de_termino((store.get("terminos", {}).get(kw) or {}).get("mensual") or {})
        if not idx:
            return {}                       # falta un termino → no hay canasta
        indices[kw] = idx
    meses = set.intersection(*(set(v) for v in indices.values()))
    return {m: round(sum(indices[kw][m] for kw in TRENDS_KEYWORDS) / len(TRENDS_KEYWORDS), 1)
            for m in sorted(meses)}


def fetch_sentimiento_store(store_path: Path | None = None) -> dict:
    """Store por termino del sentimiento digital (ADR-0034 + ADR-0222).

    Una consulta por termino sobre la ventana fija 2021→hoy. Cada termino se
    reemplaza ENTERO cuando su propia descarga es sana (>= TRENDS_MIN_MESES
    meses y los tres meses de la base); el que falla conserva su serie previa.
    Eso es nuevo y lo habilita el rebase por termino: con la canasta cruda de
    antes, mezclar terminos de corridas distintas mezclaba escalas y por eso el
    reemplazo tenia que ser todo-o-nada.

    Idempotente dentro del dia: un termino ya refrescado hoy no se vuelve a
    pedir, asi el colector (card) y descargar_series.py (serie) comparten los
    seis pedidos en vez de gastar doce contra una fuente con rate limit.
    """
    # Se resuelve acá y no como default del parámetro: un default se liga al
    # definir la función y deja de mirar el módulo, con lo que la ruta se vuelve
    # imposible de sustituir en un test sin tocar el disco de verdad.
    store_path = Path(store_path) if store_path else SENTIMIENTO_STORE
    hoy = datetime.today()
    sello = hoy.strftime("%Y-%m-%d")
    store = json.loads(store_path.read_text(encoding="utf-8-sig")) \
        if store_path.exists() else {}
    if store.get("_meta", {}).get("esquema") != SENTIMIENTO_ESQUEMA:
        # Store de antes de ADR-0222 (o inexistente): su `mensual` esta en otra
        # unidad, asi que se descarta en vez de leerse como si fuera un indice.
        store = {"_meta": {"esquema": SENTIMIENTO_ESQUEMA}, "terminos": {}, "mensual": {}}
    store.setdefault("terminos", {})

    pt = None
    for kw in TRENDS_KEYWORDS:
        if (store["terminos"].get(kw) or {}).get("actualizado") == sello:
            continue                        # ya se pidio hoy
        try:
            if pt is None:
                _patch_urllib3()
                from pytrends.request import TrendReq
                pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 40), retries=2, backoff_factor=1)
            pt.build_payload([kw], cat=0, geo=TRENDS_GEO,
                             timeframe=f"{TRENDS_VENTANA_DESDE} {sello}")
            mensual = _mensual_de_df(pt.interest_over_time(), kw, hoy)
            if len(mensual) < TRENDS_MIN_MESES:
                raise ValueError(f"solo {len(mensual)} meses sanos (rate limit?)")
            if not indice_de_termino(mensual):
                raise ValueError("faltan meses de la base 4T-2023")
            store["terminos"][kw] = {"actualizado": sello, "mensual": mensual}
            logger.info("sentimiento/%s OK: %d meses", kw, len(mensual))
        except Exception as e:
            logger.warning("sentimiento/%s FAIL (%s); queda la serie previa (%s)",
                           kw, str(e)[:80],
                           (store["terminos"].get(kw) or {}).get("actualizado", "sin serie"))

    compuesto = compuesto_sentimiento(store)
    if compuesto:
        store["mensual"] = compuesto
        store["_meta"] = {
            "esquema": SENTIMIENTO_ESQUEMA,
            "fuente": "Google Trends (una consulta por termino, ventana fija 2021→)",
            "actualizado": max(t["actualizado"] for t in store["terminos"].values()),
            "keywords": list(TRENDS_KEYWORDS),
            "unidad": "indice 100 = 4T-2023 (mas busquedas = mas urgencia)",
            "nota": ("ADR-0222: cada termino se rebasa contra su propio 4T-2023 dentro de "
                     "su consulta, asi que el escalar de Trends se cancela y los seis se "
                     "promedian con peso igual. Cada termino se reemplaza entero cuando su "
                     "descarga es sana; el que falla conserva la anterior."),
        }
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


def fetch_trends() -> dict:
    """Card del sentimiento digital: ultimo mes CERRADO de la canasta.

    Hasta ADR-0222 la card era un pulso propio de 3 meses en tiempo real, con su
    consulta aparte: eso obligaba a la excepcion G3 del gate (card y serie con
    semantica distinta) y a una segunda ronda de pedidos. Con seis terminos ese
    pulso necesitaria seis consultas mas para un numero que no puntua, asi que
    card y serie pasan a ser el mismo dato y el par vuelve a reconciliar.
    """
    results = {}
    try:
        store = fetch_sentimiento_store()
        compuesto = store.get("mensual") or {}
        if not compuesto:
            raise ValueError("canasta vacia — Trends sin datos y sin store previo")
        ultimo = max(compuesto)
        # Se publica el DESGLOSE por termino, no el promedio: publicar.py lo
        # promedia y asi la card y la serie salen del mismo calculo, ademas de
        # dejar a la vista de que termino viene el movimiento.
        por_termino = {kw: indice_de_termino(store["terminos"][kw]["mensual"])[ultimo]
                       for kw in TRENDS_KEYWORDS}
        results["sentimiento_digital"] = {
            "interes_relativo": por_termino,
            "keywords": list(TRENDS_KEYWORDS),
            "geo": TRENDS_GEO,
            "mes": ultimo,
            "canasta": compuesto[ultimo],
            "timeframe": f"ventana fija {TRENDS_VENTANA_DESDE}→, ultimo mes cerrado",
            "escala": "indice 100 = 4T-2023 por termino (peso igual, ADR-0222)",
            "fuente": "Google Trends via pytrends",
            "nota": ("Proxy de urgencia percibida. Mayor = mas busquedas de urgencia = peor. "
                     "Sujeto a rate limits de Google — cada termino conserva su serie previa."),
        }
        logger.info("Trends OK (%s): canasta %.1f", ultimo, compuesto[ultimo])

    except Exception as e:
        logger.warning("Trends FAIL (normal si hay rate limit): %s", e)
        results["sentimiento_digital"] = {
            "interes_relativo": None,
            "keywords": list(TRENDS_KEYWORDS),
            "geo": TRENDS_GEO,
            "fuente": "Google Trends via pytrends",
            "nota": f"Rate limit o error de conexion: {e}. Reintentar en 1h.",
        }

    return results


def _canasta_mensual(df, keywords: list[str], hoy: datetime) -> dict:
    """Promedio mensual de una canasta de keywords, excluyendo el mes en curso
    (incompleto). Mismo criterio que fetch_sentimiento_serie (ADR-0034)."""
    cols = [k for k in keywords if k in df.columns]
    canasta = df[cols].mean(axis=1)
    mensual = {}
    for d, v in canasta.groupby(canasta.index.strftime("%Y-%m")).mean().items():
        if v > 0 and d < hoy.strftime("%Y-%m"):
            mensual[d] = round(float(v), 1)
    return mensual


def _tail_promedio(df, keywords: list[str], n: int = 3) -> float | None:
    cols = [k for k in keywords if k in df.columns]
    if df is None or df.empty or not cols:
        return None
    return round(float(df[cols].tail(n).mean(axis=1).mean()), 1)


def fetch_intencion_migratoria_store(store_path: Path) -> dict:
    """
    Store mensual del indice de intencion migratoria (ADR-0035). Fuente UNICA
    compartida por espiritu_epoca.py (score) y descargar_series.py (serie
    publica): se actualiza como maximo una vez por mes — si el store ya tiene
    el mes calendario actual, no se llama a pytrends. De las 5 tandas de la
    guia original, solo la Tanda 1 (intencion expresada) es puntuable; el
    resto queda como contexto/diagnostico bajo la clave "contexto".
    """
    hoy = datetime.today()
    mes_actual = hoy.strftime("%Y-%m")

    store = json.loads(store_path.read_text(encoding="utf-8-sig")) if store_path.exists() \
        else {"_meta": {}, "mensual": {}, "contexto": {}}

    if store["_meta"].get("actualizado", "")[:7] == mes_actual:
        return store  # ya esta al dia este mes: no llamar a Trends

    try:
        _patch_urllib3()
        from pytrends.request import TrendReq
        pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 40), retries=2, backoff_factor=1)
        timeframe_full = f"2021-01-01 {hoy.strftime('%Y-%m-%d')}"

        # Tanda 1: intencion expresada (puntuable) + desglose regional (mismo payload)
        pt.build_payload(MIGRACION_TANDA_INTENCION, cat=0, timeframe=timeframe_full, geo=TRENDS_GEO)
        df1 = pt.interest_over_time()
        if df1 is None or df1.empty:
            raise ValueError("Trends devolvio vacio (rate limit) para Tanda 1 (intencion)")
        mensual = _canasta_mensual(df1, MIGRACION_TANDA_INTENCION, hoy)
        if len(mensual) < 36:
            raise ValueError(f"Tanda 1 con muy poca historia sana ({len(mensual)} meses)")

        # Desglose regional con payload de UN solo término (el principal de la
        # canasta). Con la canasta completa, interest_by_region devuelve la
        # participación relativa de cada término DENTRO de cada región (las
        # columnas suman ~100 por región), y su promedio da 100/5 = 20 para
        # todas las provincias — un número sin contenido (verificado: el store
        # publicaba 20,0 para las 24). Con un término solo, el valor es
        # interés relativo ENTRE regiones (0–100 contra la región pico), que
        # sí es un desglose regional real.
        termino_regional = MIGRACION_TANDA_INTENCION[0]
        try:
            pt.build_payload([termino_regional], cat=0, timeframe=timeframe_full, geo=TRENDS_GEO)
            regional_df = pt.interest_by_region(resolution="REGION", inc_low_vol=True)
            regional = {prov: round(float(v), 1) for prov, v in
                        regional_df[termino_regional].sort_values(ascending=False).items() if v > 0}
        except Exception as e:
            logger.warning("Regional intencion_migratoria FAIL: %s", e)
            regional = store.get("contexto", {}).get("regional", {})

        # Tanda de control: Tanda 1 filtrada por categoria "Jobs". Se guarda
        # solo su nivel reciente DENTRO de su propia escala (0-100 contra su
        # pico de 12 meses). NO se compara contra la Tanda 1: cada payload de
        # Trends se normaliza por separado, así que restar o dividir niveles
        # de dos payloads distintos no tiene significado.
        try:
            pt.build_payload(MIGRACION_TANDA_INTENCION, cat=MIGRACION_CATEGORIA_EMPLEO,
                              timeframe="today 12-m", geo=TRENDS_GEO)
            df_control = pt.interest_over_time()
            valor_control = _tail_promedio(df_control, MIGRACION_TANDA_INTENCION, n=3)
        except Exception as e:
            logger.warning("Control empleo intencion_migratoria FAIL: %s", e)
            valor_control = None

        # Tandas 2-4: contexto, solo ultimo valor (sin backfill historico)
        contexto = {}
        for clave, keywords in [
            ("ciudadanias", MIGRACION_TANDA_CIUDADANIAS),
            ("trabajo_visas", MIGRACION_TANDA_TRABAJO_VISAS),
            ("destinos", MIGRACION_TANDA_DESTINOS),
        ]:
            try:
                pt.build_payload(keywords, cat=0, timeframe="today 3-m", geo=TRENDS_GEO)
                df_ctx = pt.interest_over_time()
                contexto[clave] = {"valor": _tail_promedio(df_ctx, keywords, n=4), "keywords": keywords}
            except Exception as e:
                logger.warning("Tanda %s FAIL: %s", clave, e)
                contexto[clave] = store.get("contexto", {}).get(clave, {"valor": None, "keywords": keywords})

        # Tanda 5: diagnostico de causa — compara tendencia contra Tanda 1
        try:
            pt.build_payload(MIGRACION_TANDA_DIAGNOSTICO, cat=0, timeframe="today 12-m", geo=TRENDS_GEO)
            df5 = pt.interest_over_time()
            cols5 = [k for k in MIGRACION_TANDA_DIAGNOSTICO if k in df5.columns] if df5 is not None else []
            cols1 = [k for k in MIGRACION_TANDA_INTENCION if k in df1.columns]
            if df5 is not None and not df5.empty and len(df5) >= 6:
                serie5 = df5[cols5].mean(axis=1)
                serie1 = df1[cols1].mean(axis=1)
                tendencia_5 = float(serie5.tail(3).mean() - serie5.head(3).mean())
                tendencia_1 = float(serie1.tail(3).mean() - serie1.head(3).mean())
                if tendencia_1 > 0 and tendencia_5 <= 0:
                    motivo = "estructural"
                elif tendencia_1 > 0 and tendencia_5 > 0:
                    motivo = "economico/coyuntural"
                else:
                    motivo = "indeterminado"
            else:
                motivo = store.get("contexto", {}).get("diagnostico_causa", {}).get("motivo_dominante", "indeterminado")
        except Exception as e:
            logger.warning("Tanda diagnostico FAIL: %s", e)
            motivo = store.get("contexto", {}).get("diagnostico_causa", {}).get("motivo_dominante", "indeterminado")

        contexto["diagnostico_causa"] = {"motivo_dominante": motivo, "keywords": MIGRACION_TANDA_DIAGNOSTICO}
        contexto["control_empleo"] = {
            "valor": valor_control,
            "nota": "escala propia (0-100 vs su pico de 12m); no comparable con la tanda de intención",
        }
        contexto["regional"] = regional
        contexto["regional_termino"] = termino_regional

        store["mensual"] = mensual
        store["contexto"] = contexto
        store["_meta"] = {
            "fuente": "Google Trends (canasta mensual, ventana fija 2021→)",
            "actualizado": hoy.strftime("%Y-%m-%d"),
            "nota": ("ADR-0035: store se reemplaza entero en cada corrida sana; corridas "
                     "distintas no se mezclan. Tanda 1 (intencion) es la unica puntuable; "
                     "el resto de contexto no entra a calcular_score()."),
        }
        store_path.parent.mkdir(parents=True, exist_ok=True)
        store_path.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info("intencion_migratoria store actualizado: %d meses", len(mensual))

    except Exception as e:
        logger.warning("intencion_migratoria FAIL (normal si hay rate limit): %s", e)

    return store
