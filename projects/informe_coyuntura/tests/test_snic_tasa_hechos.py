"""ADR-0327: `tasa_homicidios`/`tasa_robos` tienen que leer la columna
`tasa_hechos` del CSV del SNIC (ya calculada por la fuente, cada 100.000
hab.), NO `cantidad_hechos` (el conteo bruto de casos). La revisión
adversarial probó esta mutación exacta —leer `cantidad_hechos`— y no
encontró ninguna guarda: publicaría 1.613 en vez de 3,48 para homicidios, un
error de tres órdenes de magnitud sin ningún test que lo cazara.

Control positivo Y negativo en la misma corrida: el fixture hace que
`cantidad_hechos` y `tasa_hechos` DIVERGAN a propósito (no coinciden ni de
casualidad), así que si el parser tomara la columna equivocada el valor leído
sería obviamente el número grande, no el pequeño.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import descargar_series as ds  # noqa: E402

NOMBRE_HOMICIDIOS = ds.SNIC_TIPOS_TASA["tasa_homicidios"]
NOMBRE_ROBOS = ds.SNIC_TIPOS_TASA["tasa_robos"]


class _RespuestaFalsa:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        return None


def _csv_tasas(n_anios=22):
    """26 años >= 20 (umbral de "descarga sana" en `_snic_tasas`), con
    `cantidad_hechos` y `tasa_hechos` deliberadamente distintos en escala:
    la cantidad es un entero de 6 cifras, la tasa un decimal de una cifra."""
    header = "anio;codigo_delito_snic_nombre;cantidad_hechos;tasa_hechos"
    filas = [header]
    for i in range(n_anios):
        anio = 2000 + i
        filas.append(f"{anio};{NOMBRE_HOMICIDIOS};999999;3,48")
        filas.append(f"{anio};{NOMBRE_ROBOS};888888;778,1")
    return ("\n".join(filas) + "\n").encode("utf-8")


def _store_vacio(tmp_path):
    p = tmp_path / "snic_serie.json"
    p.write_text(json.dumps({"anual": {}, "por_tipo": {}, "_meta": {"actualizado": None}}),
                 encoding="utf-8")
    return p


def _sin_config_cacheado(monkeypatch):
    """`_snic_tasas`/`fetch_tasa_*_serie` hacen `sys.path.insert(vida_cotidiana)`
    y después `from config import SNIC_CSV` — si otro test de la corrida ya
    dejó `sys.modules["config"]` apuntando al `config.py` de la RAÍZ (que no
    tiene `SNIC_CSV`), Python reutiliza el módulo cacheado y el import
    revienta. Misma trampa que documentan `test_snic_homicidios.py` y
    compañía para el colector; acá aplica al módulo que la consume."""
    monkeypatch.delitem(sys.modules, "config", raising=False)


def test_snic_tasas_lee_tasa_hechos_no_cantidad_hechos(tmp_path, monkeypatch):
    _sin_config_cacheado(monkeypatch)
    monkeypatch.setattr(ds, "SNIC_SERIE_STORE", _store_vacio(tmp_path))
    monkeypatch.setattr(ds.requests, "get",
                        lambda *a, **k: _RespuestaFalsa(_csv_tasas()))

    tasas = ds._snic_tasas()

    valor_leido = tasas[NOMBRE_HOMICIDIOS]["2021"]
    assert valor_leido == 3.48, (
        f"se leyó {valor_leido}: si el parser tomara `cantidad_hechos` en "
        f"vez de `tasa_hechos` este valor sería 999999")
    assert valor_leido != 999999


def test_snic_tasas_robos_tambien_lee_tasa_no_cantidad(tmp_path, monkeypatch):
    _sin_config_cacheado(monkeypatch)
    monkeypatch.setattr(ds, "SNIC_SERIE_STORE", _store_vacio(tmp_path))
    monkeypatch.setattr(ds.requests, "get",
                        lambda *a, **k: _RespuestaFalsa(_csv_tasas()))

    tasas = ds._snic_tasas()

    valor_leido = tasas[NOMBRE_ROBOS]["2021"]
    assert valor_leido == 778.1
    assert valor_leido != 888888


def test_fetch_tasa_homicidios_serie_devuelve_tasas_no_cantidades(tmp_path, monkeypatch):
    """Integración real: la función que `itvc.py` termina consumiendo."""
    _sin_config_cacheado(monkeypatch)
    monkeypatch.setattr(ds, "SNIC_SERIE_STORE", _store_vacio(tmp_path))
    monkeypatch.setattr(ds.requests, "get",
                        lambda *a, **k: _RespuestaFalsa(_csv_tasas()))

    serie = ds.fetch_tasa_homicidios_serie()
    assert serie, "la serie salió vacía"
    valores = {v for _fecha, v in serie}
    assert valores == {3.48}, (
        f"valores leídos {valores}: se esperaba sólo 3,48 (tasa_hechos), no "
        f"999999 (cantidad_hechos)")
