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
    MIGRACION_TANDA_INTENCION, MIGRACION_TANDA_CIUDADANIAS,
    MIGRACION_TANDA_TRABAJO_VISAS, MIGRACION_TANDA_DESTINOS,
    MIGRACION_TANDA_DIAGNOSTICO, MIGRACION_CATEGORIA_EMPLEO,
)

logger = logging.getLogger(__name__)


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


def _fetch_trends(keywords: list[str], geo: str, timeframe: str = "today 3-m") -> dict:
    """Retorna interes relativo (0-100) para cada keyword en el periodo."""
    _patch_urllib3()
    from pytrends.request import TrendReq

    pt = TrendReq(hl="es-AR", tz=-180, timeout=(10, 30), retries=2, backoff_factor=0.5)
    pt.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo, gprop="")
    df = pt.interest_over_time()

    if df is None or df.empty:
        return {}

    # Promedio de los ultimos 4 periodos por keyword
    tail = df[keywords].tail(4)
    return {kw: round(float(tail[kw].mean()), 1) for kw in keywords if kw in tail.columns}


def fetch_trends() -> dict:
    """Descarga interes relativo en Google Trends para palabras clave de vida cotidiana."""
    results = {}

    try:
        interes = _fetch_trends(TRENDS_KEYWORDS, TRENDS_GEO, timeframe="today 3-m")
        if not interes:
            raise ValueError("DataFrame vacio — posible rate limit")

        results["sentimiento_digital"] = {
            "interes_relativo": interes,
            "keywords": TRENDS_KEYWORDS,
            "geo": TRENDS_GEO,
            "timeframe": "ultimos 3 meses",
            "escala": "0-100 (100 = maximo historico en el periodo)",
            "fuente": "Google Trends via pytrends",
            "nota": (
                "Proxy de urgencia percibida. Alto 'inseguridad'/'precios' = presion ciudadana. "
                "Sujeto a rate limits de Google — puede fallar silenciosamente."
            ),
        }
        logger.info("Trends OK: %s", interes)

    except Exception as e:
        logger.warning("Trends FAIL (normal si hay rate limit): %s", e)
        # Fallback: retornar estructura vacia pero documentada
        results["sentimiento_digital"] = {
            "interes_relativo": None,
            "keywords": TRENDS_KEYWORDS,
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
