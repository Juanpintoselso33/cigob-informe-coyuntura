"""Cumplimiento de la meta de reservas del programa con el FMI (ADR-0428).

El programa de Servicio Ampliado fija metas de VARIACIÓN de las reservas
internacionales netas (RIN) entre fechas de prueba. El FMI no publica la RIN
mensual, así que el avance se ESTIMA con la variación de las reservas netas
estrictas de la planilla SDDS del BCRA (I.A + II.1 + II.2 + II.3, la misma
medición que publica la card de reservas netas) desde la base de cada meta.

El valor del indicador es el avance contra la meta PRORRATEADA al mes, en %:

    avance = (netas(mes) − netas(base)) / (meta × meses transcurridos / meses de la ventana) × 100

Prorrateada para que un enero no salga rojo por construcción: con la meta entera
de denominador, acumular al ritmo exacto del año daría 8 % en enero.

Las metas viven en `data/macro/metas_reservas_fmi.json`. Cuando el FMI publica el
resultado oficial de una fecha de prueba, se carga en el campo `oficial` y ese
dato reemplaza a la estimación en el mes de la fecha de prueba.

Todo acá es puro (sin red): lo usan el colector (`macro.py`) y la serie
(`descargar_series.py`), así que la card y el último punto del gráfico salen de
la misma cuenta.
"""
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
METAS_PATH = PROJECT_DIR / "data" / "macro" / "metas_reservas_fmi.json"

CAMPOS = ("base", "fecha_meta", "acumulacion_meta", "tipo", "fuente", "revision")
TIPOS = ("criterio de desempeño", "indicativa")


def _ym(fecha: str) -> str:
    return fecha[:7]


def meses_entre(desde_ym: str, hasta_ym: str) -> int:
    """Meses de `desde_ym` a `hasta_ym` ('YYYY-MM'): 2025-12 → 2026-09 = 9."""
    a = int(desde_ym[:4]) * 12 + int(desde_ym[5:7])
    b = int(hasta_ym[:4]) * 12 + int(hasta_ym[5:7])
    return b - a


def cargar_metas(path: Path = METAS_PATH) -> list[dict]:
    """Lee y valida la tabla de metas. Falla fuerte si está mal cargada: una meta
    sin fuente o dos ventanas superpuestas no se publican."""
    metas = json.loads(Path(path).read_text(encoding="utf-8"))["metas"]
    for m in metas:
        for campo in CAMPOS:
            if m.get(campo) in (None, ""):
                raise ValueError(f"meta {m.get('fecha_meta')}: falta `{campo}` (fuente, revisión y fechas son obligatorias)")
        if m["tipo"] not in TIPOS:
            raise ValueError(f"meta {m['fecha_meta']}: tipo «{m['tipo']}» fuera de {TIPOS}")
        if not float(m["acumulacion_meta"]) > 0:
            raise ValueError(f"meta {m['fecha_meta']}: la acumulación tiene que ser positiva")
        if meses_entre(_ym(m["base"]), _ym(m["fecha_meta"])) <= 0:
            raise ValueError(f"meta {m['fecha_meta']}: la base no es anterior a la fecha de la meta")
        for p in m.setdefault("pruebas_oficiales", []):
            if not p.get("fecha") or p.get("acumulacion") is None or not p.get("fuente"):
                raise ValueError(f"meta {m['fecha_meta']}: cada prueba oficial necesita `fecha`, `acumulacion` y `fuente`")
            if not _ym(m["base"]) < _ym(p["fecha"]) < _ym(m["fecha_meta"]):
                raise ValueError(f"meta {m['fecha_meta']}: la prueba oficial {p['fecha']} cae fuera de la ventana")
        oficial = m.setdefault("oficial", None)
        if oficial is not None:
            if not isinstance(oficial, dict) or oficial.get("acumulacion") is None or not oficial.get("fuente"):
                raise ValueError(f"meta {m['fecha_meta']}: el dato oficial necesita `acumulacion` y `fuente`")
    metas = sorted(metas, key=lambda m: m["fecha_meta"])
    for previa, siguiente in zip(metas, metas[1:]):
        if siguiente["base"] < previa["fecha_meta"]:
            raise ValueError(f"la meta {siguiente['fecha_meta']} se superpone con la de {previa['fecha_meta']}")
    return metas


def meta_vigente(metas: list[dict], ym: str) -> dict | None:
    """La meta cuya ventana (base, fecha_meta] contiene el mes `ym`."""
    for m in metas:
        if _ym(m["base"]) < ym <= _ym(m["fecha_meta"]):
            return m
    return None


def meta_prorrateada(meta: dict, ym: str) -> float:
    """Acumulación exigida a `ym`: la meta por los meses transcurridos sobre los
    de la ventana (lineal)."""
    total = meses_entre(_ym(meta["base"]), _ym(meta["fecha_meta"]))
    transcurridos = meses_entre(_ym(meta["base"]), ym)
    return float(meta["acumulacion_meta"]) * transcurridos / total


def avance(metas: list[dict], ym: str, netas_por_mes: dict) -> dict | None:
    """Avance del mes `ym` contra su meta, o None si no hay meta vigente o falta
    el dato del mes o de la base. `netas_por_mes`: {YYYY-MM: netas estrictas}."""
    meta = meta_vigente(metas, ym)
    if meta is None:
        return None
    oficial = meta.get("oficial")
    intermedia = next((p for p in meta.get("pruebas_oficiales") or []
                       if _ym(p["fecha"]) == ym), None)
    if oficial and ym == _ym(meta["fecha_meta"]):
        acumulado, origen = float(oficial["acumulacion"]), "oficial"
    elif intermedia:
        # Fecha de prueba intermedia del programa (p. ej. junio de 2026) con
        # resultado informado por el FMI: gana sobre la estimación propia, para
        # que la serie no contradiga al FMI (Juan, 13-nov-2026).
        acumulado, origen = float(intermedia["acumulacion"]), "oficial"
    else:
        base_ym = _ym(meta["base"])
        if ym not in netas_por_mes or base_ym not in netas_por_mes:
            return None
        acumulado = float(netas_por_mes[ym]) - float(netas_por_mes[base_ym])
        origen = "estimacion"
    exigido = meta_prorrateada(meta, ym)
    return {
        "valor": round(acumulado / exigido * 100.0, 1),
        "acumulado": round(acumulado, 0),
        "meta_prorrateada": round(exigido, 0),
        "meta_total": float(meta["acumulacion_meta"]),
        "meses_transcurridos": meses_entre(_ym(meta["base"]), ym),
        "meses_ventana": meses_entre(_ym(meta["base"]), _ym(meta["fecha_meta"])),
        "base": meta["base"],
        "fecha_meta": meta["fecha_meta"],
        "tipo_meta": meta["tipo"],
        "fuente_meta": meta["fuente"],
        "origen": origen,
    }


def serie(metas: list[dict], netas_por_mes: dict) -> list[tuple[str, dict]]:
    """[(YYYY-MM, avance)] ascendente, sólo los meses con meta y dato."""
    out = []
    for ym in sorted(netas_por_mes):
        r = avance(metas, ym, netas_por_mes)
        if r is not None:
            out.append((ym, r))
    return out
