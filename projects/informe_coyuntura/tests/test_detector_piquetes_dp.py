"""El detector de años nuevos de piquetes de Diagnóstico Político (ADR-0025).

El sitio se rehízo en 2026 y /monitoreos-politicos da 404: el detector fallaba
siempre y la card publicaba «No se pudo verificar si el portal publicó anclajes
más recientes». Ahora mira el mapa del sitio y /insights, y que no haya un año
nuevo es lo normal (el cierre anual sale en enero)."""
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import gestion  # noqa: E402


def test_lee_el_anio_del_texto_y_de_la_url_de_la_entrada():
    f = gestion.anios_de_piquetes_dp
    assert f("3.893 piquetes en 2025, la cifra más baja desde 2011") == {2025}
    assert f("/2026/01/11/3-893-piquetes-2025-la-cifra-mas-baja-desde-2011/") == {2025}
    assert f("sin novedades") == set()


def _con_paginas(monkeypatch, textos):
    def get(url, **kw):
        return SimpleNamespace(text=textos[url], raise_for_status=lambda: None)
    monkeypatch.setattr(gestion.requests, "get", get)


def test_sin_anio_nuevo_no_hay_advertencia(monkeypatch):
    _con_paginas(monkeypatch, {u: "<html>insights</html>" for u in gestion.DP_PAGINAS_DETECTOR})
    r = gestion.fetch_protocolo_antipiquetes()
    assert r["advertencia_fuente"] == ""
    assert "No se pudo verificar" not in r["detalle_txt"]


def test_un_anio_nuevo_se_avisa(monkeypatch):
    textos = {u: "" for u in gestion.DP_PAGINAS_DETECTOR}
    textos[gestion.DP_PAGINAS_DETECTOR[0]] = "<loc>https://x/2027/01/10/2-000-piquetes-2026-algo</loc>"
    _con_paginas(monkeypatch, textos)
    r = gestion.fetch_protocolo_antipiquetes()
    assert "2026" in r["advertencia_fuente"]
